import argparse
import os
import re
import sys
from time import time

import requests as requests
import torch
from openai import OpenAI
from transformers import AutoTokenizer, AutoModel

import json
from model import Verse, SimilarVerse
from verse_repository import VerseRepository

OPENAI_KEY = os.getenv('OPENAI_KEY')
if not OPENAI_KEY:
    sys.exit('OPENAI_KEY not set')

HUGGING_FACE_EMBEDDING_MODELS = ['hugging_face_bge']
OPENAI_EMBEDDING_MODELS = ['text-embedding-ada-002', 'text-embedding-3-small']
# OPENAI_EMBEDDING_MODELS = ['text-embedding-3-small']
ALL_EMBEDDING_MODELS = HUGGING_FACE_EMBEDDING_MODELS + OPENAI_EMBEDDING_MODELS

THRESHOLDS = {
    'hugging_face_bge': 0.8,
    'text-embedding-ada-002': 0.9,
    'text-embedding-3-small': 0.8,
}
openai_client = OpenAI(api_key=OPENAI_KEY)

tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-base-en-v1.5")
model = AutoModel.from_pretrained("BAAI/bge-base-en-v1.5")


def get_millis():
    return int(round(time() * 1000))


def populate_bge_embedding(verses):
    for verse in verses:
        start = get_millis()
        inputs = tokenizer(verse.clean_text, return_tensors='pt')

        # Get the embeddings
        outputs = model(**inputs)

        # The last hidden state is the first element of the output tuple
        tensor = outputs[0]

        embedding = torch.mean(tensor, dim=1)

        # Detach the tensor from the computation graph and convert it to a numpy array
        embedding = embedding.detach()

        # Convert the tensor to a list
        embedding = embedding[0].tolist()

        verse.hugging_face_bge_embedding = embedding


def populate_embeddings(verses):
    populate_bge_embedding(verses)

    for openai_embedding_model in OPENAI_EMBEDDING_MODELS:
        clean_texts = [verse.clean_text for verse in verses]
        response = openai_client.embeddings.create(input=clean_texts, model=openai_embedding_model)

        embedding_data = response.data

        if len(embedding_data) != len(verses):
            sys.exit(f'Error: {len(embedding_data)} embeddings returned for {len(verses)} verses')

        for i, verse in enumerate(verses):
            if openai_embedding_model == 'text-embedding-ada-002':
                verse.openai_ada_002_embedding = embedding_data[i].embedding
            elif openai_embedding_model == 'text-embedding-3-small':
                verse.openai_3_small_embedding = embedding_data[i].embedding
            elif openai_embedding_model == 'text-embedding-3-large':
                verse.openai_3_large_embedding = embedding_data[i].embedding
            else:
                sys.exit('unknown openai_embedding_model: ' + openai_embedding_model)


def get_clean_text(text):
    text = re.sub('[^a-zA-Z0-9]', ' ', text).lower()
    text = re.sub(' +', ' ', text)
    text = text.strip()
    return text


def get_verse_string(verse):
    if isinstance(verse, dict):
        return f'{verse["volume"]} {verse["book_title"]} {verse["chapter_number"]}:{verse["verse_number"]}'
    else:
        return f'{verse.volume} {verse.book} {verse.chapter}:{verse.verse}'


def index_similar_verses(thresholds: dict):
    verse_repository = VerseRepository()

    winners = []

    skip = {}

    for volume in verse_repository.select_distinct_volumes():
        if volume != 'Pearl of Great Price':
            continue

        for verse in verse_repository.select_all_verses_from_volume(volume):
            if verse.book in skip and verse.chapter in skip[verse.book]:
                continue

            for embedding_model in ALL_EMBEDDING_MODELS:
                threshold = thresholds[embedding_model]

                similars = verse_repository.select_similar_verses(verse, embedding_model=embedding_model,
                                                                  threshold=threshold)
                if similars:
                    print(f'{verse.book} {verse.chapter}:{verse.verse} {verse.text}')
                    similar_dicts = []

                    SimilarVerse.delete().where(
                        (SimilarVerse.base_verse_id == verse.id) & (SimilarVerse.embedding_model == embedding_model)
                    ).execute()

                    for similar in similars:
                        similar_verse = SimilarVerse(
                            base_verse=verse,
                            similar_verse=similar,
                            embedding_model=embedding_model,
                            score=similar.cosine_distance
                        )

                        similar_verse.save(force_insert=True)

                        print(
                            f' -> {similar.book} {similar.chapter}:{similar.verse} ({similar.cosine_distance}) {similar.text}')
                        similar.embedding = None
                        similar_dicts.append(similar.to_dict())
                    winners.append({
                        'verse': verse.to_dict(),
                        'similars': similar_dicts
                    })

    with open(f'winners-{threshold}.json', 'w') as file:
        json.dump(winners, file, indent=4)


def index_raw_verses():
    base_url = 'https://raw.githubusercontent.com/beandog/lds-scriptures/refs/heads/master/json'
    sources_directory = f"{os.path.dirname(os.path.realpath(__file__))}/sources"

    if not os.path.exists(sources_directory):
        os.makedirs(sources_directory)

    if not os.path.exists(sources_directory):
        sys.exit(f"Could not create sources directory: {sources_directory}")

    corpus = {}

    for filename in ['lds-scriptures-json.txt']:
        fullpath = f'{sources_directory}/{filename}'
        if not os.path.exists(fullpath):
            url = f'{base_url}/{filename}'

            print(f'Downloading {url}')

            response = requests.get(url)
            with open(fullpath, 'wb') as f:
                print(f'Writing {fullpath}')
                f.write(response.content)

        with open(fullpath, 'r') as file:
            verses = json.load(file)

            chapter_strings = {}

            volume_book_index = 0

            for this_verse in verses:
                volume = this_verse['volume_title']

                if volume not in corpus:
                    corpus[volume] = {}
                    volume_book_index = 0

                this_verse['volume'] = volume

                book = this_verse['book_title']
                chapter = this_verse['chapter_number']
                verse = this_verse['verse_number']
                text = this_verse['scripture_text']

                if book not in corpus[volume]:
                    corpus[volume][book] = {}
                    volume_book_index += 1

                if chapter not in corpus[volume][book]:
                    corpus[volume][book][chapter] = []

                clean_text = get_clean_text(text)

                verse_record = Verse(
                    volume=volume,
                    book=book,
                    volume_book_index=volume_book_index,
                    chapter=chapter,
                    verse=verse,
                    text=text,
                    clean_text=clean_text,
                )

                corpus[volume][book][chapter].append(verse_record)

                chapter_string = f'{book} {chapter}'

                if chapter_string not in chapter_strings:
                    chapter_strings[chapter_string] = True
                    print(f' -> {chapter_string}')

    verse_repository = VerseRepository()

    for volume in sorted(corpus.keys()):
        print(volume)
        for book in sorted(corpus[volume].keys()):
            for chapter in sorted(corpus[volume][book].keys()):
                print(f'  -> {book} {chapter}')
                verses = corpus[volume][book][chapter]
                verse_count = verse_repository.select_count_verses_by_volume_book_chapter(volume, book, chapter)

                if verse_count == len(verses):
                    print(f'    -> Skipping {book} {chapter}')
                    continue

                populate_embeddings(verses)
                # save all the verses in bulk
                Verse.bulk_create(verses)


def generate_library_info():
    verse_repository = VerseRepository()

    data = {}

    volumes = verse_repository.select_distinct_volumes()
    for volume in volumes:
        books = verse_repository.select_distinct_books(volume)
        data[volume] = []
        for book in books:
            chapters = verse_repository.select_distinct_chapters(book)
            data[volume].append({
                'book': book,
                'chapters': len(chapters)
            })

    with open('json/library-info.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4)


def generate_static_json_content_files():
    verse_repository = VerseRepository()

    for volume in verse_repository.select_distinct_volumes():
        print(f'Indexing {volume}')
        books = verse_repository.select_distinct_books(volume)

        for book in books:
            print(f' -> {book}')
            chapters = verse_repository.select_distinct_chapters(book)

            for chapter in chapters:
                print(f'   -> {chapter}')
                data = {
                    'volume': volume,
                    'book': book,
                    'chapter': chapter,
                    'verses': []
                }

                these_verses = verse_repository.select_verses_by_volume_book_chapter(volume, book, chapter)

                for verse in these_verses:
                    verse_dict = verse.to_dict()

                    for field in ['clean_text', 'id']:
                        del verse_dict[field]

                    similar_dicts = []

                    similars = verse_repository.select_similar_verses_simple(verse=verse)
                    if similars:

                        for similar in similars:
                            similar.embedding = None
                            similar_dict = similar.to_dict()

                            fields_to_delete = ['clean_text', 'id']

                            for key in similar_dict.keys():
                                if key.endswith('_embedding'):
                                    fields_to_delete.append(key)

                            for field in fields_to_delete:
                                del similar_dict[field]

                            similar_dict['embedding_model'] = similar.similarverse.embedding_model
                            similar_dict['score'] = similar.similarverse.score

                            similar_dicts.append(similar_dict)

                    data['verses'].append({
                        'verse': verse_dict['verse'],
                        'text': verse_dict['text'],
                        'similars': similar_dicts
                    })

                directory = f'json/{volume}'.replace(' ', '_').lower()
                if not os.path.exists(directory):
                    os.makedirs(directory)
                filename = f'{directory}/{book}-{chapter}.json'.replace(' ', '_').lower()
                with open(filename, 'w') as file:
                    json.dump(data, file, indent=4)
                    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Index similar verses with a specified threshold.')
    parser.add_argument('--threshold', type=float, default=0.8, help='Threshold for cosine similarity')
    args = parser.parse_args()

    # index_raw_verses()
    index_similar_verses(thresholds=THRESHOLDS)
    generate_library_info()
    generate_static_json_content_files()

# base volume
# chapter
# similar volumes
# threshold

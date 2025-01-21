import argparse
import json
import os
import re
import sys
from time import time

import requests as requests
import torch
from transformers import AutoTokenizer, AutoModel

from model import Verse, SimilarVerse
from verse_repository import VerseRepository

tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-base-en-v1.5")
model = AutoModel.from_pretrained("BAAI/bge-base-en-v1.5")


def get_millis():
    return int(round(time() * 1000))


def get_embedding(verse):
    start = get_millis()
    inputs = tokenizer(verse, return_tensors='pt')

    # Get the embeddings
    outputs = model(**inputs)

    # The last hidden state is the first element of the output tuple
    tensor = outputs[0]

    embedding = torch.mean(tensor, dim=1)

    # Detach the tensor from the computation graph and convert it to a numpy array
    embedding = embedding.detach()

    # Convert the tensor to a list
    embedding = embedding[0].tolist()

    elapsed = get_millis() - start

    return embedding


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


def index_similar_verses(threshold):
    verse_repository = VerseRepository()

    winners = []

    skip = {
        # '1 Nephi': [20, 21],
        # '2 Nephi': [7, 8, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 27],
        # 'Mosiah': [14],
        # '3 Nephi': [12, 13, 14, 22, 24, 25]
    }

    verse_strings = {}

    for verse in verse_repository.select_all_verses():
        if verse.book in skip and verse.chapter in skip[verse.book]:
            continue

        verse_string = get_verse_string(verse)
        if verse_string in verse_strings:
            continue

        similars = verse_repository.select_similar_verses(verse, threshold=threshold)
        if similars:
            print(f'{verse.book} {verse.chapter}:{verse.verse} {verse.text}')
            similar_dicts = []

            SimilarVerse.delete().where(SimilarVerse.base_verse_id == verse.id).execute()

            # delete from similar_verse where base_verse = verse
            for similar in similars:
                similar_verse = SimilarVerse(
                    base_verse=verse,
                    similar_verse=similar,
                    score=similar.cosine_distance
                )

                print(
                    f'base_verse: {verse.id} {verse_string}, similar_verse: {similar.id}, score: {similar.cosine_distance}')

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

    volumes = {}
    verse_strings = {}

    verse_repository = VerseRepository()
    inserted_verses = verse_repository.select_all_verses()

    for inserted_verse in inserted_verses:
        verse_string = get_verse_string(inserted_verse)
        verse_strings[verse_string] = True

    for filename in ['kjv-scriptures-json.txt', 'lds-scriptures-json.txt']:
        fullpath = f'{sources_directory}/{filename}'
        if not os.path.exists(fullpath):
            url = f'{base_url}/{filename}'

            print(f'Downloading {url}')

            response = requests.get(url)
            with open(fullpath, 'wb') as f:
                print(f'Writing {fullpath}')
                f.write(response.content)

        with open(fullpath, 'r') as file:
            data = json.load(file)

            chapter_strings = {}

            for this_verse in data:
                volume = this_verse['volume_title']
                this_verse['volume'] = volume

                if volume not in volumes:
                    print(f'Indexing {volume}')
                    volumes[volume] = True

                book = this_verse['book_title']
                chapter = this_verse['chapter_number']
                verse = this_verse['verse_number']
                text = this_verse['scripture_text']

                verse_string = get_verse_string(this_verse)

                if verse_string in verse_strings:
                    continue

                clean_text = get_clean_text(text)
                embedding = get_embedding(clean_text)

                verse_record = Verse(
                    volume=volume,
                    book=book,
                    chapter=chapter,
                    verse=verse,
                    text=text,
                    clean_text=clean_text,
                    embedding=embedding
                )

                try:
                    verse_record.save()
                except Exception as e:
                    pass

                chapter_string = f'{book} {chapter}'

                if chapter_string not in chapter_strings:
                    chapter_strings[chapter_string] = True
                    print(f' -> {chapter_string}')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Index similar verses with a specified threshold.')
    parser.add_argument('--threshold', type=float, default=0.5, help='Threshold for cosine similarity')
    args = parser.parse_args()

    index_raw_verses()
    index_similar_verses(threshold=args.threshold)

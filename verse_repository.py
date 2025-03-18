from typing import List

from peewee import fn

from model import Verse, SimilarVerse

EMBEDDING_FIELDS = {
    'hugging_face_bge': Verse.hugging_face_bge_embedding,
    'text-embedding-ada-002': Verse.openai_ada_002_embedding,
    'text-embedding-3-small': Verse.openai_3_small_embedding,
}


class VerseRepository:
    def select_distinct_volumes(self):
        query = Verse.select(Verse.volume).distinct().order_by(Verse.volume)
        return [verse.volume for verse in query]

    def select_all_verses_from_volume(self, volume: str):
        query = Verse.select().where(Verse.volume == volume).order_by(Verse.id)
        return list(query)

    def select_all_verses(self):
        query = Verse.select().order_by(Verse.id)
        return list(query)

    def select_book_of_mormon_verses(self):
        query = Verse.select().where(Verse.volume == 'Book of Mormon').order_by(Verse.id)
        return list(query)

    def select_similar_verses_simple(self, verse: Verse):
        query = (Verse
                 .select(Verse, SimilarVerse.embedding_model, SimilarVerse.score)
                 .join(SimilarVerse, on=(Verse.id == SimilarVerse.similar_verse))
                 .where(SimilarVerse.base_verse == verse)
                 .order_by(SimilarVerse.embedding_model, SimilarVerse.score.desc()))

        return list(query)

    def select_similar_verses(self, verse: Verse, embedding_model: str, threshold: float = 0.9, limit: int = 10):
        embedding: List[float] = None
        if embedding_model in EMBEDDING_FIELDS:
            if embedding_model == 'hugging_face_bge':
                embedding = verse.hugging_face_bge_embedding.tolist()
            elif embedding_model == 'text-embedding-ada-002':
                embedding = verse.openai_ada_002_embedding.tolist()
            elif embedding_model == 'text-embedding-3-small':
                embedding = verse.openai_3_small_embedding.tolist()
            elif embedding_model == 'text-embedding-3-large':
                embedding = verse.openai_3_large_embedding.tolist()
        else:
            raise ValueError(f'Invalid embedding model: {embedding_model}')

        embedding_column = EMBEDDING_FIELDS[embedding_model]

        # query = (Verse
        #          .select(Verse, SimilarVerse.score,
        #                  (1 - embedding_column.cosine_distance(embedding)).alias('cosine_distance'))
        #          .join(SimilarVerse, on=(Verse.id == SimilarVerse.similar_verse))
        #          .where(
        #     (SimilarVerse.base_verse == verse) & ((1 - embedding_column.cosine_distance(embedding)) >= threshold))
        #          .order_by((1 - embedding_column.cosine_distance(embedding)).desc())
        #          .limit(limit))

        query = (Verse
                 .select(Verse,
                         (1 - embedding_column.cosine_distance(embedding)).alias('cosine_distance'))
                 .where((1 - embedding_column.cosine_distance(embedding)) >= threshold, Verse.id != verse.id)
                 .order_by((1 - embedding_column.cosine_distance(embedding)).desc()))

        return list(query)

    def select_distinct_books(self, volume: str):
        subquery = (Verse
                    .select(Verse.book, fn.MIN(Verse.id).alias('min_id'))
                    .where(Verse.volume == volume)
                    .group_by(Verse.book)
                    .alias('subquery'))

        query = (Verse
                 .select(Verse.book)
                 .join(subquery, on=(Verse.id == subquery.c.min_id))
                 .order_by(Verse.id))

        return [verse.book for verse in query]

    def select_distinct_chapters(self, book: str):
        subquery = (Verse
                    .select(Verse.chapter, fn.MIN(Verse.id).alias('min_id'))
                    .where(Verse.book == book)
                    .group_by(Verse.chapter)
                    .alias('subquery'))

        query = (Verse
                 .select(Verse.chapter)
                 .join(subquery, on=(Verse.id == subquery.c.min_id))
                 .order_by(Verse.chapter))

        return [verse.chapter for verse in query]

    def select_verses_by_volume_book_chapter(self, volume: str, book: str, chapter: int):
        query = Verse.select().where(
            (Verse.volume == volume) & (Verse.book == book) & (Verse.chapter == chapter)).order_by(Verse.id)
        return list(query)

    def select_count_verses_by_volume_book_chapter(self, volume: str, book: str, chapter: int):
        query = Verse.select(fn.COUNT(Verse.id)).where(
            (Verse.volume == volume) & (Verse.book == book) & (Verse.chapter == chapter))
        return query.scalar()

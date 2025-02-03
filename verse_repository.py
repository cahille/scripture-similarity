from typing import List

from peewee import fn

from model import Verse, SimilarVerse


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

    def select_similar_verses(self, verse: Verse, threshold: float = 0.9, limit: int = 10):
        embedding: List[float] = verse.embedding.tolist()

        query = (Verse
                 .select(Verse, SimilarVerse.score,
                         (1 - Verse.embedding.cosine_distance(embedding)).alias('cosine_distance'))
                 .join(SimilarVerse, on=(Verse.id == SimilarVerse.similar_verse))
                 .where(
            (SimilarVerse.base_verse == verse) & ((1 - Verse.embedding.cosine_distance(embedding)) >= threshold))
                 .order_by((1 - Verse.embedding.cosine_distance(embedding)).desc())
                 .limit(limit))

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

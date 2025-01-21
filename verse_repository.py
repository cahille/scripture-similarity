from typing import List

from model import Verse


class VerseRepository:
    def select_all_verses(self):
        query = Verse.select().order_by(Verse.id)
        return list(query)

    def select_book_of_mormon_verses(self):
        query = Verse.select().where(Verse.volume == 'Book of Mormon').order_by(Verse.id)
        return list(query)

    def select_similar_verses(self, verse: Verse, threshold: float = 0.9, limit: int = 10):
        embedding: List[float] = verse.embedding.tolist()

        query = (Verse
                 .select(Verse, (1 - Verse.embedding.cosine_distance(embedding)).alias('cosine_distance'))
                 .where(
            (Verse.volume != verse.volume) & ((1 - Verse.embedding.cosine_distance(embedding)) >= threshold))
                 .order_by((1 - Verse.embedding.cosine_distance(embedding)).desc())
                 .limit(limit))

        return list(query)

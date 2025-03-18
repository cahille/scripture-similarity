import os

import numpy as np
from peewee import Model, CharField, IntegerField, TextField, PostgresqlDatabase, ForeignKeyField, FloatField, \
    CompositeKey
from pgvector.peewee import VectorField

dp_port = os.environ.get('DB_PORT', 5432)

# psql commands
"""
\c postgres
GRANT USAGE ON SCHEMA public TO "scripture-similarity";
GRANT CREATE ON SCHEMA public TO "scripture-similarity";
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO "scripture-similarity";
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO "scripture-similarity";
CREATE DATABASE "scripture-similarity";
CREATE USER "scripture-similarity" WITH ENCRYPTED PASSWORD 'scripture-similarity';
GRANT ALL PRIVILEGES ON DATABASE "scripture-similarity" TO "scripture-similarity";
"""

print(f'Connecting to database')
db = PostgresqlDatabase('scripture-similarity', user='scripture-similarity', password='scripture-similarity',
                        host='localhost', port=dp_port)


class Verse(Model):
    def to_dict(self):
        data = {}
        for field_name, field_value in self.__data__.items():
            if isinstance(field_value, np.ndarray):
                continue
            if field_value == None:
                continue

            data[field_name] = field_value

        return data

    volume = CharField(max_length=100)
    book = CharField(max_length=100)
    volume_book_index = IntegerField()
    chapter = IntegerField()
    verse = IntegerField()
    text = TextField()
    clean_text = TextField()
    hugging_face_bge_embedding = VectorField(dimensions=768)
    openai_ada_002_embedding = VectorField(dimensions=1536)
    openai_3_small_embedding = VectorField(dimensions=1536)

    class Meta:
        database = db
        table_name = 'verse'


class SimilarVerse(Model):
    base_verse = ForeignKeyField(Verse, backref='similar_verse', on_delete='CASCADE')
    similar_verse = ForeignKeyField(Verse, backref='base_verse', on_delete='CASCADE')
    embedding_model = CharField(max_length=100)
    score = FloatField()

    class Meta:
        database = db
        table_name = 'similar_verse'
        primary_key = CompositeKey('base_verse', 'similar_verse')

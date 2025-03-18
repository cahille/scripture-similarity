-- migrate:up
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS verse (
    id SERIAL PRIMARY KEY,
    volume VARCHAR(100) NOT NULL,
    book VARCHAR(100) NOT NULL,
    volume_book_index INT NOT NULL,
    chapter INT NOT NULL,
    verse INT NOT NULL,
    text TEXT NOT NULL,
    clean_text TEXT NOT NULL,
    hugging_face_bge_embedding vector(768) NOT NULL,
    openai_ada_002_embedding vector(1536) NOT NULL,
    openai_3_small_embedding vector(1536) NOT NULL,
    UNIQUE(volume, book, chapter, verse)
);

CREATE TABLE IF NOT EXISTS similar_verse (
    base_verse_id INT NOT NULL,
    similar_verse_id INT NOT NULL,
    embedding_model VARCHAR(100) NOT NULL,
    score FLOAT NOT NULL,
    UNIQUE (base_verse_id, similar_verse_id, embedding_model),
    FOREIGN KEY (base_verse_id) REFERENCES verse(id),
    FOREIGN KEY (similar_verse_id) REFERENCES verse(id)
);

SET maintenance_work_mem = '1GB';
SET hnsw.max_scan_tuples = 3072;
CREATE INDEX IF NOT EXISTS idx_hugging_face_bge_embedding ON verse USING hnsw (hugging_face_bge_embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_openai_ada_002_embedding ON verse USING hnsw (openai_ada_002_embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_openai_3_small_embedding ON verse USING hnsw (openai_3_small_embedding vector_cosine_ops);
-- migrate:down

DROP TABLE IF EXISTS similar_verse;

DROP TABLE IF EXISTS verse;

DROP EXTENSION IF EXISTS vector;
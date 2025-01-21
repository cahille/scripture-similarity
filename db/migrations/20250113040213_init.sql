-- migrate:up
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS verse (
    id SERIAL PRIMARY KEY,
    volume VARCHAR(100) NOT NULL,
    book VARCHAR(100) NOT NULL,
    chapter INT NOT NULL,
    verse INT NOT NULL,
    text TEXT NOT NULL,
    clean_text TEXT NOT NULL,
    embedding vector(768) NOT NULL,
    UNIQUE(volume, book, chapter, verse)
);

CREATE TABLE IF NOT EXISTS similar_verse (
    base_verse_id INT NOT NULL,
    similar_verse_id INT NOT NULL,
    score FLOAT NOT NULL,
    UNIQUE (base_verse_id, similar_verse_id),
    FOREIGN KEY (base_verse_id) REFERENCES verse(id),
    FOREIGN KEY (similar_verse_id) REFERENCES verse(id)
);

-- migrate:down

DROP TABLE IF EXISTS verse;

DROP TABLE IF EXISTS similar_verse;

DROP EXTENSION IF EXISTS vector;
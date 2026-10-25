CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    document_id text PRIMARY KEY,
    title text NOT NULL,
    audience text NOT NULL CHECK (audience IN ('operator', 'auditor', 'both'))
);

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id text PRIMARY KEY,
    document_id text NOT NULL REFERENCES documents (document_id),
    section_path text NOT NULL,
    ordinal integer NOT NULL CHECK (ordinal >= 0),
    page integer NOT NULL CHECK (page >= 1),
    body text NOT NULL,
    content_hash text NOT NULL,
    embedding_model text NOT NULL,
    embedding_version text NOT NULL,
    embedding vector NOT NULL,
    search_vector tsvector GENERATED ALWAYS AS (to_tsvector('english', body)) STORED,
    UNIQUE (document_id, section_path, ordinal)
);

-- Lexical index only. Vector search is an exact scan until a measurement says otherwise.
CREATE INDEX IF NOT EXISTS chunks_search_vector_idx ON chunks USING gin (search_vector);

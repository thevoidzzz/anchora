"""PostgreSQL catalog. Chunk ids are the ones the chunker already assigned."""

import hashlib
import math
from collections.abc import Sequence
from pathlib import Path
from typing import cast

import psycopg
from psycopg.rows import dict_row

from anchora.domain.embedding import EmbeddingIdentity
from anchora.domain.errors import IngestError, SearchError
from anchora.domain.manual import Audience, Chunk, Role

_SCHEMA = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")


class PostgresCatalog:
    """One connection string. Each call is its own transaction."""

    def __init__(self, database_url: str) -> None:
        self._database_url = database_url

    def ensure_schema(self) -> None:
        with psycopg.connect(self._database_url) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            if _chunks_lack_embedding(conn):
                conn.execute("DROP TABLE IF EXISTS chunks")
                conn.execute("DROP TABLE IF EXISTS documents")
            conn.execute(_SCHEMA)

    def clear(self) -> None:
        with psycopg.connect(self._database_url) as conn:
            conn.execute("TRUNCATE documents CASCADE")

    def save(
        self,
        chunks: Sequence[Chunk],
        embeddings: Sequence[Sequence[float]],
        identity: EmbeddingIdentity,
    ) -> None:
        if not chunks:
            raise IngestError("nothing to save")
        document_id = chunks[0].document_id
        title = chunks[0].document_title
        audience = chunks[0].audience
        if any(
            chunk.document_id != document_id or chunk.document_title != title or chunk.audience != audience
            for chunk in chunks
        ):
            raise IngestError("a save covers one document")
        if len(embeddings) != len(chunks):
            raise IngestError("each chunk needs one embedding")
        vectors = [_vector_literal(vector, identity.dimensions) for vector in embeddings]
        ids = [chunk.chunk_id for chunk in chunks]
        rows = [
            (
                chunk.chunk_id,
                chunk.document_id,
                chunk.section_path,
                chunk.ordinal,
                chunk.page,
                chunk.text,
                hashlib.sha256(chunk.text.encode("utf-8")).hexdigest(),
                identity.name,
                identity.version,
                vector,
            )
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
        with psycopg.connect(self._database_url) as conn:
            _reject_other_model(conn, identity)
            conn.execute(
                """
                INSERT INTO documents (document_id, title, audience)
                VALUES (%s, %s, %s)
                ON CONFLICT (document_id) DO UPDATE
                SET title = EXCLUDED.title, audience = EXCLUDED.audience
                """,
                (document_id, title, audience),
            )
            conn.execute(
                """
                DELETE FROM chunks
                WHERE document_id = %s AND NOT (chunk_id = ANY(%s))
                """,
                (document_id, ids),
            )
            conn.cursor().executemany(
                """
                INSERT INTO chunks (
                    chunk_id, document_id, section_path, ordinal, page, body, content_hash,
                    embedding_model, embedding_version, embedding
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::vector)
                ON CONFLICT (chunk_id) DO UPDATE
                SET section_path = EXCLUDED.section_path,
                    ordinal = EXCLUDED.ordinal,
                    page = EXCLUDED.page,
                    body = EXCLUDED.body,
                    content_hash = EXCLUDED.content_hash,
                    embedding_model = EXCLUDED.embedding_model,
                    embedding_version = EXCLUDED.embedding_version,
                    embedding = EXCLUDED.embedding
                """,
                rows,
            )

    def ids_for(self, document_id: str) -> tuple[str, ...]:
        with psycopg.connect(self._database_url, row_factory=dict_row) as conn:
            rows = conn.execute(
                """
                SELECT chunk_id FROM chunks
                WHERE document_id = %s
                ORDER BY section_path, ordinal
                """,
                (document_id,),
            ).fetchall()
        return tuple(row["chunk_id"] for row in rows)

    def get(self, chunk_id: str) -> Chunk | None:
        with psycopg.connect(self._database_url, row_factory=dict_row) as conn:
            row = conn.execute(
                """
                SELECT c.chunk_id, c.document_id, d.title, d.audience,
                       c.section_path, c.ordinal, c.page, c.body
                FROM chunks c
                JOIN documents d ON d.document_id = c.document_id
                WHERE c.chunk_id = %s
                """,
                (chunk_id,),
            ).fetchone()
        if row is None:
            return None
        return _chunk(row)

    def search(self, term: str, role: Role) -> tuple[Chunk, ...]:
        with psycopg.connect(self._database_url, row_factory=dict_row) as conn:
            rows = conn.execute(
                """
                SELECT c.chunk_id, c.document_id, d.title, d.audience,
                       c.section_path, c.ordinal, c.page, c.body
                FROM chunks c
                JOIN documents d ON d.document_id = c.document_id
                WHERE c.search_vector @@ plainto_tsquery('english', %s)
                  AND d.audience IN (%s, 'both')
                ORDER BY ts_rank(c.search_vector, plainto_tsquery('english', %s)) DESC,
                         c.chunk_id
                """,
                (term, role, term),
            ).fetchall()
        return tuple(_chunk(row) for row in rows)

    def embedding_identity(self) -> EmbeddingIdentity | None:
        with psycopg.connect(self._database_url) as conn:
            return _stored_identity(conn)

    def nearest(self, vector: Sequence[float], role: Role, identity: EmbeddingIdentity) -> tuple[Chunk, ...]:
        stored = self.embedding_identity()
        if stored is None:
            return ()
        if stored != identity:
            raise SearchError("query embedding model does not match the stored catalog")
        try:
            literal = _vector_literal(vector, identity.dimensions)
        except IngestError as exc:
            raise SearchError(str(exc)) from exc
        with psycopg.connect(self._database_url, row_factory=dict_row) as conn:
            rows = conn.execute(
                """
                SELECT c.chunk_id, c.document_id, d.title, d.audience,
                       c.section_path, c.ordinal, c.page, c.body
                FROM chunks c
                JOIN documents d ON d.document_id = c.document_id
                WHERE d.audience IN (%s, 'both')
                  AND c.embedding_model = %s
                  AND c.embedding_version = %s
                ORDER BY c.embedding <=> %s::vector, c.chunk_id
                """,
                (role, identity.name, identity.version, literal),
            ).fetchall()
        return tuple(_chunk(row) for row in rows)


def _chunks_lack_embedding(conn: psycopg.Connection) -> bool:
    row = conn.execute(
        """
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'chunks'
        ) AND NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'chunks' AND column_name = 'embedding'
        )
        """
    ).fetchone()
    return bool(row and row[0])


def _stored_identity(conn: psycopg.Connection) -> EmbeddingIdentity | None:
    rows = conn.execute(
        """
        SELECT DISTINCT embedding_model, embedding_version, vector_dims(embedding) AS dimensions
        FROM chunks
        """
    ).fetchall()
    if not rows:
        return None
    if len(rows) > 1:
        raise IngestError("embedding model does not match the stored catalog")
    row = rows[0]
    return EmbeddingIdentity(str(row[0]), str(row[1]), int(row[2]))


def _reject_other_model(conn: psycopg.Connection, identity: EmbeddingIdentity) -> None:
    stored = _stored_identity(conn)
    if stored is not None and stored != identity:
        raise IngestError("embedding model does not match the stored catalog")


def _vector_literal(values: Sequence[float], dimensions: int) -> str:
    if len(values) != dimensions:
        raise IngestError("embedding dimensions do not match the model")
    parts: list[str] = []
    for value in values:
        number = float(value)
        if not math.isfinite(number):
            raise IngestError("embedding values must be finite")
        parts.append(repr(number))
    return "[" + ",".join(parts) + "]"


def _chunk(row: dict[str, object]) -> Chunk:
    return Chunk(
        chunk_id=str(row["chunk_id"]),
        document_id=str(row["document_id"]),
        document_title=str(row["title"]),
        audience=cast(Audience, row["audience"]),
        section_path=str(row["section_path"]),
        ordinal=int(str(row["ordinal"])),
        page=int(str(row["page"])),
        text=str(row["body"]),
    )

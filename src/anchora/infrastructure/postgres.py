"""PostgreSQL catalog. Chunk ids are the ones the chunker already assigned."""

import hashlib
from collections.abc import Sequence
from pathlib import Path
from typing import cast

import psycopg
from psycopg.rows import dict_row

from anchora.domain.errors import IngestError
from anchora.domain.manual import Audience, Chunk

_SCHEMA = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")


class PostgresCatalog:
    """One connection string. Each call is its own transaction."""

    def __init__(self, database_url: str) -> None:
        self._database_url = database_url

    def ensure_schema(self) -> None:
        with psycopg.connect(self._database_url) as conn:
            conn.execute(_SCHEMA)

    def clear(self) -> None:
        with psycopg.connect(self._database_url) as conn:
            conn.execute("TRUNCATE documents CASCADE")

    def save(self, chunks: Sequence[Chunk]) -> None:
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
            )
            for chunk in chunks
        ]
        with psycopg.connect(self._database_url) as conn:
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
                INSERT INTO chunks (chunk_id, document_id, section_path, ordinal, page, body, content_hash)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (chunk_id) DO UPDATE
                SET section_path = EXCLUDED.section_path,
                    ordinal = EXCLUDED.ordinal,
                    page = EXCLUDED.page,
                    body = EXCLUDED.body,
                    content_hash = EXCLUDED.content_hash
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
        return Chunk(
            chunk_id=row["chunk_id"],
            document_id=row["document_id"],
            document_title=row["title"],
            audience=cast(Audience, row["audience"]),
            section_path=row["section_path"],
            ordinal=row["ordinal"],
            page=row["page"],
            text=row["body"],
        )

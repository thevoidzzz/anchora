"""Load a manual into the catalog. Ids come from the chunker, not from the database."""

from anchora.application.ports import DocumentCatalog, Embedder
from anchora.domain.manual import Chunk, ChunkConfig, parse_manual


def ingest_manual(
    text: str,
    catalog: DocumentCatalog,
    embedder: Embedder,
    config: ChunkConfig | None = None,
) -> tuple[Chunk, ...]:
    """Parse a manual, embed it with one model, and store it.

    A second call with the same sections keeps the ids and replaces the vectors.
    """

    chunks = parse_manual(text, config)
    catalog.save(chunks, embedder.embed(tuple(chunk.text for chunk in chunks)), embedder.identity())
    return chunks

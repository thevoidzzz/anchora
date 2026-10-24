"""Load a manual into the catalog. Ids come from the chunker, not from the database."""

from anchora.application.ports import DocumentCatalog
from anchora.domain.manual import Chunk, ChunkConfig, parse_manual


def ingest_manual(
    text: str,
    catalog: DocumentCatalog,
    config: ChunkConfig | None = None,
) -> tuple[Chunk, ...]:
    """Parse a manual and store it. A second call with the same sections keeps the ids."""

    chunks = parse_manual(text, config)
    catalog.save(chunks)
    return chunks

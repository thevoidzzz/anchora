"""Ports the application needs. Infrastructure implements them."""

from collections.abc import Sequence
from typing import Protocol

from anchora.domain.manual import Chunk


class DocumentCatalog(Protocol):
    """Stored manuals. A save replaces one document and leaves the others in place."""

    def save(self, chunks: Sequence[Chunk]) -> None:
        """Upsert one document. Chunk ids that this load no longer has are removed."""

    def ids_for(self, document_id: str) -> tuple[str, ...]:
        """Chunk ids of one document, in section order."""

    def get(self, chunk_id: str) -> Chunk | None:
        """The stored chunk, or none when that id is not in the catalog."""

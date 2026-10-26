"""Ports the application needs. Infrastructure implements them."""

from collections.abc import Sequence
from typing import Protocol

from anchora.domain.embedding import EmbeddingIdentity
from anchora.domain.manual import Chunk, Role
from anchora.domain.model import ModelCompletion


class Embedder(Protocol):
    """Turns passage text into vectors. Tests use a deterministic stand-in."""

    def identity(self) -> EmbeddingIdentity:
        """The model that will produce the vectors."""

    def embed(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]:
        """One vector per text, in the same order, in this model's space."""


class DocumentCatalog(Protocol):
    """Stored manuals. A save replaces one document and leaves the others in place."""

    def save(
        self,
        chunks: Sequence[Chunk],
        embeddings: Sequence[Sequence[float]],
        identity: EmbeddingIdentity,
    ) -> None:
        """Upsert one document. Chunk ids that this load no longer has are removed."""

    def ids_for(self, document_id: str) -> tuple[str, ...]:
        """Chunk ids of one document, in section order."""

    def get(self, chunk_id: str) -> Chunk | None:
        """The stored chunk, or none when that id is not in the catalog."""

    def search(self, term: str, role: Role) -> tuple[Chunk, ...]:
        """Lexical matches this role may see. Audience both is included. Other roles are not."""

    def embedding_identity(self) -> EmbeddingIdentity | None:
        """The model stored on the chunks, or none when the catalog is empty."""

    def nearest(
        self,
        vector: Sequence[float],
        role: Role,
        identity: EmbeddingIdentity,
    ) -> tuple[Chunk, ...]:
        """Every chunk this role may see, nearest cosine distance first. No similarity cutoff."""


class LanguageModel(Protocol):
    """Drafts an answer from passages the catalog already filtered. It does not write citations."""

    def complete(self, question: str, passages: Sequence[Chunk]) -> ModelCompletion:
        """Return a draft and the chunk ids to cite. The server copies the excerpts."""

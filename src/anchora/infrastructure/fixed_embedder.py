"""Deterministic vectors. Tests and a local run use this instead of a hosted model."""

import hashlib
from collections.abc import Mapping, Sequence

from anchora.domain.embedding import EmbeddingIdentity


class FixedEmbedder:
    """One stable unit vector per text. Assigned texts keep the vector they were given."""

    def __init__(
        self,
        *,
        name: str = "fixed-embedder",
        version: str = "1",
        dimensions: int = 8,
        assigned: Mapping[str, Sequence[float]] | None = None,
    ) -> None:
        self._identity = EmbeddingIdentity(name, version, dimensions)
        self._assigned = dict(assigned or {})

    def identity(self) -> EmbeddingIdentity:
        return self._identity

    def embed(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]:
        return tuple(self._vector(text) for text in texts)

    def _vector(self, text: str) -> tuple[float, ...]:
        if text in self._assigned:
            return tuple(float(value) for value in self._assigned[text])
        slot = int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:4], "big") % self._identity.dimensions
        values = [0.0] * self._identity.dimensions
        values[slot] = 1.0
        return tuple(values)

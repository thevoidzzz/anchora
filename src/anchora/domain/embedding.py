"""Which model produced a vector. A neighbor search is only valid inside that space."""

from dataclasses import dataclass

from anchora.domain.errors import EmbeddingIdentityError


@dataclass(frozen=True, slots=True)
class EmbeddingIdentity:
    """Name, version, and width. Two versions are different spaces."""

    name: str
    version: str
    dimensions: int

    def __post_init__(self) -> None:
        if self.name.strip() == "" or self.version.strip() == "":
            raise EmbeddingIdentityError("embedding model name and version are required")
        if self.dimensions < 1:
            raise EmbeddingIdentityError("embedding dimensions must be at least 1")

"""Domain types. This package does not import infrastructure or the API."""

from anchora.domain.errors import ChunkConfigError, ManualError
from anchora.domain.manual import (
    DEFAULT_MAX_CHARS,
    DEFAULT_OVERLAP_CHARS,
    Chunk,
    ChunkConfig,
    parse_manual,
)

__all__ = [
    "DEFAULT_MAX_CHARS",
    "DEFAULT_OVERLAP_CHARS",
    "Chunk",
    "ChunkConfig",
    "ChunkConfigError",
    "ManualError",
    "parse_manual",
]

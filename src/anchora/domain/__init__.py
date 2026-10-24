"""Domain types. This package does not import infrastructure or the API."""

from anchora.domain.citation import AssembledAnswer, Citation, assemble_answer
from anchora.domain.errors import (
    ChunkConfigError,
    DuplicateRetrievedChunkError,
    IngestError,
    ManualError,
    SearchError,
)
from anchora.domain.manual import (
    DEFAULT_MAX_CHARS,
    DEFAULT_OVERLAP_CHARS,
    Chunk,
    ChunkConfig,
    Role,
    parse_manual,
)

__all__ = [
    "DEFAULT_MAX_CHARS",
    "DEFAULT_OVERLAP_CHARS",
    "AssembledAnswer",
    "Chunk",
    "ChunkConfig",
    "ChunkConfigError",
    "Citation",
    "DuplicateRetrievedChunkError",
    "IngestError",
    "ManualError",
    "Role",
    "SearchError",
    "assemble_answer",
    "parse_manual",
]

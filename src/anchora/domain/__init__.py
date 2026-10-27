"""Domain types. This package does not import infrastructure or the API."""

from anchora.domain.citation import AssembledAnswer, Citation, assemble_answer
from anchora.domain.embedding import EmbeddingIdentity
from anchora.domain.errors import (
    CatalogUnavailable,
    ChunkConfigError,
    DuplicateRetrievedChunkError,
    EmbeddingIdentityError,
    FusionError,
    IngestError,
    ManualError,
    ModelSchemaError,
    ModelTimeout,
    RequestError,
    SearchError,
)
from anchora.domain.fusion import FUSION_LIMIT, RRF_K, fuse_rankings
from anchora.domain.limits import QUESTION_MAX_CHARS
from anchora.domain.model import ModelCompletion
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
    "CatalogUnavailable",
    "DuplicateRetrievedChunkError",
    "EmbeddingIdentity",
    "EmbeddingIdentityError",
    "FUSION_LIMIT",
    "FusionError",
    "IngestError",
    "ManualError",
    "ModelCompletion",
    "ModelSchemaError",
    "ModelTimeout",
    "QUESTION_MAX_CHARS",
    "RRF_K",
    "RequestError",
    "Role",
    "SearchError",
    "assemble_answer",
    "fuse_rankings",
    "parse_manual",
]

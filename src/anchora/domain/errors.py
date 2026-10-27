"""Failures of a manual or of a chunk window. Callers can catch these."""


class ManualError(ValueError):
    """The manual text cannot be chunked."""


class ChunkConfigError(ValueError):
    """The character window cannot be used."""


class IngestError(ValueError):
    """The chunks cannot be stored."""


class EmbeddingIdentityError(ValueError):
    """The embedding model identity cannot be used."""


class SearchError(ValueError):
    """The search cannot run. The role is operator or auditor."""


class RequestError(ValueError):
    """The question cannot be accepted."""


class CatalogUnavailable(Exception):
    """The catalog cannot be reached."""


class ModelSchemaError(Exception):
    """The model response did not match the schema."""


class ModelTimeout(Exception):
    """The model did not respond in time."""


class FusionError(ValueError):
    """The rankings cannot be fused."""


class DuplicateRetrievedChunkError(ValueError):
    """The same chunk id arrived twice in one retrieval."""

    def __init__(self, chunk_id: str) -> None:
        self.chunk_id = chunk_id
        super().__init__(f"duplicate retrieved chunk: {chunk_id}")

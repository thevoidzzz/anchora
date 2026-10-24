"""Failures of a manual or of a chunk window. Callers can catch these."""


class ManualError(ValueError):
    """The manual text cannot be chunked."""


class ChunkConfigError(ValueError):
    """The character window cannot be used."""


class IngestError(ValueError):
    """The chunks cannot be stored as one document."""


class SearchError(ValueError):
    """The search cannot run. The role is operator or auditor."""


class DuplicateRetrievedChunkError(ValueError):
    """The same chunk id arrived twice in one retrieval."""

    def __init__(self, chunk_id: str) -> None:
        self.chunk_id = chunk_id
        super().__init__(f"duplicate retrieved chunk: {chunk_id}")

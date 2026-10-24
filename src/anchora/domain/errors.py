"""Failures of a manual or of a chunk window. Callers can catch these."""


class ManualError(ValueError):
    """The manual text cannot be chunked."""


class ChunkConfigError(ValueError):
    """The character window cannot be used."""

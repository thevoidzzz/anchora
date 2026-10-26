"""What the model is allowed to return. It does not write the excerpt."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ModelCompletion:
    """A draft and the chunk ids the model chose. Tokens are counted by the provider."""

    draft: str
    chunk_ids: tuple[str, ...]
    model: str
    input_tokens: int
    output_tokens: int

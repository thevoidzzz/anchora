"""Cites every passage it was given. No network and no key."""

from collections.abc import Sequence

from anchora.domain.manual import Chunk
from anchora.domain.model import ModelCompletion


class CitingModel:
    """A stand-in language model. The excerpt still comes from the server."""

    def complete(self, question: str, passages: Sequence[Chunk]) -> ModelCompletion:
        return ModelCompletion(
            draft="See the cited passages.",
            chunk_ids=tuple(passage.chunk_id for passage in passages),
            model="citing-stand-in",
            input_tokens=len(passages),
            output_tokens=1,
        )

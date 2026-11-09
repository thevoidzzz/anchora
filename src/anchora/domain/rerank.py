"""Reorder the fused passages. This does not replace the fusion."""

import re
from collections.abc import Sequence

from anchora.domain.manual import Chunk

_TOKEN = re.compile(r"[a-z0-9]+")


def rerank_passages(question: str, passages: Sequence[Chunk]) -> tuple[Chunk, ...]:
    """Order by shared tokens with the question. A tie keeps the fusion order."""

    needles = _tokens(question)
    ranked = sorted(
        enumerate(passages),
        key=lambda pair: (-len(_tokens(pair[1].text) & needles), pair[0]),
    )
    return tuple(passage for _, passage in ranked)


def _tokens(text: str) -> set[str]:
    return set(_TOKEN.findall(text.lower()))

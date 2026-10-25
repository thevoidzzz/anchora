"""Reciprocal rank fusion. The inputs are ranks, not scores from different scales."""

from collections.abc import Sequence

from anchora.domain.errors import DuplicateRetrievedChunkError, FusionError

RRF_K = 60
FUSION_LIMIT = 5


def fuse_rankings(
    rankings: Sequence[Sequence[str]],
    *,
    k: int = RRF_K,
    limit: int = FUSION_LIMIT,
) -> tuple[str, ...]:
    """Sum `1 / (k + rank)` per list. Rank starts at 1. Ties break by chunk id."""

    if k < 1:
        raise FusionError("k must be at least 1")
    if limit < 1:
        raise FusionError("limit must be at least 1")
    scores: dict[str, float] = {}
    for ranking in rankings:
        seen: set[str] = set()
        for rank, chunk_id in enumerate(ranking, start=1):
            if chunk_id in seen:
                raise DuplicateRetrievedChunkError(chunk_id)
            seen.add(chunk_id)
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank)
    ordered = sorted(scores, key=lambda chunk_id: (-scores[chunk_id], chunk_id))
    return tuple(ordered[:limit])

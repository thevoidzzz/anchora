"""Retrieval. The audience predicate belongs to the catalog, in the query."""

from typing import cast

from anchora.application.ports import DocumentCatalog, Embedder
from anchora.domain.errors import SearchError
from anchora.domain.fusion import FUSION_LIMIT, RRF_K, fuse_rankings
from anchora.domain.manual import Chunk, Role

_ROLES = frozenset({"operator", "auditor"})


def find_passages(term: str, role: str, catalog: DocumentCatalog) -> tuple[Chunk, ...]:
    """Passages whose text matches the term and whose audience is this role or both.

    Rank is the catalog's. This function does not drop rows afterwards.
    """

    return catalog.search(term, _require_role(role))


def find_nearest(question: str, role: str, catalog: DocumentCatalog, embedder: Embedder) -> tuple[Chunk, ...]:
    """Nearest passages in the query model's space. The catalog applies the audience predicate."""

    checked = _require_role(role)
    vectors = embedder.embed((question,))
    if len(vectors) != 1:
        raise SearchError("the embedder must return one query vector")
    return catalog.nearest(vectors[0], checked, embedder.identity())


def retrieve(
    question: str,
    role: str,
    catalog: DocumentCatalog,
    embedder: Embedder,
    *,
    k: int = RRF_K,
    limit: int = FUSION_LIMIT,
) -> tuple[Chunk, ...]:
    """Fuse the lexical list and the nearest-neighbor list.

    A passage in both lists can outrank the leader of one list. The text rank and the
    cosine distance are not added.
    """

    lexical = find_passages(question, role, catalog)
    vector = find_nearest(question, role, catalog, embedder)
    by_id: dict[str, Chunk] = {}
    for chunk in (*lexical, *vector):
        by_id.setdefault(chunk.chunk_id, chunk)
    order = fuse_rankings(
        (
            tuple(chunk.chunk_id for chunk in lexical),
            tuple(chunk.chunk_id for chunk in vector),
        ),
        k=k,
        limit=limit,
    )
    return tuple(by_id[chunk_id] for chunk_id in order)


def _require_role(role: str) -> Role:
    if role not in _ROLES:
        raise SearchError("role must be operator or auditor")
    return cast(Role, role)

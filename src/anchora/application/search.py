"""Retrieval. The audience predicate belongs to the catalog, in the query."""

from typing import cast

from anchora.application.ports import DocumentCatalog, Embedder
from anchora.domain.errors import SearchError
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


def _require_role(role: str) -> Role:
    if role not in _ROLES:
        raise SearchError("role must be operator or auditor")
    return cast(Role, role)

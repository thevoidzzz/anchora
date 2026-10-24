"""Lexical search. The audience predicate belongs to the catalog, in the query."""

from typing import cast

from anchora.application.ports import DocumentCatalog
from anchora.domain.errors import SearchError
from anchora.domain.manual import Chunk, Role

_ROLES = frozenset({"operator", "auditor"})


def find_passages(term: str, role: str, catalog: DocumentCatalog) -> tuple[Chunk, ...]:
    """Passages whose text matches the term and whose audience is this role or both.

    Rank is the catalog's. This function does not drop rows afterwards.
    """

    if role not in _ROLES:
        raise SearchError("role must be operator or auditor")
    return catalog.search(term, cast(Role, role))

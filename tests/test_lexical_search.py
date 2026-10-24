"""An exact term comes back for the role that may see it, and not for the other."""

import pytest

from anchora.application import find_passages, ingest_manual
from anchora.domain import SearchError
from anchora.infrastructure.postgres import PostgresCatalog


def _manual(document_id: str, title: str, audience: str, body: str) -> str:
    return f"---\nid: {document_id}\ntitle: {title}\naudience: {audience}\n---\n\n{body}"


def _section(heading: str, page: int, text: str) -> str:
    return f"## {heading}\npage: {page}\n\n{text}\n"


@pytest.fixture
def catalog(database_url: str) -> PostgresCatalog:
    store = PostgresCatalog(database_url)
    store.ensure_schema()
    store.clear()
    return store


def test_an_exact_term_stays_inside_the_role(catalog: PostgresCatalog) -> None:
    operator = ingest_manual(
        _manual(
            "month-end-close",
            "Month-end close",
            "operator",
            _section("Book the batch", 4, "The desk books Meridian before noon."),
        ),
        catalog,
    )
    auditor = ingest_manual(
        _manual(
            "approval-limits",
            "Approval limits",
            "auditor",
            _section("Sample the batch", 2, "The desk books Meridian before noon."),
        ),
        catalog,
    )
    shared = ingest_manual(
        _manual(
            "close-codes",
            "Close codes",
            "both",
            _section("Codes", 1, "Meridian is the close code for that desk."),
        ),
        catalog,
    )
    operator_id = operator[0].chunk_id
    auditor_id = auditor[0].chunk_id
    shared_id = shared[0].chunk_id

    for_operator = find_passages("Meridian", "operator", catalog)
    for_auditor = find_passages("Meridian", "auditor", catalog)

    assert {chunk.chunk_id for chunk in for_operator} == {operator_id, shared_id}
    assert {chunk.audience for chunk in for_operator} <= {"operator", "both"}
    assert {chunk.chunk_id for chunk in for_auditor} == {auditor_id, shared_id}
    assert {chunk.audience for chunk in for_auditor} <= {"auditor", "both"}
    assert catalog.ids_for("approval-limits") == (auditor_id,)
    assert catalog.ids_for("month-end-close") == (operator_id,)
    assert catalog.get(auditor_id) is not None
    assert catalog.get(operator_id) is not None


def test_a_role_outside_the_two_desks_is_rejected() -> None:
    with pytest.raises(SearchError, match="operator or auditor"):
        find_passages("Meridian", "both", _Catalog())


class _Catalog:
    def search(self, term: str, role: str) -> tuple[object, ...]:
        raise AssertionError("the catalog must not be queried")

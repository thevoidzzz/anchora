"""Reingest keeps chunk ids. Another document stays in the catalog."""

import pytest

from anchora.application import ingest_manual
from anchora.domain import IngestError, parse_manual
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


def test_reingest_keeps_ids_and_leaves_the_other_document(catalog: PostgresCatalog) -> None:
    close = _manual(
        "month-end-close",
        "Month-end close",
        "operator",
        _section("Tie-out the trial balance", 4, "The operator compares the ledger."),
    )
    limits = _manual(
        "approval-limits",
        "Approval limits",
        "auditor",
        _section("Sample the journal", 2, "The auditor samples the journal."),
    )
    first = ingest_manual(close, catalog)
    ingest_manual(limits, catalog)
    edited = ingest_manual(close.replace("ledger", "journal"), catalog)

    assert [chunk.chunk_id for chunk in edited] == [chunk.chunk_id for chunk in first]
    assert catalog.ids_for("month-end-close") == (first[0].chunk_id,)
    assert catalog.ids_for("approval-limits") == ("approval-limits#Sample the journal#0",)
    stored = catalog.get(first[0].chunk_id)
    assert stored is not None
    assert stored.text == "The operator compares the journal."
    assert stored.audience == "operator"
    assert stored.page == 4


def test_removing_a_section_drops_only_that_id(catalog: PostgresCatalog) -> None:
    both = _section("Open", 1, "Open the period.") + "\n" + _section("Close", 2, "Close the period.")
    manual = _manual("month-end-close", "Month-end close", "both", both)
    ingest_manual(manual, catalog)
    ingest_manual(_manual("month-end-close", "Month-end close", "both", _section("Open", 1, "Open the period.")), catalog)

    assert catalog.ids_for("month-end-close") == ("month-end-close#Open#0",)
    assert catalog.get("month-end-close#Close#0") is None
    kept = catalog.get("month-end-close#Open#0")
    assert kept is not None
    assert kept.audience == "both"


def test_a_save_refuses_chunks_from_two_documents(catalog: PostgresCatalog) -> None:
    close = parse_manual(
        _manual("month-end-close", "Month-end close", "operator", _section("Open", 1, "Open the period."))
    )
    limits = parse_manual(
        _manual("approval-limits", "Approval limits", "auditor", _section("Sample", 2, "Sample the journal."))
    )

    with pytest.raises(IngestError, match="one document"):
        catalog.save(close + limits)

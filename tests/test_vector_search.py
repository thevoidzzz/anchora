"""The nearest passage stays inside the role. A second embedding model is refused."""

import psycopg
import pytest

from anchora.application import find_nearest, ingest_manual
from anchora.domain import IngestError, SearchError
from anchora.infrastructure.fixed_embedder import FixedEmbedder
from anchora.infrastructure.postgres import PostgresCatalog

_NEAR = "Book Meridian at the desk."
_FAR = "Count the drawers."
_SHARED = "Meridian is the close code."


def _axis(index: int, dimensions: int = 8) -> tuple[float, ...]:
    values = [0.0] * dimensions
    values[index] = 1.0
    return tuple(values)


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


def test_the_nearest_passage_stays_inside_the_role(catalog: PostgresCatalog) -> None:
    embedder = FixedEmbedder(assigned={_NEAR: _axis(0), _FAR: _axis(4), _SHARED: _axis(4)})
    operator = ingest_manual(
        _manual("month-end-close", "Month-end close", "operator", _section("Book the batch", 4, _NEAR)),
        catalog,
        embedder,
    )
    auditor = ingest_manual(
        _manual("approval-limits", "Approval limits", "auditor", _section("Sample the batch", 2, _NEAR)),
        catalog,
        embedder,
    )
    shared = ingest_manual(
        _manual("close-codes", "Close codes", "both", _section("Codes", 1, _SHARED)),
        catalog,
        embedder,
    )
    operator_id = operator[0].chunk_id
    shared_id = shared[0].chunk_id
    auditor_id = auditor[0].chunk_id

    nearest = find_nearest(_NEAR, "operator", catalog, embedder)

    assert [chunk.chunk_id for chunk in nearest] == [operator_id, shared_id]
    assert catalog.ids_for("approval-limits") == (auditor_id,)

    ingest_manual(
        _manual("month-end-close", "Month-end close", "operator", _section("Book the batch", 4, _FAR)),
        catalog,
        embedder,
    )
    after_edit = find_nearest(_NEAR, "operator", catalog, embedder)

    assert [chunk.chunk_id for chunk in after_edit] == [shared_id, operator_id]
    assert catalog.get(auditor_id) is not None
    assert auditor_id not in {chunk.chunk_id for chunk in after_edit}


def test_a_different_embedding_model_is_refused(catalog: PostgresCatalog) -> None:
    current = FixedEmbedder(version="1")
    replacement = FixedEmbedder(version="2")
    stored = ingest_manual(
        _manual("month-end-close", "Month-end close", "operator", _section("Book the batch", 4, _NEAR)),
        catalog,
        current,
    )

    with pytest.raises(IngestError, match="does not match"):
        ingest_manual(
            _manual("approval-limits", "Approval limits", "auditor", _section("Sample the batch", 2, _NEAR)),
            catalog,
            replacement,
        )

    assert catalog.embedding_identity() == current.identity()
    assert catalog.ids_for("month-end-close") == (stored[0].chunk_id,)
    with pytest.raises(SearchError, match="does not match"):
        find_nearest(_NEAR, "operator", catalog, replacement)

    catalog.clear()
    ingest_manual(
        _manual("month-end-close", "Month-end close", "operator", _section("Book the batch", 4, _FAR)),
        catalog,
        replacement,
    )
    assert [chunk.chunk_id for chunk in find_nearest(_FAR, "operator", catalog, replacement)] == [
        "month-end-close#Book the batch#0"
    ]
    with pytest.raises(SearchError, match="does not match"):
        find_nearest(_FAR, "operator", catalog, current)


def test_a_vector_of_the_wrong_width_is_refused(catalog: PostgresCatalog) -> None:
    text = "Open the period."
    embedder = FixedEmbedder(assigned={text: (1.0, 0.0)})

    with pytest.raises(IngestError, match="dimensions"):
        ingest_manual(
            _manual("month-end-close", "Month-end close", "operator", _section("Open", 1, text)),
            catalog,
            embedder,
        )

    assert catalog.ids_for("month-end-close") == ()


def test_vector_search_does_not_build_an_approximate_index(database_url: str, catalog: PostgresCatalog) -> None:
    with psycopg.connect(database_url) as conn:
        rows = conn.execute(
            """
            SELECT indexdef FROM pg_indexes
            WHERE schemaname = 'public'
              AND (indexdef ILIKE '%hnsw%' OR indexdef ILIKE '%ivfflat%')
            """
        ).fetchall()
    assert rows == []

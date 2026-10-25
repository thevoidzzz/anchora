"""Lexical and vector ranks fuse by reciprocal rank. The other role stays out."""

import pytest

from anchora.application import ingest_manual, retrieve
from anchora.domain import (
    FUSION_LIMIT,
    RRF_K,
    DuplicateRetrievedChunkError,
    FusionError,
    fuse_rankings,
)
from anchora.infrastructure.fixed_embedder import FixedEmbedder
from anchora.infrastructure.postgres import PostgresCatalog


def _axis(index: int, dimensions: int = 8) -> tuple[float, ...]:
    values = [0.0] * dimensions
    values[index] = 1.0
    return tuple(values)


def test_a_passage_in_both_lists_outranks_the_leader_of_one() -> None:
    assert RRF_K == 60
    assert fuse_rankings((["shared", "lexical-only"], ["vector-only", "shared"])) == (
        "shared",
        "vector-only",
        "lexical-only",
    )


def test_fusion_limit_drops_the_tail() -> None:
    ranking = tuple(f"chunk-{index}" for index in range(6))
    assert FUSION_LIMIT == 5
    assert fuse_rankings((ranking,)) == ranking[:5]


def test_a_repeated_id_in_one_list_is_an_error() -> None:
    with pytest.raises(DuplicateRetrievedChunkError):
        fuse_rankings((["chunk-0", "chunk-0"],))


def test_k_starts_at_one() -> None:
    with pytest.raises(FusionError, match="k must be at least 1"):
        fuse_rankings((["chunk-0"],), k=0)


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


def test_retrieve_keeps_the_lexical_hit_and_the_neighbor_inside_the_role(catalog: PostgresCatalog) -> None:
    lexical_text = "Meridian is the desk code."
    neighbor_text = "Count the drawers tonight."
    auditor_text = "Meridian is the sample code."
    embedder = FixedEmbedder(
        assigned={
            "Meridian": _axis(0),
            lexical_text: _axis(4),
            neighbor_text: _axis(0),
            auditor_text: _axis(0),
        }
    )
    operator = _section("Codes", 1, lexical_text) + "\n" + _section("Drawers", 2, neighbor_text)
    ingest_manual(_manual("month-end-close", "Month-end close", "operator", operator), catalog, embedder)
    auditor = ingest_manual(
        _manual("approval-limits", "Approval limits", "auditor", _section("Sample", 2, auditor_text)),
        catalog,
        embedder,
    )

    hits = retrieve("Meridian", "operator", catalog, embedder)

    assert [chunk.chunk_id for chunk in hits] == [
        "month-end-close#Codes#0",
        "month-end-close#Drawers#0",
    ]
    assert catalog.ids_for("approval-limits") == (auditor[0].chunk_id,)
    assert auditor[0].chunk_id not in {chunk.chunk_id for chunk in hits}

"""No passage for the role means no model call. A citation is still copied from the chunk."""

from collections.abc import Sequence

import pytest

from anchora.application import answer_question, ingest_manual
from anchora.domain import QUESTION_MAX_CHARS, Chunk, ModelCompletion, RequestError, SearchError
from anchora.infrastructure.fixed_embedder import FixedEmbedder
from anchora.infrastructure.postgres import PostgresCatalog


class ScriptedModel:
    """Returns one prepared completion and records the passages it was given."""

    def __init__(self, draft: str, chunk_ids: Sequence[str]) -> None:
        self.calls: list[tuple[str, tuple[Chunk, ...]]] = []
        self._draft = draft
        self._chunk_ids = tuple(chunk_ids)

    def complete(self, question: str, passages: Sequence[Chunk]) -> ModelCompletion:
        copied = tuple(passages)
        self.calls.append((question, copied))
        return ModelCompletion(
            draft=self._draft,
            chunk_ids=self._chunk_ids,
            model="scripted-model",
            input_tokens=11,
            output_tokens=5,
        )


class _ClosedCatalog:
    def search(self, term: str, role: str) -> tuple[Chunk, ...]:
        raise AssertionError("the catalog must not be queried")

    def nearest(self, vector: Sequence[float], role: str, identity: object) -> tuple[Chunk, ...]:
        raise AssertionError("the catalog must not be queried")


def test_a_blank_or_oversized_question_does_not_call_the_model() -> None:
    model = ScriptedModel("unused", ())
    catalog = _ClosedCatalog()
    embedder = FixedEmbedder()

    with pytest.raises(RequestError, match="empty"):
        answer_question("  ", "operator", catalog, embedder, model)
    with pytest.raises(RequestError, match=str(QUESTION_MAX_CHARS)):
        answer_question("m" * (QUESTION_MAX_CHARS + 1), "operator", catalog, embedder, model)
    with pytest.raises(SearchError, match="operator or auditor"):
        answer_question("Where is the close?", "both", catalog, embedder, model)

    assert model.calls == []


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


def test_the_other_roles_manual_does_not_reach_the_model(catalog: PostgresCatalog) -> None:
    embedder = FixedEmbedder()
    auditor = ingest_manual(
        _manual(
            "approval-limits",
            "Approval limits",
            "auditor",
            _section("Sample", 2, "Meridian is the sample code."),
        ),
        catalog,
        embedder,
    )
    model = ScriptedModel("The code is Meridian.", (auditor[0].chunk_id,))

    result = answer_question("Meridian", "operator", catalog, embedder, model)

    assert result.refused is True
    assert result.reason == "no_evidence"
    assert result.answer is None
    assert result.citations == ()
    assert result.model is None
    assert result.input_tokens == 0
    assert result.output_tokens == 0
    assert result.generation_ms == 0
    assert model.calls == []
    assert catalog.ids_for("approval-limits") == (auditor[0].chunk_id,)


def test_a_grounded_answer_copies_the_passage_the_model_was_given(catalog: PostgresCatalog) -> None:
    operator_text = "The desk books the close before noon."
    auditor_text = "Meridian is the sample code."
    embedder = FixedEmbedder()
    operator = ingest_manual(
        _manual("month-end-close", "Month-end close", "operator", _section("Book the batch", 4, operator_text)),
        catalog,
        embedder,
    )
    ingest_manual(
        _manual("approval-limits", "Approval limits", "auditor", _section("Sample", 2, auditor_text)),
        catalog,
        embedder,
    )
    model = ScriptedModel("Book the close before noon.", (operator[0].chunk_id,))

    result = answer_question("Where is the close booked?", "operator", catalog, embedder, model)

    assert model.calls == [("Where is the close booked?", (operator[0],))]
    assert result.refused is False
    assert result.reason is None
    assert result.answer == "Book the close before noon."
    assert result.model == "scripted-model"
    assert result.input_tokens == 11
    assert result.output_tokens == 5
    assert [citation.chunk_id for citation in result.citations] == [operator[0].chunk_id]
    assert result.citations[0].excerpt == operator_text
    assert result.citations[0].page == 4
    assert auditor_text not in {chunk.text for _, passages in model.calls for chunk in passages}


def test_a_foreign_id_refuses_and_drops_the_draft(catalog: PostgresCatalog) -> None:
    embedder = FixedEmbedder()
    operator = ingest_manual(
        _manual(
            "month-end-close",
            "Month-end close",
            "operator",
            _section("Book the batch", 4, "The desk books the close before noon."),
        ),
        catalog,
        embedder,
    )
    auditor = ingest_manual(
        _manual(
            "approval-limits",
            "Approval limits",
            "auditor",
            _section("Sample", 2, "Meridian is the sample code."),
        ),
        catalog,
        embedder,
    )
    model = ScriptedModel("Use the sample code.", (auditor[0].chunk_id,))

    result = answer_question("Where is the close booked?", "operator", catalog, embedder, model)

    assert model.calls[0][1] == (operator[0],)
    assert result.refused is True
    assert result.reason == "no_valid_citation"
    assert result.answer is None
    assert result.citations == ()

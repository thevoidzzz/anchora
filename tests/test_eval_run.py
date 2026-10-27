"""The bundled set prints a report and fails when a relevant section is missing."""

import pytest

from anchora.application.evaluate import evaluate
from anchora.application.search import retrieve
from anchora.domain import EvalError
from anchora.domain.scoring import EvalItem
from anchora.eval.__main__ import main
from anchora.eval.load import load_golden
from anchora.infrastructure.citing_model import CitingModel
from anchora.infrastructure.fixed_embedder import FixedEmbedder
from anchora.infrastructure.postgres import PostgresCatalog


@pytest.fixture
def catalog(database_url: str) -> PostgresCatalog:
    store = PostgresCatalog(database_url)
    store.ensure_schema()
    store.clear()
    return store


def test_the_golden_set_has_fifty_hand_written_questions() -> None:
    items = load_golden()
    assert len(items) == 50
    assert len({item.id for item in items}) == 50
    assert any(item.expect_refusal for item in items)
    assert any(not item.expect_refusal for item in items)


def test_the_report_keeps_an_exact_term_and_hides_the_other_role(
    catalog: PostgresCatalog,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    database_url: str,
) -> None:
    monkeypatch.setenv("DATABASE_URL", database_url)
    main()
    printed = capsys.readouterr().out
    embedder = FixedEmbedder()

    accruals = retrieve("JE-4419", "operator", catalog, embedder)
    hidden = retrieve("JE-4419", "auditor", catalog, embedder)
    velora = retrieve("VELORA", "operator", catalog, embedder)
    lexical = catalog.search("When is the estimate journal recorded?", "operator")

    assert any(chunk.section_path == "Book accruals" for chunk in accruals)
    assert all(chunk.document_id != "month-end-close" for chunk in hidden)
    assert any(chunk.section_path == "Velora schedule" for chunk in velora)
    velora_ids = [chunk_id for chunk_id in catalog.ids_for("month-end-close") if "#Velora schedule#" in chunk_id]
    assert len(velora_ids) == 2
    assert all(chunk.section_path != "Book accruals" for chunk in lexical)
    assert "embedding_model: fixed-embedder\n" in printed
    assert "embedding_version: 1\n" in printed
    assert "language_model: citing-stand-in\n" in printed
    assert "questions: 50\n" in printed
    assert "evidence_questions: 41\n" in printed
    assert "hit_at_5: 0.951\n" in printed
    assert "recall_at_5: 0.956\n" in printed
    assert "citation_validity: 1.000\n" in printed
    assert "correct_refusals: 0\n" in printed
    assert "false_refusals: 0\n" in printed
    assert "missed_refusals: 9\n" in printed


def test_a_missing_relevant_section_fails_before_scoring(catalog: PostgresCatalog) -> None:
    manual = "---\nid: month-end-close\ntitle: Month-end close\naudience: operator\n---\n\n## Open\npage: 1\n\nOpen the period.\n"
    item = EvalItem(
        id="missing",
        role="operator",
        question="Where is the missing section?",
        relevant_sections=("month-end-close#Missing",),
        expect_refusal=False,
    )

    with pytest.raises(EvalError, match="month-end-close#Missing"):
        evaluate(catalog, FixedEmbedder(), CitingModel(), [manual], [item])

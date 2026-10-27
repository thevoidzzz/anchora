"""Hit@5 and recall@5 ignore refusals. A bad excerpt fails citation validity."""

import pytest

from anchora.domain.scoring import EvalItem, QuestionOutcome, format_report, percentile, score_run


def _item(
    item_id: str,
    *,
    relevant: tuple[str, ...] = (),
    expect_refusal: bool = False,
    role: str = "operator",
) -> EvalItem:
    return EvalItem(
        id=item_id,
        role=role,
        question="Where is the code?",
        relevant_sections=relevant,
        expect_refusal=expect_refusal,
    )


def _outcome(
    item: EvalItem,
    retrieved: tuple[str, ...],
    *,
    refused: bool,
) -> QuestionOutcome:
    return QuestionOutcome(item=item, retrieved_sections=retrieved, refused=refused)


def _report(outcomes: tuple[QuestionOutcome, ...], excerpts: tuple[tuple[str, str], ...] = ()):
    return score_run(
        outcomes,
        excerpts,
        retrieval_ms=(1.0, 2.0, 3.0, 4.0, 5.0),
        generation_ms=(1.0, 2.0, 3.0, 4.0, 5.0),
        input_tokens=3,
        output_tokens=1,
        embedding_model="fixed-embedder",
        embedding_version="1",
        language_model="citing-stand-in",
    )


def test_hit_and_recall_ignore_refusal_questions_and_stop_at_five() -> None:
    evidence = _item("evidence", relevant=("manual#Kept", "manual#Missed"))
    refused = _item("hidden", relevant=("manual#Secret",), expect_refusal=True)
    report = _report(
        (
            _outcome(evidence, ("manual#Other", "manual#Kept", "s#6", "s#7", "s#8", "manual#Missed"), refused=False),
            _outcome(refused, (), refused=True),
        )
    )

    assert report.evidence_questions == 1
    assert report.hit_at_5 == 1
    assert report.recall_at_5 == pytest.approx(0.5)
    assert report.correct_refusals == 1
    assert report.false_refusals == 0
    assert report.missed_refusals == 0


def test_false_and_missed_refusals_are_separate() -> None:
    report = _report(
        (
            _outcome(_item("has-evidence", relevant=("manual#Kept",)), (), refused=True),
            _outcome(_item("should-refuse", expect_refusal=True), ("manual#Other",), refused=False),
        )
    )

    assert report.hit_at_5 == 0
    assert report.false_refusals == 1
    assert report.missed_refusals == 1
    assert report.correct_refusals == 0
    assert report.evidence_questions == 1


def test_a_mismatched_excerpt_lowers_citation_validity() -> None:
    report = _report(
        (_outcome(_item("evidence", relevant=("manual#Kept",)), ("manual#Kept",), refused=False),),
        (("Open the period.", "Open the period."), ("wired", "Open the period.")),
    )

    assert report.citations == 2
    assert report.invalid_citations == 1
    assert report.citation_validity == pytest.approx(0.5)


def test_percentile_uses_nearest_rank() -> None:
    assert percentile((1, 2, 3, 4, 5), 95) == 5
    assert percentile(tuple(range(1, 101)), 95) == 95


def test_the_report_names_the_embedding_model() -> None:
    report = _report(())
    text = format_report(report)

    assert "embedding_model: fixed-embedder\n" in text
    assert "embedding_version: 1\n" in text
    assert "hit_at_5: n/a\n" in text
    assert "citation_validity: n/a\n" in text
    assert "retrieval_ms_p95: 5.000\n" in text

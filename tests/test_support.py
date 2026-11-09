"""A code in the draft has to appear in the cited excerpt. A refusal is outside the rate."""

from anchora.domain.scoring import EvalItem, QuestionOutcome, format_report, score_run
from anchora.domain.support import draft_is_supported


def test_the_pointer_draft_is_supported_and_a_foreign_code_is_not() -> None:
    excerpt = "Record JE-4419 before noon."

    assert draft_is_supported("See the cited passages.", (excerpt,))
    assert draft_is_supported("The entry is JE-4419.", (excerpt,))
    assert not draft_is_supported("Use SMP-30.", (excerpt,))
    assert not draft_is_supported("See the cited passages.", ())


def test_the_report_keeps_support_apart_from_refusals() -> None:
    delivered = EvalItem("shown", "operator", "Where is JE-4419?", ("manual#Record",), False)
    refused = EvalItem("hidden", "auditor", "JE-4419", ("manual#Record",), True)
    report = score_run(
        (
            QuestionOutcome(
                item=delivered,
                retrieved_sections=("manual#Record",),
                refused=False,
                supported=True,
            ),
            QuestionOutcome(
                item=refused,
                retrieved_sections=(),
                refused=True,
                supported=None,
            ),
        ),
        (),
        retrieval_ms=(1.0, 1.0),
        generation_ms=(1.0, 1.0),
        input_tokens=1,
        output_tokens=1,
        embedding_model="fixed-embedder",
        embedding_version="1",
        language_model="citing-stand-in",
    )

    text = format_report(report)

    assert report.supported_answers == 1
    assert "supported_answers: 1.000\n" in text
    assert report.correct_refusals == 1

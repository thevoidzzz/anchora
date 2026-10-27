"""Score a fixed question set. Hit and recall stay apart from refusals."""

import math
from collections.abc import Sequence
from dataclasses import dataclass

TOP_K = 5


@dataclass(frozen=True, slots=True)
class EvalItem:
    """One hand-written question. Relevant ids are document plus section path."""

    id: str
    role: str
    question: str
    relevant_sections: tuple[str, ...]
    expect_refusal: bool


@dataclass(frozen=True, slots=True)
class QuestionOutcome:
    """What retrieval and the answer contract did with one item."""

    item: EvalItem
    retrieved_sections: tuple[str, ...]
    refused: bool


@dataclass(frozen=True, slots=True)
class EvalReport:
    """The printed baseline. Rates are None when the denominator is empty."""

    embedding_model: str
    embedding_version: str
    language_model: str
    questions: int
    evidence_questions: int
    hit_at_5: float | None
    recall_at_5: float | None
    citation_validity: float | None
    citations: int
    invalid_citations: int
    correct_refusals: int
    false_refusals: int
    missed_refusals: int
    retrieval_ms_p95: float
    generation_ms_p95: float
    input_tokens: int
    output_tokens: int
    outcomes: tuple[QuestionOutcome, ...]


def section_id(document_id: str, section_path: str) -> str:
    """The id the golden set stores. The ordinal is not part of it."""

    return f"{document_id}#{section_path}"


def percentile(values: Sequence[float], percent: float) -> float:
    """Nearest-rank percentile. `percent` is in (0, 100]."""

    if not values:
        raise ValueError("percentile needs at least one value")
    if not 0 < percent <= 100:
        raise ValueError("percent must be in (0, 100]")
    ordered = sorted(values)
    rank = math.ceil(percent / 100 * len(ordered))
    return ordered[rank - 1]


def score_run(
    outcomes: Sequence[QuestionOutcome],
    excerpts: Sequence[tuple[str, str]],
    *,
    retrieval_ms: Sequence[float],
    generation_ms: Sequence[float],
    input_tokens: int,
    output_tokens: int,
    embedding_model: str,
    embedding_version: str,
    language_model: str,
) -> EvalReport:
    """Score retrieval on evidence questions and refusals on their own counts.

    `excerpts` are `(returned, stored)` pairs. A citation is valid when they match.
    Only the first five retrieved sections can count toward hit and recall.
    """

    evidence = [outcome for outcome in outcomes if not outcome.item.expect_refusal]
    if evidence:
        hits = sum(1 for outcome in evidence if _found(outcome))
        hit_at_5 = hits / len(evidence)
        relevant_total = sum(len(set(outcome.item.relevant_sections)) for outcome in evidence)
        found_total = sum(len(_found_sections(outcome)) for outcome in evidence)
        recall_at_5 = found_total / relevant_total
    else:
        hit_at_5 = None
        recall_at_5 = None
    invalid = sum(1 for returned, stored in excerpts if returned != stored)
    citations = len(excerpts)
    validity = None if citations == 0 else (citations - invalid) / citations
    return EvalReport(
        embedding_model=embedding_model,
        embedding_version=embedding_version,
        language_model=language_model,
        questions=len(outcomes),
        evidence_questions=len(evidence),
        hit_at_5=hit_at_5,
        recall_at_5=recall_at_5,
        citation_validity=validity,
        citations=citations,
        invalid_citations=invalid,
        correct_refusals=sum(1 for outcome in outcomes if outcome.item.expect_refusal and outcome.refused),
        false_refusals=sum(1 for outcome in outcomes if not outcome.item.expect_refusal and outcome.refused),
        missed_refusals=sum(1 for outcome in outcomes if outcome.item.expect_refusal and not outcome.refused),
        retrieval_ms_p95=percentile(retrieval_ms, 95),
        generation_ms_p95=percentile(generation_ms, 95),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        outcomes=tuple(outcomes),
    )


def format_report(report: EvalReport) -> str:
    """Stable lines. A rate with an empty denominator is `n/a`."""

    lines = (
        f"embedding_model: {report.embedding_model}",
        f"embedding_version: {report.embedding_version}",
        f"language_model: {report.language_model}",
        f"questions: {report.questions}",
        f"evidence_questions: {report.evidence_questions}",
        f"hit_at_5: {_rate(report.hit_at_5)}",
        f"recall_at_5: {_rate(report.recall_at_5)}",
        f"citation_validity: {_rate(report.citation_validity)}",
        f"citations: {report.citations}",
        f"correct_refusals: {report.correct_refusals}",
        f"false_refusals: {report.false_refusals}",
        f"missed_refusals: {report.missed_refusals}",
        f"retrieval_ms_p95: {report.retrieval_ms_p95:.3f}",
        f"generation_ms_p95: {report.generation_ms_p95:.3f}",
        f"input_tokens: {report.input_tokens}",
        f"output_tokens: {report.output_tokens}",
    )
    return "\n".join(lines) + "\n"


def _found(outcome: QuestionOutcome) -> bool:
    return bool(_found_sections(outcome))


def _found_sections(outcome: QuestionOutcome) -> set[str]:
    return set(outcome.retrieved_sections[:TOP_K]) & set(outcome.item.relevant_sections)


def _rate(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.3f}"

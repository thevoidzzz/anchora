"""Answer a question from retrieved passages, or refuse before calling the model."""

from collections.abc import Callable
from dataclasses import dataclass
from time import perf_counter
from typing import Literal

from anchora.application.ports import DocumentCatalog, Embedder, LanguageModel
from anchora.application.search import retrieve
from anchora.domain.citation import Citation, assemble_answer
from anchora.domain.errors import RequestError
from anchora.domain.limits import QUESTION_MAX_CHARS


@dataclass(frozen=True, slots=True)
class Answer:
    """A grounded answer, or a refusal that does not carry a draft."""

    refused: bool
    answer: str | None
    reason: Literal["no_evidence", "no_valid_citation"] | None
    citations: tuple[Citation, ...]
    model: str | None
    input_tokens: int
    output_tokens: int
    retrieval_ms: float
    generation_ms: float


def answer_question(
    question: str,
    role: str,
    catalog: DocumentCatalog,
    embedder: Embedder,
    model: LanguageModel,
    *,
    clock: Callable[[], float] = perf_counter,
) -> Answer:
    """Retrieve for this role, then ask the model. No rows means no model call."""

    if question.strip() == "":
        raise RequestError("question must not be empty")
    if len(question) > QUESTION_MAX_CHARS:
        raise RequestError(f"question must be at most {QUESTION_MAX_CHARS} characters")
    started = clock()
    passages = retrieve(question, role, catalog, embedder)
    retrieval_ms = (clock() - started) * 1000
    if not passages:
        return Answer(
            refused=True,
            answer=None,
            reason="no_evidence",
            citations=(),
            model=None,
            input_tokens=0,
            output_tokens=0,
            retrieval_ms=retrieval_ms,
            generation_ms=0.0,
        )
    started = clock()
    completion = model.complete(question, passages)
    generation_ms = (clock() - started) * 1000
    assembled = assemble_answer(completion.draft, completion.chunk_ids, passages)
    return Answer(
        refused=assembled.refused,
        answer=assembled.answer,
        reason=assembled.reason,
        citations=assembled.citations,
        model=completion.model,
        input_tokens=completion.input_tokens,
        output_tokens=completion.output_tokens,
        retrieval_ms=retrieval_ms,
        generation_ms=generation_ms,
    )

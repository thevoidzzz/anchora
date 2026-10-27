"""Run the bundled manuals and the golden set. This module does not open a driver."""

from collections.abc import Sequence

from anchora.application.answer import answer_question
from anchora.application.ingest import ingest_manual
from anchora.application.ports import DocumentCatalog, Embedder, LanguageModel
from anchora.application.search import retrieve
from anchora.domain.errors import EvalError
from anchora.domain.scoring import EvalItem, EvalReport, QuestionOutcome, score_run, section_id

_ROLES = frozenset({"operator", "auditor"})


def evaluate(
    catalog: DocumentCatalog,
    embedder: Embedder,
    model: LanguageModel,
    manuals: Sequence[str],
    items: Sequence[EvalItem],
) -> EvalReport:
    """Replace the catalog with these manuals, then score every item.

    A relevant section that is not in the manuals is an error. Hit@5 does not
    invent a passing bar. Citation validity below 1 is reported, and the caller
    decides whether that fails the process.
    """

    if not items:
        raise EvalError("the evaluation set is empty")
    _reject_duplicate_ids(items)
    catalog.clear()
    known: set[str] = set()
    for manual in manuals:
        for chunk in ingest_manual(manual, catalog, embedder):
            known.add(section_id(chunk.document_id, chunk.section_path))
    missing = [
        f"{item.id}: {section}"
        for item in items
        for section in item.relevant_sections
        if section not in known
    ]
    if missing:
        raise EvalError("relevant section is not in the corpus: " + ", ".join(missing))
    identity = embedder.identity()
    outcomes: list[QuestionOutcome] = []
    excerpts: list[tuple[str, str]] = []
    retrieval_ms: list[float] = []
    generation_ms: list[float] = []
    input_tokens = 0
    output_tokens = 0
    language_model = "-"
    for item in items:
        passages = retrieve(item.question, item.role, catalog, embedder)
        answer = answer_question(item.question, item.role, catalog, embedder, model)
        outcomes.append(
            QuestionOutcome(
                item=item,
                retrieved_sections=tuple(section_id(passage.document_id, passage.section_path) for passage in passages),
                refused=answer.refused,
            )
        )
        for citation in answer.citations:
            stored = catalog.get(citation.chunk_id)
            stored_text = "" if stored is None else stored.text
            excerpts.append((citation.excerpt, stored_text))
        retrieval_ms.append(answer.retrieval_ms)
        generation_ms.append(answer.generation_ms)
        input_tokens += answer.input_tokens
        output_tokens += answer.output_tokens
        if answer.model is not None:
            language_model = answer.model
    return score_run(
        outcomes,
        excerpts,
        retrieval_ms=retrieval_ms,
        generation_ms=generation_ms,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        embedding_model=identity.name,
        embedding_version=identity.version,
        language_model=language_model,
    )


def _reject_duplicate_ids(items: Sequence[EvalItem]) -> None:
    seen: set[str] = set()
    for item in items:
        if item.role not in _ROLES:
            raise EvalError(f"role must be operator or auditor: {item.id}")
        if item.question.strip() == "":
            raise EvalError(f"question must not be empty: {item.id}")
        if not item.expect_refusal and not item.relevant_sections:
            raise EvalError(f"an evidence question needs a relevant section: {item.id}")
        if len(item.relevant_sections) != len(set(item.relevant_sections)):
            raise EvalError(f"relevant sections repeat: {item.id}")
        if item.id in seen:
            raise EvalError(f"duplicate question id: {item.id}")
        seen.add(item.id)

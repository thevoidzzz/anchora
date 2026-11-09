"""Shared tokens move a passage ahead. A tie keeps the fusion order."""

from anchora.domain.manual import Chunk
from anchora.domain.rerank import rerank_passages
from anchora.domain.scoring import EvalItem, QuestionOutcome, format_report, score_run


def _chunk(chunk_id: str, text: str) -> Chunk:
    return Chunk(
        chunk_id=chunk_id,
        document_id="manual",
        document_title="Manual",
        audience="operator",
        section_path="Section",
        ordinal=0,
        page=1,
        text=text,
    )


def test_shared_tokens_move_the_passage_ahead_of_the_fusion_leader() -> None:
    leader = _chunk("a", "The night desk books the close.")
    match = _chunk("b", "Record JE-4419 before noon.")

    ordered = rerank_passages("Where is JE-4419?", (leader, match))

    assert [chunk.chunk_id for chunk in ordered] == ["b", "a"]


def test_equal_overlap_keeps_the_fusion_order() -> None:
    first = _chunk("a", "Record the JE-4419 entry.")
    second = _chunk("b", "JE-4419 is the entry.")

    ordered = rerank_passages("JE-4419", (first, second))

    assert [chunk.chunk_id for chunk in ordered] == ["a", "b"]


def test_the_report_prints_the_fusion_and_the_rerank_apart() -> None:
    item = EvalItem(
        id="moved",
        role="operator",
        question="Where is JE-4419?",
        relevant_sections=("manual#Record",),
        expect_refusal=False,
    )
    outcome = QuestionOutcome(
        item=item,
        retrieved_sections=("manual#Other",),
        refused=False,
        reranked_sections=("manual#Record",),
    )
    report = score_run(
        (outcome,),
        (),
        retrieval_ms=(1.0,),
        generation_ms=(1.0,),
        input_tokens=1,
        output_tokens=1,
        embedding_model="fixed-embedder",
        embedding_version="1",
        language_model="citing-stand-in",
    )

    text = format_report(report)

    assert "hit_at_5: 0.000\n" in text
    assert "rerank_hit_at_5: 1.000\n" in text
    assert "rerank_recall_at_5: 1.000\n" in text

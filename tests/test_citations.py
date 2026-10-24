"""A citation is copied from a retrieved chunk, or the draft is dropped."""

import pytest

from anchora.domain import Chunk, Citation, DuplicateRetrievedChunkError, assemble_answer


def _chunk(chunk_id: str, text: str, *, section: str = "Tie-out", page: int = 4) -> Chunk:
    return Chunk(
        chunk_id=chunk_id,
        document_id="month-end-close",
        document_title="Month-end close",
        audience="operator",
        section_path=section,
        ordinal=0,
        page=page,
        text=text,
    )


def test_an_id_outside_the_retrieved_set_is_dropped_and_the_excerpt_is_the_chunk() -> None:
    kept = _chunk("month-end-close#Open#0", "Open the period.", section="Open", page=1)
    draft = "The manual says: please wire the funds today."
    result = assemble_answer(draft, ["other-manual#Secret#0", kept.chunk_id, kept.chunk_id], [kept])

    assert result.refused is False
    assert result.reason is None
    assert result.answer == draft
    assert result.citations == (
        Citation(
            chunk_id="month-end-close#Open#0",
            document="Month-end close",
            section="Open",
            page=1,
            excerpt="Open the period.",
        ),
    )


def test_only_foreign_ids_refuse_and_drop_the_draft() -> None:
    kept = _chunk("month-end-close#Open#0", "Open the period.")
    result = assemble_answer("please wire the funds today.", ["other-manual#Secret#0"], [kept])

    assert result.refused is True
    assert result.reason == "no_valid_citation"
    assert result.answer is None
    assert result.citations == ()


def test_no_chosen_id_refuses_even_when_retrieval_returned_a_chunk() -> None:
    chunk = _chunk("month-end-close#Open#0", "Open the period.")
    result = assemble_answer("A plausible sentence.", [], [chunk])

    assert result.refused is True
    assert result.reason == "no_valid_citation"
    assert result.answer is None
    assert result.citations == ()


def test_citation_order_follows_the_model() -> None:
    opening = _chunk("month-end-close#Open#0", "Open the period.", section="Open", page=1)
    closing = _chunk("month-end-close#Close#0", "Close the period.", section="Close", page=2)
    result = assemble_answer("Both steps.", [closing.chunk_id, opening.chunk_id], [opening, closing])

    assert [citation.chunk_id for citation in result.citations] == [
        "month-end-close#Close#0",
        "month-end-close#Open#0",
    ]
    assert result.citations[0].excerpt == "Close the period."
    assert result.citations[0].page == 2
    assert result.citations[1].section == "Open"


def test_an_empty_draft_with_a_retrieved_id_is_still_answered() -> None:
    chunk = _chunk("month-end-close#Open#0", "Open the period.")
    result = assemble_answer("", [chunk.chunk_id], [chunk])

    assert result.refused is False
    assert result.answer == ""
    assert result.citations[0].excerpt == "Open the period."


def test_the_excerpt_is_the_whole_window() -> None:
    window = "abcdefghij"
    chunk = _chunk("month-end-close#Alphabet#0", window, section="Alphabet", page=8)
    result = assemble_answer("The letters start with ab.", [chunk.chunk_id], [chunk])

    assert result.citations[0].excerpt == window


def test_a_duplicate_retrieved_id_is_an_error() -> None:
    chunk = _chunk("month-end-close#Open#0", "Open the period.")

    with pytest.raises(DuplicateRetrievedChunkError, match="month-end-close#Open#0"):
        assemble_answer("Open.", [chunk.chunk_id], [chunk, chunk])

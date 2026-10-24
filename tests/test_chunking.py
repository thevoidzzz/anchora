"""A section keeps its id when the file is parsed again."""

import pytest

from anchora.domain import (
    DEFAULT_MAX_CHARS,
    DEFAULT_OVERLAP_CHARS,
    ChunkConfig,
    ChunkConfigError,
    ManualError,
    parse_manual,
)

_WINDOW = ChunkConfig(max_chars=100, overlap_chars=0)


def _manual(body: str, **fields: str) -> str:
    meta = {
        "id": "month-end-close",
        "title": "Month-end close",
        "audience": "operator",
        **fields,
    }
    front = "\n".join(f"{key}: {meta[key]}" for key in ("id", "title", "audience"))
    return f"---\n{front}\n---\n\n{body}"


def _section(heading: str, page: int, text: str, level: str = "##") -> str:
    return f"{level} {heading}\npage: {page}\n\n{text}\n"


def test_section_under_the_cap_keeps_a_stable_id() -> None:
    text = _manual(_section("Tie-out the trial balance", 4, "The operator compares the ledger to the subledger."))
    chunk = parse_manual(text, _WINDOW)[0]

    assert chunk.chunk_id == "month-end-close#Tie-out the trial balance#0"
    assert chunk.document_id == "month-end-close"
    assert chunk.document_title == "Month-end close"
    assert chunk.audience == "operator"
    assert chunk.section_path == "Tie-out the trial balance"
    assert chunk.ordinal == 0
    assert chunk.page == 4
    assert chunk.text == "The operator compares the ledger to the subledger."
    assert parse_manual(text, _WINDOW) == parse_manual(text, _WINDOW)


def test_editing_the_text_keeps_the_id_and_renaming_the_heading_changes_it() -> None:
    original_text = _manual(_section("Tie-out the trial balance", 4, "The operator compares the ledger."))
    original = parse_manual(original_text, _WINDOW)[0]
    edited = parse_manual(original_text.replace("ledger", "journal"), _WINDOW)[0]
    renamed = parse_manual(original_text.replace("Tie-out the trial balance", "Tie the trial balance"), _WINDOW)[0]

    assert edited.chunk_id == original.chunk_id
    assert edited.text != original.text
    assert renamed.chunk_id == "month-end-close#Tie the trial balance#0"
    assert renamed.chunk_id != original.chunk_id


def test_heading_whitespace_collapses_and_case_stays() -> None:
    text = _manual(_section("  Tie-out   the   Señorío  ", 2, "A named account stays in the path."))
    chunk = parse_manual(text, _WINDOW)[0]

    assert chunk.section_path == "Tie-out the Señorío"
    assert chunk.chunk_id == "month-end-close#Tie-out the Señorío#0"


@pytest.mark.parametrize("audience", ["operator", "auditor", "both"])
def test_audience_comes_from_the_file(audience: str) -> None:
    text = _manual(_section("Limits", 1, "The limit is stated here."), audience=audience)
    assert parse_manual(text, _WINDOW)[0].audience == audience


def test_nested_heading_uses_the_parent_path_and_its_own_page() -> None:
    body = (
        _section("Tie-out the trial balance", 4, "Compare the ledger to the subledger.")
        + "\n"
        + _section("Exceptions", 5, "An exception above the limit goes to the controller.", level="###")
    )
    chunks = parse_manual(_manual(body), _WINDOW)

    assert [(chunk.section_path, chunk.page, chunk.ordinal) for chunk in chunks] == [
        ("Tie-out the trial balance", 4, 0),
        ("Tie-out the trial balance / Exceptions", 5, 0),
    ]


def test_each_section_starts_its_ordinal_at_zero() -> None:
    body = _section("Open", 1, "Open the period.") + "\n" + _section("Close", 2, "Close the period.")
    chunks = parse_manual(_manual(body), _WINDOW)

    assert [chunk.ordinal for chunk in chunks] == [0, 0]
    assert chunks[0].chunk_id == "month-end-close#Open#0"
    assert chunks[1].chunk_id == "month-end-close#Close#0"


def test_long_section_splits_on_a_fixed_window_and_shares_the_section() -> None:
    body_text = "abcdefghijklmnopqrstuvwxyz"
    config = ChunkConfig(max_chars=10, overlap_chars=3)
    chunks = parse_manual(_manual(_section("Alphabet", 8, body_text)), config)

    assert [chunk.text for chunk in chunks] == [
        "abcdefghij",
        "hijklmnopq",
        "opqrstuvwx",
        "vwxyz",
    ]
    assert [chunk.ordinal for chunk in chunks] == [0, 1, 2, 3]
    assert {chunk.section_path for chunk in chunks} == {"Alphabet"}
    assert {chunk.page for chunk in chunks} == {8}
    assert chunks[1].text.startswith(chunks[0].text[-config.overlap_chars :])
    assert chunks[-1].text.endswith(body_text[-1])


def test_overlap_zero_joins_back_to_the_section() -> None:
    body_text = "abcdefghij"
    chunks = parse_manual(_manual(_section("Alphabet", 1, body_text)), ChunkConfig(4, 0))

    assert "".join(chunk.text for chunk in chunks) == body_text
    assert [chunk.chunk_id for chunk in chunks] == [
        "month-end-close#Alphabet#0",
        "month-end-close#Alphabet#1",
        "month-end-close#Alphabet#2",
    ]


def test_a_smaller_window_keeps_the_first_id() -> None:
    body_text = "abcdefghijklmnopqrstuvwxyz"
    text = _manual(_section("Alphabet", 1, body_text))
    wide = parse_manual(text, ChunkConfig(100, 0))
    narrow = parse_manual(text, ChunkConfig(10, 0))

    assert len(wide) == 1
    assert len(narrow) > 1
    assert narrow[0].chunk_id == wide[0].chunk_id


def test_a_section_exactly_at_the_cap_is_one_chunk() -> None:
    chunks = parse_manual(_manual(_section("Exact", 1, "abcd")), ChunkConfig(4, 1))

    assert len(chunks) == 1
    assert chunks[0].text == "abcd"
    assert chunks[0].ordinal == 0


def test_default_window_is_the_initial_value() -> None:
    config = ChunkConfig(DEFAULT_MAX_CHARS, DEFAULT_OVERLAP_CHARS)

    assert config.max_chars == 1500
    assert config.overlap_chars == 200


@pytest.mark.parametrize(
    ("max_chars", "overlap_chars"),
    [(0, 0), (4, 4), (4, 5), (8, -1)],
)
def test_window_rejects_an_overlap_that_is_not_inside_the_cap(max_chars: int, overlap_chars: int) -> None:
    with pytest.raises(ChunkConfigError):
        ChunkConfig(max_chars, overlap_chars)


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("no frontmatter\n", "frontmatter"),
        ("---\nid: month-end-close\n", "not closed"),
        (
            "---\nid: month-end-close\ntitle: Month-end close\naudience: operator\nowner: ada\n---\n\n## Limits\npage: 1\n\nText.\n",
            "unknown frontmatter field",
        ),
        (
            "---\nid: Month_End\ntitle: Month-end close\naudience: operator\n---\n\n## Limits\npage: 1\n\nText.\n",
            "lowercase slug",
        ),
        (
            "---\nid: month-end-close\ntitle: Month-end close\naudience: guest\n---\n\n## Limits\npage: 1\n\nText.\n",
            "audience",
        ),
        (
            "---\nid: month-end-close\ntitle: Month-end close\naudience: operator\n---\n\nA line before the heading.\n\n## Limits\npage: 1\n\nText.\n",
            "text before the first section",
        ),
        (
            "---\nid: month-end-close\ntitle: Month-end close\naudience: operator\n---\n\n# Limits\npage: 1\n\nText.\n",
            "only ## and ###",
        ),
        (
            "---\nid: month-end-close\ntitle: Month-end close\naudience: operator\n---\n\n### Limits\npage: 1\n\nText.\n",
            "parent section",
        ),
        (
            "---\nid: month-end-close\ntitle: Month-end close\naudience: operator\n---\n\n## Limits\n\nText without a page.\n",
            "needs a page",
        ),
        (
            "---\nid: month-end-close\ntitle: Month-end close\naudience: operator\n---\n\n## Limits\npage: 1\n\n",
            "has no text",
        ),
        (
            "---\nid: month-end-close\ntitle: Month-end close\naudience: operator\n---\n\n## Limits\npage: 1\n\nOnce.\n\n## Limits\npage: 2\n\nTwice.\n",
            "duplicate section path",
        ),
        (
            "---\nid: month-end-close\ntitle: Month-end close\naudience: operator\n---\n\n## Size # 10\npage: 1\n\nText.\n",
            "cannot contain #",
        ),
    ],
)
def test_rejects_a_manual_that_breaks_the_grammar(text: str, message: str) -> None:
    with pytest.raises(ManualError, match=message):
        parse_manual(text, _WINDOW)

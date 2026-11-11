"""A Spanish manual is scored apart from the English baseline."""

import pytest

from anchora.domain.errors import ManualError
from anchora.domain.manual import parse_manual
from anchora.eval.load import load_manuals
from anchora.eval.spanish import compare, manual_text
from anchora.infrastructure.postgres import PostgresCatalog

_MANUAL = """---
id: lote
title: Lote
audience: operator
---

## Cierre
page: 1

La mesa contabiliza el lote.
"""


def test_a_manual_without_lexicon_stays_english() -> None:
    chunk = parse_manual(_MANUAL)[0]
    assert chunk.lexicon == "english"


def test_spanish_is_the_only_other_lexicon() -> None:
    spanish = _MANUAL.replace("audience: operator\n", "audience: operator\nlexicon: spanish\n")
    assert parse_manual(spanish)[0].lexicon == "spanish"
    assert parse_manual(spanish)[0].chunk_id == parse_manual(_MANUAL)[0].chunk_id
    german = _MANUAL.replace("audience: operator\n", "audience: operator\nlexicon: german\n")
    with pytest.raises(ManualError, match="english or spanish"):
        parse_manual(german)


def test_the_english_baseline_does_not_load_the_spanish_manual() -> None:
    manuals = load_manuals()
    assert manuals
    assert all("id: lote\n" not in manual for manual in manuals)
    assert "lexicon: spanish" in manual_text()


@pytest.fixture
def catalog(database_url: str) -> PostgresCatalog:
    store = PostgresCatalog(database_url)
    store.ensure_schema()
    store.clear()
    return store


def test_the_spanish_dictionary_is_what_moves_hit_at_5(catalog: PostgresCatalog) -> None:
    report = compare(catalog)
    assert report == (
        "manual: lote\n"
        "questions: 1\n"
        "english_hit_at_5: 0.000\n"
        "english_recall_at_5: 0.000\n"
        "spanish_hit_at_5: 1.000\n"
        "spanish_recall_at_5: 1.000\n"
    )

"""Loading the bundled manuals cites the operator passage and hides it from the auditor."""

import pytest

from anchora.application.answer import answer_question
from anchora.infrastructure.citing_model import CitingModel
from anchora.infrastructure.fixed_embedder import FixedEmbedder
from anchora.infrastructure.postgres import PostgresCatalog
from anchora.sample import main


@pytest.fixture
def catalog(database_url: str) -> PostgresCatalog:
    store = PostgresCatalog(database_url)
    store.ensure_schema()
    store.clear()
    return store


def test_the_empty_catalog_still_refuses_and_the_samples_split_the_roles(
    catalog: PostgresCatalog,
    monkeypatch: pytest.MonkeyPatch,
    database_url: str,
) -> None:
    embedder = FixedEmbedder()
    model = CitingModel()
    empty = answer_question("Meridian", "operator", catalog, embedder, model)

    monkeypatch.setenv("DATABASE_URL", database_url)
    main()
    shown = answer_question("JE-4419", "operator", catalog, embedder, model)
    hidden = answer_question("JE-4419", "auditor", catalog, embedder, model)

    assert empty.refused
    assert empty.reason == "no_evidence"
    assert any(citation.section == "Book accruals" for citation in shown.citations)
    assert all(citation.section != "Book accruals" for citation in hidden.citations)
    assert all(citation.document != "Month-end close" for citation in hidden.citations)

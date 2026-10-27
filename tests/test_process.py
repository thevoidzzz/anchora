"""The process serves an empty catalog with the stand-in models and no paid key."""

import pytest
from fastapi.testclient import TestClient

from anchora.api.__main__ import app_from_env
from anchora.infrastructure.postgres import PostgresCatalog


def test_an_empty_catalog_refuses_meridian_without_a_paid_key(
    database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("DATABASE_URL", database_url)
    store = PostgresCatalog(database_url)
    store.ensure_schema()
    store.clear()

    response = TestClient(app_from_env()).post(
        "/v1/answers",
        json={"question": "Meridian", "role": "operator"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["refused"] is True
    assert body["reason"] == "no_evidence"
    assert body["citations"] == []

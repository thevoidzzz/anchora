"""POST /v1/answers. Refusals are 200. Transport and provider failures are problem+json."""

import logging
from collections.abc import Sequence

import pytest
from fastapi.testclient import TestClient

from anchora.api import create_app
from anchora.application import ingest_manual
from anchora.domain import QUESTION_MAX_CHARS, Chunk, ModelCompletion, ModelSchemaError, ModelTimeout
from anchora.infrastructure.fixed_embedder import FixedEmbedder
from anchora.infrastructure.postgres import PostgresCatalog

_SECRET = "sk-anchora-test-key"


class ScriptedModel:
    def __init__(self, draft: str, chunk_ids: Sequence[str]) -> None:
        self.calls = 0
        self.api_key = _SECRET
        self._draft = draft
        self._chunk_ids = tuple(chunk_ids)

    def complete(self, question: str, passages: Sequence[Chunk]) -> ModelCompletion:
        self.calls += 1
        return ModelCompletion(self._draft, self._chunk_ids, "scripted-model", 11, 5)


class _Holding:
    def __init__(self, chunk: Chunk) -> None:
        self._chunk = chunk

    def search(self, term: str, role: str) -> tuple[Chunk, ...]:
        return (self._chunk,)

    def nearest(self, vector: Sequence[float], role: str, identity: object) -> tuple[Chunk, ...]:
        return (self._chunk,)


def _passage() -> Chunk:
    return Chunk(
        chunk_id="month-end-close#Book the batch#0",
        document_id="month-end-close",
        document_title="Month-end close",
        audience="operator",
        section_path="Book the batch",
        ordinal=0,
        page=4,
        text="The desk books the close before noon.",
    )


def _manual(document_id: str, title: str, audience: str, body: str) -> str:
    return f"---\nid: {document_id}\ntitle: {title}\naudience: {audience}\n---\n\n{body}"


def _section(heading: str, page: int, text: str) -> str:
    return f"## {heading}\npage: {page}\n\n{text}\n"


@pytest.fixture
def catalog(database_url: str) -> PostgresCatalog:
    store = PostgresCatalog(database_url)
    store.ensure_schema()
    store.clear()
    return store


def test_a_grounded_answer_is_200_and_the_log_omits_the_key(catalog: PostgresCatalog, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger="anchora.api")
    text = "The desk books the close before noon."
    embedder = FixedEmbedder()
    stored = ingest_manual(
        _manual("month-end-close", "Month-end close", "operator", _section("Book the batch", 4, text)),
        catalog,
        embedder,
    )
    model = ScriptedModel("Book the close before noon.", (stored[0].chunk_id,))
    client = TestClient(create_app(catalog, embedder, model))

    response = client.post(
        "/v1/answers",
        json={"question": "Where is the close booked?", "role": "operator"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["request_id"] == response.headers["X-Request-ID"]
    assert body["refused"] is False
    assert body["reason"] is None
    assert body["answer"] == "Book the close before noon."
    assert body["citations"] == [
        {
            "chunk_id": stored[0].chunk_id,
            "document": "Month-end close",
            "section": "Book the batch",
            "page": 4,
            "excerpt": text,
        }
    ]
    assert "role=operator" in caplog.text
    assert "model=scripted-model" in caplog.text
    assert "input_tokens=11" in caplog.text
    assert "output_tokens=5" in caplog.text
    assert "refused=false" in caplog.text
    assert f"chunk_ids={stored[0].chunk_id}" in caplog.text
    assert "question=Where is the close booked?" in caplog.text
    assert "retrieval_ms=" in caplog.text
    assert "generation_ms=" in caplog.text
    assert _SECRET not in caplog.text
    assert _SECRET not in response.text


def test_no_evidence_is_200_and_does_not_call_the_model(catalog: PostgresCatalog, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger="anchora.api")
    embedder = FixedEmbedder()
    ingest_manual(
        _manual(
            "approval-limits",
            "Approval limits",
            "auditor",
            _section("Sample", 2, "Meridian is the sample code."),
        ),
        catalog,
        embedder,
    )
    model = ScriptedModel("unused", ())
    client = TestClient(create_app(catalog, embedder, model))

    response = client.post("/v1/answers", json={"question": "Meridian", "role": "operator"})

    assert response.status_code == 200
    body = response.json()
    assert body["refused"] is True
    assert body["reason"] == "no_evidence"
    assert body["answer"] is None
    assert body["citations"] == []
    assert model.calls == 0
    assert "refused=true" in caplog.text
    assert "model=-" in caplog.text
    assert "question=Meridian" in caplog.text
    assert _SECRET not in caplog.text


def test_a_foreign_id_is_a_refusal() -> None:
    passage = _passage()
    model = ScriptedModel("Use the sample code.", ("approval-limits#Sample#0",))
    client = TestClient(create_app(_Holding(passage), FixedEmbedder(), model))

    response = client.post("/v1/answers", json={"question": "Where is the close booked?", "role": "operator"})

    assert response.status_code == 200
    body = response.json()
    assert body["refused"] is True
    assert body["reason"] == "no_valid_citation"
    assert body["answer"] is None
    assert body["citations"] == []
    assert model.calls == 1


def test_invalid_input_is_400() -> None:
    client = TestClient(create_app(_Holding(_passage()), FixedEmbedder(), ScriptedModel("unused", ())))

    empty = client.post("/v1/answers", json={"question": "  ", "role": "operator"})
    unknown = client.post("/v1/answers", json={"question": "Where is the close?", "role": "both"})
    missing = client.post("/v1/answers", json={})
    garbled = client.post(
        "/v1/answers",
        content=b"not-json",
        headers={"content-type": "application/json"},
    )
    oversized = client.post(
        "/v1/answers",
        json={"question": "m" * (QUESTION_MAX_CHARS + 1), "role": "operator"},
    )

    assert empty.status_code == 400
    assert empty.json()["detail"] == "question must not be empty"
    assert unknown.status_code == 400
    assert unknown.json()["detail"] == "role must be operator or auditor"
    assert missing.status_code == 400
    assert missing.json()["detail"] == "question and role are required"
    assert garbled.status_code == 400
    assert garbled.json()["detail"] == "request body must be json"
    assert oversized.status_code == 400
    assert str(QUESTION_MAX_CHARS) in oversized.json()["detail"]
    for response in (empty, unknown, missing, garbled, oversized):
        assert response.headers["content-type"].startswith("application/problem+json")
        assert response.json()["status"] == 400
        assert response.json()["request_id"] == response.headers["X-Request-ID"]


def test_a_timeout_is_504_and_is_not_retried() -> None:
    class _Slow:
        def __init__(self) -> None:
            self.calls = 0

        def complete(self, question: str, passages: Sequence[Chunk]) -> ModelCompletion:
            self.calls += 1
            raise ModelTimeout("slow")

    model = _Slow()
    client = TestClient(create_app(_Holding(_passage()), FixedEmbedder(), model))
    response = client.post("/v1/answers", json={"question": "Where is the close?", "role": "operator"})

    assert response.status_code == 504
    assert response.json()["detail"] == "the model did not respond in time"
    assert response.headers["content-type"].startswith("application/problem+json")
    assert model.calls == 1


def test_a_schema_mismatch_is_retried_once_and_then_502() -> None:
    passage = _passage()

    class _Once:
        def __init__(self) -> None:
            self.calls = 0

        def complete(self, question: str, passages: Sequence[Chunk]) -> ModelCompletion:
            self.calls += 1
            if self.calls == 1:
                raise ModelSchemaError("missing chunk_ids")
            return ModelCompletion("Book the close.", (passage.chunk_id,), "scripted-model", 4, 2)

    recovered = _Once()
    client = TestClient(create_app(_Holding(passage), FixedEmbedder(), recovered))
    ok = client.post("/v1/answers", json={"question": "Where is the close?", "role": "operator"})
    assert ok.status_code == 200
    assert ok.json()["answer"] == "Book the close."
    assert recovered.calls == 2

    class _Twice:
        def __init__(self) -> None:
            self.calls = 0

        def complete(self, question: str, passages: Sequence[Chunk]) -> ModelCompletion:
            self.calls += 1
            raise ModelSchemaError("missing chunk_ids")

    failed = _Twice()
    client = TestClient(create_app(_Holding(passage), FixedEmbedder(), failed))
    response = client.post("/v1/answers", json={"question": "Where is the close?", "role": "operator"})
    assert response.status_code == 502
    assert response.json()["detail"] == "the model response did not match the schema"
    assert response.headers["content-type"].startswith("application/problem+json")
    assert failed.calls == 2


def test_a_down_database_is_503_and_hides_the_connection_string() -> None:
    catalog = PostgresCatalog("postgresql://anchora@127.0.0.1:1/anchora?connect_timeout=1")
    client = TestClient(create_app(catalog, FixedEmbedder(), ScriptedModel("unused", ())))

    response = client.post("/v1/answers", json={"question": "Meridian", "role": "operator"})

    assert response.status_code == 503
    assert response.json()["detail"] == "the catalog is unavailable"
    assert response.headers["content-type"].startswith("application/problem+json")
    assert "127.0.0.1" not in response.text
    assert "connect_timeout" not in response.text

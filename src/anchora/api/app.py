"""HTTP contract. Handlers call use cases and do not write SQL."""

import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from anchora.application.answer import Answer, answer_question
from anchora.application.ports import DocumentCatalog, Embedder, LanguageModel
from anchora.domain.errors import CatalogUnavailable, ModelSchemaError, ModelTimeout, RequestError, SearchError

logger = logging.getLogger("anchora.api")


class AnswerBody(BaseModel):
    """Question and role. Length and role checks live in the use case."""

    question: str
    role: str


def create_app(catalog: DocumentCatalog, embedder: Embedder, model: LanguageModel) -> FastAPI:
    """Build the API around an already constructed catalog, embedder, and model."""

    app = FastAPI()

    @app.middleware("http")
    async def attach_request_id(request: Request, call_next):
        request.state.request_id = str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid_body(request: Request, exc: RequestValidationError) -> JSONResponse:
        return _problem(request, 400, "Bad Request", _validation_detail(exc))

    @app.exception_handler(RequestError)
    async def rejected_question(request: Request, exc: RequestError) -> JSONResponse:
        return _problem(request, 400, "Bad Request", str(exc))

    @app.exception_handler(SearchError)
    async def rejected_role(request: Request, exc: SearchError) -> JSONResponse:
        return _problem(request, 400, "Bad Request", str(exc))

    @app.exception_handler(ModelTimeout)
    async def timed_out(request: Request, exc: ModelTimeout) -> JSONResponse:
        return _problem(request, 504, "Gateway Timeout", "the model did not respond in time")

    @app.exception_handler(ModelSchemaError)
    async def invalid_model(request: Request, exc: ModelSchemaError) -> JSONResponse:
        return _problem(request, 502, "Bad Gateway", "the model response did not match the schema")

    @app.exception_handler(CatalogUnavailable)
    async def catalog_down(request: Request, exc: CatalogUnavailable) -> JSONResponse:
        return _problem(request, 503, "Service Unavailable", "the catalog is unavailable")

    @app.post("/v1/answers")
    def answers(body: AnswerBody, request: Request) -> dict[str, object]:
        result = answer_question(body.question, body.role, catalog, embedder, model)
        _log_answer(request, body.role, body.question, result)
        return _payload(request, result)

    return app


def _payload(request: Request, result: Answer) -> dict[str, object]:
    return {
        "request_id": request.state.request_id,
        "refused": result.refused,
        "answer": result.answer,
        "reason": result.reason,
        "citations": [
            {
                "chunk_id": citation.chunk_id,
                "document": citation.document,
                "section": citation.section,
                "page": citation.page,
                "excerpt": citation.excerpt,
            }
            for citation in result.citations
        ],
    }


def _log_answer(request: Request, role: str, question: str, result: Answer) -> None:
    chunk_ids = ",".join(citation.chunk_id for citation in result.citations)
    model_name = result.model if result.model is not None else "-"
    logger.info(
        "request_id=%s role=%s retrieval_ms=%.3f generation_ms=%.3f model=%s input_tokens=%s output_tokens=%s refused=%s chunk_ids=%s question=%s",
        request.state.request_id,
        role,
        result.retrieval_ms,
        result.generation_ms,
        model_name,
        result.input_tokens,
        result.output_tokens,
        str(result.refused).lower(),
        chunk_ids,
        question,
    )


def _problem(request: Request, status: int, title: str, detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        media_type="application/problem+json",
        content={
            "type": "about:blank",
            "title": title,
            "status": status,
            "detail": detail,
            "request_id": request.state.request_id,
        },
    )


def _validation_detail(exc: RequestValidationError) -> str:
    errors = exc.errors()
    if any(error.get("type") == "json_invalid" for error in errors):
        return "request body must be json"
    missing = [error.get("loc", ()) for error in errors if error.get("type") == "missing"]
    fields = {part for loc in missing for part in loc if isinstance(part, str)}
    if "question" in fields and "role" in fields:
        return "question and role are required"
    if "question" in fields:
        return "question is required"
    if "role" in fields:
        return "role is required"
    return "request body is invalid"

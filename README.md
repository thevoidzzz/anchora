# Anchora

[![tests](https://github.com/thevoidzzz/anchora/actions/workflows/tests.yml/badge.svg)](https://github.com/thevoidzzz/anchora/actions/workflows/tests.yml)

Grounded assistant for internal operating manuals. A citation is copied from the retrieved passage, or the answer is refused.

`POST /v1/answers` takes a question and a role (`operator` or `auditor`). A refusal is HTTP 200. Invalid input, a model that times out or returns the wrong shape, and a database that is down use `application/problem+json`.

## Evaluation

`python -m anchora.eval` loads the bundled manuals and the 50 hand-written questions, then prints hit@5 and recall@5 apart from refusals. It also prints those two rates after reordering the five fused passages by tokens shared with the question, and `supported_answers` for delivered drafts. The answer still uses the fusion order. The database needs the `vector` extension.

```bash
DATABASE_URL=postgresql://anchora@localhost:5432/anchora python -m anchora.eval
```

Run on 2026-10-27 with embedding model `fixed-embedder` version 1 and language model `citing-stand-in`. This is that stand-in, not a hosted model. `fixed-embedder` does not encode meaning, and a question with no passage for the role can still be answered when the role can see other passages. A cosine cutoff on that embedder does not separate those nine missed refusals from the evidence questions, so this version still has no similarity floor.

```
embedding_model: fixed-embedder
embedding_version: 1
language_model: citing-stand-in
questions: 50
evidence_questions: 41
hit_at_5: 0.951
recall_at_5: 0.956
citation_validity: 1.000
citations: 250
correct_refusals: 0
false_refusals: 0
missed_refusals: 9
retrieval_ms_p95: 20.802
generation_ms_p95: 0.010
input_tokens: 250
output_tokens: 50
```

On 2026-11-09 the same command printed the fusion rates again and the reorder of those five passages. Hit@5 and recall@5 stayed on the fusion figures. The model still receives the fusion order.

```
embedding_model: fixed-embedder
embedding_version: 1
language_model: citing-stand-in
questions: 50
evidence_questions: 41
hit_at_5: 0.951
recall_at_5: 0.956
rerank_hit_at_5: 0.951
rerank_recall_at_5: 0.956
citation_validity: 1.000
citations: 250
correct_refusals: 0
false_refusals: 0
missed_refusals: 9
retrieval_ms_p95: 4.891
generation_ms_p95: 0.004
input_tokens: 250
output_tokens: 50
```

On 2026-11-09 the same command printed `supported_answers: 1.000`. A delivered draft counts when every digit-bearing token in it appears in a cited excerpt. The stand-in draft is `See the cited passages.`, which adds no code. A refusal stays outside that rate. This is not a comparison with people. The other figures of that run match the block above, except `retrieval_ms_p95: 5.472` and `generation_ms_p95: 0.005`.

`python -m anchora.eval.spanish` does not load those 50 questions. On 2026-11-11 it scored one manual, `lote`, once with the `english` dictionary and once with `spanish`. Chunking stayed the same. Five filler manuals sit closer in the fixed embedder, so a lexical miss falls outside the five fused passages. These four rates do not replace the English baseline.

```bash
DATABASE_URL=postgresql://anchora@localhost:5432/anchora python -m anchora.eval.spanish
```

```
manual: lote
questions: 1
english_hit_at_5: 0.000
english_recall_at_5: 0.000
spanish_hit_at_5: 1.000
spanish_recall_at_5: 1.000
```

On 2026-11-11 `python -m anchora.eval` printed `retrieval_ms_p95: 11.034` and `hit_at_5: 0.951`. That is milliseconds on this corpus. Vector search stays an exact scan. No approximate index was added.

```
embedding_model: fixed-embedder
embedding_version: 1
language_model: citing-stand-in
questions: 50
evidence_questions: 41
hit_at_5: 0.951
recall_at_5: 0.956
rerank_hit_at_5: 0.951
rerank_recall_at_5: 0.956
citation_validity: 1.000
supported_answers: 1.000
citations: 250
correct_refusals: 0
false_refusals: 0
missed_refusals: 9
retrieval_ms_p95: 11.034
generation_ms_p95: 0.010
input_tokens: 250
output_tokens: 50
```

## Tests

GitHub Actions runs `pytest` against PostgreSQL 16 with pgvector, on pull requests and on pushes to `main`. The job installs no model client and uses no API key. Tests embed with a deterministic stand-in.

The local database needs the `vector` extension. The image `pgvector/pgvector:pg16` provides it.

```bash
pip install -e ".[dev]"
DATABASE_URL=postgresql://anchora@localhost:5432/anchora pytest
```

The same suite runs in Docker. The image installs no model client and sets no API key. Compose does not publish the database port.

```bash
docker compose run --rm --build tests
```

The service listens on port 8000. On an empty catalog, `POST /v1/answers` with question `Meridian` and role `operator` is HTTP 200 and `no_evidence`.

```bash
docker compose up --build api
```

## Try it

Create a codespace on the 2-core machine. It uses the default image. Delete the codespace when you finish.

```bash
docker compose up --build --detach --wait api
curl --retry 5 --retry-connrefused --retry-delay 1 -s -X POST localhost:8000/v1/answers \
  -H 'content-type: application/json' \
  -d '{"question":"Meridian","role":"operator"}'
docker compose down
```

On an empty catalog the response is HTTP 200 and `no_evidence`.

Load the bundled manuals into that database. The command replaces the catalog. `JE-4419` as `operator` cites the section `Book accruals`. The same question as `auditor` does not cite that manual.

```bash
docker compose exec api python -m anchora.sample
curl -s -X POST localhost:8000/v1/answers \
  -H 'content-type: application/json' \
  -d '{"question":"JE-4419","role":"operator"}'
curl -s -X POST localhost:8000/v1/answers \
  -H 'content-type: application/json' \
  -d '{"question":"JE-4419","role":"auditor"}'
```

Set `PUBLISH_PORT` when another process is already listening on 8000. The database stays unpublished.

```bash
PUBLISH_PORT=8001 docker compose up --build --detach api
```

## Contributing

Open a pull request against `main`. The `test` check has to pass before merge.

Architecture and decisions live in `docs/architecture/` and `docs/adr/`.

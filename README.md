# Anchora

[![tests](https://github.com/thevoidzzz/anchora/actions/workflows/tests.yml/badge.svg)](https://github.com/thevoidzzz/anchora/actions/workflows/tests.yml)

Grounded assistant for internal operating manuals. A citation is copied from the retrieved passage, or the answer is refused.

`POST /v1/answers` takes a question and a role (`operator` or `auditor`). A refusal is HTTP 200. Invalid input, a model that times out or returns the wrong shape, and a database that is down use `application/problem+json`.

## Evaluation

`python -m anchora.eval` loads the bundled manuals and the 50 hand-written questions, then prints hit@5 and recall@5 apart from refusals. The database needs the `vector` extension.

```bash
DATABASE_URL=postgresql://anchora@localhost:5432/anchora python -m anchora.eval
```

Run on 2026-10-27 with embedding model `fixed-embedder` version 1 and language model `citing-stand-in`. This is that stand-in, not a hosted model. `fixed-embedder` does not encode meaning, and a question with no passage for the role can still be answered when the role can see other passages: this version has no similarity cutoff, so those nine refusals are missed.

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

## Tests

GitHub Actions runs `pytest` against PostgreSQL 16 with pgvector, on pull requests and on pushes to `main`. The job installs no model client and uses no API key. Tests embed with a deterministic stand-in.

The local database needs the `vector` extension. The image `pgvector/pgvector:pg16` provides it.

```bash
pip install -e ".[dev]"
DATABASE_URL=postgresql://anchora@localhost:5432/anchora pytest
```

## Contributing

Open a pull request against `main`. The `test` check has to pass before merge.

Architecture and decisions live in `docs/architecture/` and `docs/adr/`.

# Anchora

[![tests](https://github.com/thevoidzzz/anchora/actions/workflows/tests.yml/badge.svg)](https://github.com/thevoidzzz/anchora/actions/workflows/tests.yml)

Grounded assistant for internal operating manuals. A citation is copied from the retrieved passage, or the answer is refused.

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

# Anchora

[![tests](https://github.com/thevoidzzz/anchora/actions/workflows/tests.yml/badge.svg)](https://github.com/thevoidzzz/anchora/actions/workflows/tests.yml)

Grounded assistant for internal operating manuals. A citation is copied from the retrieved passage, or the answer is refused.

## Tests

GitHub Actions runs `pytest` on pull requests and on pushes to `main`. The job installs no model client and uses no API key.

```bash
pip install pytest
pytest
```

## Contributing

Open a pull request against `main`. The `test` check has to pass before merge.

Architecture and decisions live in `docs/architecture/` and `docs/adr/`.

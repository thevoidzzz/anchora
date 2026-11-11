"""Print hit@5 and recall@5 for one Spanish manual under both dictionaries."""

import os
import sys

from anchora.domain.errors import EvalError
from anchora.eval.spanish import compare
from anchora.infrastructure.postgres import PostgresCatalog


def main() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is required")
    catalog = PostgresCatalog(database_url)
    try:
        catalog.ensure_schema()
        sys.stdout.write(compare(catalog))
    except EvalError as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()

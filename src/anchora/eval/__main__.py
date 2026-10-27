"""Print the evaluation report. Requires DATABASE_URL and does not call a hosted model."""

import os
import sys

from anchora.application.evaluate import evaluate
from anchora.domain.errors import EvalError
from anchora.domain.scoring import format_report
from anchora.eval.load import load_golden, load_manuals
from anchora.infrastructure.citing_model import CitingModel
from anchora.infrastructure.fixed_embedder import FixedEmbedder
from anchora.infrastructure.postgres import PostgresCatalog


def main() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is required")
    catalog = PostgresCatalog(database_url)
    try:
        catalog.ensure_schema()
        report = evaluate(catalog, FixedEmbedder(), CitingModel(), load_manuals(), load_golden())
    except EvalError as exc:
        raise SystemExit(str(exc)) from exc
    sys.stdout.write(format_report(report))
    if report.invalid_citations:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

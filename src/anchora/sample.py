"""Replace the catalog with the bundled manuals. The check does not call this."""

import os

from anchora.application.ingest import ingest_manual
from anchora.eval.load import load_manuals
from anchora.infrastructure.fixed_embedder import FixedEmbedder
from anchora.infrastructure.postgres import PostgresCatalog


def load_samples(catalog: PostgresCatalog, embedder: FixedEmbedder) -> int:
    """Clear the catalog and store the bundled manuals. Returns how many chunks were stored."""

    catalog.clear()
    stored = 0
    for manual in load_manuals():
        stored += len(ingest_manual(manual, catalog, embedder))
    return stored


def main() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is required")
    catalog = PostgresCatalog(database_url)
    catalog.ensure_schema()
    load_samples(catalog, FixedEmbedder())


if __name__ == "__main__":
    main()

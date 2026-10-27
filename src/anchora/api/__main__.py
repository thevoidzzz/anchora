"""Process entrypoint. Wires the catalog and the stand-in models. No paid key."""

import os

from anchora.api.app import create_app
from anchora.infrastructure.citing_model import CitingModel
from anchora.infrastructure.fixed_embedder import FixedEmbedder
from anchora.infrastructure.postgres import PostgresCatalog


def app_from_env():
    """Build the API from DATABASE_URL. The catalog is not cleared."""

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is required")
    catalog = PostgresCatalog(database_url)
    catalog.ensure_schema()
    return create_app(catalog, FixedEmbedder(), CitingModel())


def main() -> None:
    import uvicorn

    uvicorn.run(app_from_env(), host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()

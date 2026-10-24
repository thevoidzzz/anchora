"""PostgreSQL for tests that store or search manuals."""

import os

import pytest


@pytest.fixture(scope="session")
def database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        pytest.fail("DATABASE_URL is required and must point at PostgreSQL")
    return url

"""The API can move to another host port. The database stays unpublished."""

from pathlib import Path

_COMPOSE = Path(__file__).resolve().parents[1] / "compose.yaml"


def test_the_host_port_defaults_to_8000_and_the_database_stays_private() -> None:
    text = _COMPOSE.read_text(encoding="utf-8")
    assert text.count("\n    ports:") == 1
    assert '"${PUBLISH_PORT:-8000}:8000"' in text
    assert "5432:5432" not in text

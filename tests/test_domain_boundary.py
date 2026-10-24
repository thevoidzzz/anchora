"""The domain package stays free of drivers. The architecture test is the lock."""

import ast
from pathlib import Path

_DOMAIN = Path(__file__).resolve().parents[1] / "src" / "anchora" / "domain"
_FORBIDDEN_PREFIXES = (
    "anchora.infrastructure",
    "anchora.api",
    "fastapi",
    "psycopg",
    "sqlalchemy",
    "httpx",
    "openai",
)


def test_domain_does_not_import_infrastructure_or_the_api() -> None:
    violations: list[str] = []
    for path in sorted(_DOMAIN.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            modules: list[str] = []
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                modules = [node.module]
            for module in modules:
                if module.startswith(_FORBIDDEN_PREFIXES):
                    violations.append(f"{path.name} imports {module}")
    assert violations == []

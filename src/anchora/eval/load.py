"""Load the versioned manuals and golden set."""

import json
from pathlib import Path

from anchora.domain.errors import EvalError
from anchora.domain.scoring import EvalItem

_ROOT = Path(__file__).resolve().parent


def corpus_dir() -> Path:
    return _ROOT / "corpus"


def golden_path() -> Path:
    return _ROOT / "golden.json"


def load_manuals() -> tuple[str, ...]:
    paths = sorted(corpus_dir().glob("*.md"))
    if not paths:
        raise EvalError("the corpus directory has no manuals")
    return tuple(path.read_text(encoding="utf-8") for path in paths)


def load_golden() -> tuple[EvalItem, ...]:
    payload = json.loads(golden_path().read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise EvalError("the golden set must be a list")
    items: list[EvalItem] = []
    for raw in payload:
        if not isinstance(raw, dict):
            raise EvalError("each golden item must be an object")
        sections = raw.get("relevant_sections")
        if not isinstance(sections, list) or not all(isinstance(section, str) for section in sections):
            raise EvalError(f"relevant_sections must be a list of strings: {raw.get('id')}")
        items.append(
            EvalItem(
                id=str(raw["id"]),
                role=str(raw["role"]),
                question=str(raw["question"]),
                relevant_sections=tuple(sections),
                expect_refusal=bool(raw["expect_refusal"]),
            )
        )
    return tuple(items)

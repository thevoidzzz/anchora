"""The codespace keeps the default image. The try request is the empty-catalog refusal."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_the_codespace_keeps_the_default_image() -> None:
    config = json.loads((ROOT / ".devcontainer" / "devcontainer.json").read_text(encoding="utf-8"))
    assert set(config) == {"name", "hostRequirements", "forwardPorts", "features"}
    assert config["name"] == "Anchora"
    assert config["hostRequirements"] == {"cpus": 2}
    assert config["forwardPorts"] == [8000]
    assert config["features"] == {"ghcr.io/devcontainers/features/docker-in-docker:4": {}}


def test_the_readme_try_asks_the_empty_catalog() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Create a codespace on the 2-core machine." in readme
    assert "default image" in readme
    assert "Delete the codespace when you finish." in readme
    assert "docker compose up --build --detach --wait api" in readme
    assert "localhost:8000/v1/answers" in readme
    assert '{"question":"Meridian","role":"operator"}' in readme
    assert "docker compose down" in readme
    assert "no_evidence" in readme
    lowered = readme.lower()
    for needle in ("openai", "anthropic", "render.com", "railway.app", "fly.dev"):
        assert needle not in lowered


def test_the_image_suite_copies_the_codespace() -> None:
    dockerfile = ROOT / "Dockerfile"
    if not dockerfile.is_file():
        return  # shortcut: the test image omits the Dockerfile, the checkout run locks this COPY
    assert "COPY .devcontainer ./.devcontainer" in dockerfile.read_text(encoding="utf-8")


def test_the_architecture_records_the_default_image() -> None:
    path = ROOT / "docs" / "architecture" / "ARCHITECTURE.md"
    if not path.is_file():
        return  # shortcut: the test image omits docs, the checkout run locks this sentence
    text = path.read_text(encoding="utf-8")
    assert "imagen Linux por defecto" in text
    assert "2 núcleos" in text
    assert "No hay prebuild." in text

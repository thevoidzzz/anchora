"""Split a policy manual into chunks whose ids survive a reingest."""

import re
from dataclasses import dataclass
from typing import Literal, cast

from anchora.domain.errors import ChunkConfigError, ManualError

Audience = Literal["operator", "auditor", "both"]

DEFAULT_MAX_CHARS = 1500
DEFAULT_OVERLAP_CHARS = 200

_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_SECTION_HEADING_RE = re.compile(r"^(#{2,3})[ \t]+(.*\S)[ \t]*$")
_ANY_HEADING_RE = re.compile(r"^#{1,6}(?:[ \t]|$)")
_PAGE_RE = re.compile(r"^page:[ \t]*([1-9][0-9]*)[ \t]*$")
_FRONTMATTER_KEYS = ("id", "title", "audience")
_AUDIENCES = frozenset({"operator", "auditor", "both"})


@dataclass(frozen=True, slots=True)
class ChunkConfig:
    """Fixed character window. Overlap must stay strictly inside the window."""

    max_chars: int
    overlap_chars: int

    def __post_init__(self) -> None:
        if self.max_chars < 1:
            raise ChunkConfigError("max_chars must be at least 1")
        if self.overlap_chars < 0 or self.overlap_chars >= self.max_chars:
            raise ChunkConfigError("overlap_chars must be >= 0 and < max_chars")


@dataclass(frozen=True, slots=True)
class Chunk:
    """One window of a section. Slices of the same section share the path and page."""

    chunk_id: str
    document_id: str
    document_title: str
    audience: Audience
    section_path: str
    ordinal: int
    page: int
    text: str


@dataclass(frozen=True, slots=True)
class _Manual:
    document_id: str
    title: str
    audience: Audience


@dataclass(frozen=True, slots=True)
class _Section:
    path: str
    page: int
    text: str


def parse_manual(text: str, config: ChunkConfig | None = None) -> tuple[Chunk, ...]:
    """Chunk a manual. The same file and the same window always yield the same ids."""

    window = config if config is not None else ChunkConfig(DEFAULT_MAX_CHARS, DEFAULT_OVERLAP_CHARS)
    normalized = text.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    manual, body = _split_frontmatter(normalized)
    sections = _parse_sections(body)
    chunks: list[Chunk] = []
    for section in sections:
        chunks.extend(_chunks_for_section(manual, section, window))
    return tuple(chunks)


def _split_frontmatter(text: str) -> tuple[_Manual, str]:
    if not text.startswith("---\n"):
        raise ManualError("manual must start with frontmatter")
    rest = text[4:]
    close = rest.find("\n---")
    if close == -1:
        raise ManualError("frontmatter is not closed")
    raw_meta = rest[:close]
    after = rest[close + len("\n---") :]
    if after.startswith("\n"):
        body = after[1:]
    elif after == "":
        body = ""
    else:
        raise ManualError("frontmatter must close on its own line")
    return _parse_frontmatter(raw_meta), body


def _parse_frontmatter(raw: str) -> _Manual:
    found: dict[str, str] = {}
    for line in raw.split("\n"):
        if line.strip() == "":
            continue
        if ":" not in line:
            raise ManualError("frontmatter field must be key: value")
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key not in _FRONTMATTER_KEYS:
            raise ManualError(f"unknown frontmatter field: {key}")
        if key in found:
            raise ManualError(f"duplicate frontmatter field: {key}")
        if value == "":
            raise ManualError(f"frontmatter field is empty: {key}")
        found[key] = value
    missing = [key for key in _FRONTMATTER_KEYS if key not in found]
    if missing:
        raise ManualError(f"frontmatter is missing: {', '.join(missing)}")
    document_id = found["id"]
    if _ID_RE.fullmatch(document_id) is None:
        raise ManualError("document id must be a lowercase slug")
    audience = found["audience"]
    if audience not in _AUDIENCES:
        raise ManualError("audience must be operator, auditor, or both")
    return _Manual(document_id=document_id, title=found["title"], audience=cast(Audience, audience))


def _parse_sections(body: str) -> tuple[_Section, ...]:
    lines = body.split("\n")
    index = _skip_blanks(lines, 0)
    if index >= len(lines):
        raise ManualError("manual has no sections")
    current_h2: str | None = None
    seen: set[str] = set()
    sections: list[_Section] = []
    while index < len(lines):
        heading = _section_heading(lines[index])
        if heading is None:
            if _ANY_HEADING_RE.match(lines[index]):
                raise ManualError("only ## and ### headings are sections")
            raise ManualError("text before the first section")
        level, raw_heading = heading
        title = " ".join(raw_heading.split())
        if "#" in title:
            raise ManualError("a heading cannot contain #")
        if level == 3:
            if current_h2 is None:
                raise ManualError("a subsection needs a parent section")
            path = f"{current_h2} / {title}"
        else:
            current_h2 = title
            path = title
        if path in seen:
            raise ManualError(f"duplicate section path: {path}")
        seen.add(path)
        index = _skip_blanks(lines, index + 1)
        page_match = _PAGE_RE.match(lines[index]) if index < len(lines) else None
        if page_match is None:
            raise ManualError(f"section needs a page: {path}")
        page = int(page_match.group(1))
        index += 1
        body_lines: list[str] = []
        while index < len(lines) and _section_heading(lines[index]) is None:
            if lines[index].strip() != "" and _ANY_HEADING_RE.match(lines[index]):
                raise ManualError("only ## and ### headings are sections")
            body_lines.append(lines[index])
            index += 1
        text = "\n".join(body_lines).strip()
        if text == "":
            raise ManualError(f"section has no text: {path}")
        sections.append(_Section(path=path, page=page, text=text))
    return tuple(sections)


def _skip_blanks(lines: list[str], index: int) -> int:
    while index < len(lines) and lines[index].strip() == "":
        index += 1
    return index


def _section_heading(line: str) -> tuple[int, str] | None:
    match = _SECTION_HEADING_RE.match(line)
    if match is None:
        return None
    return len(match.group(1)), match.group(2)


def _chunks_for_section(manual: _Manual, section: _Section, config: ChunkConfig) -> tuple[Chunk, ...]:
    return tuple(
        Chunk(
            chunk_id=f"{manual.document_id}#{section.path}#{ordinal}",
            document_id=manual.document_id,
            document_title=manual.title,
            audience=manual.audience,
            section_path=section.path,
            ordinal=ordinal,
            page=section.page,
            text=piece,
        )
        for ordinal, piece in enumerate(_windows(section.text, config))
    )


def _windows(text: str, config: ChunkConfig) -> tuple[str, ...]:
    step = config.max_chars - config.overlap_chars
    start = 0
    pieces: list[str] = []
    while start < len(text):
        pieces.append(text[start : start + config.max_chars])
        if start + config.max_chars >= len(text):
            break
        start += step
    return tuple(pieces)

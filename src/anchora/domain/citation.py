"""Copy citations from retrieved chunks. The model does not write the excerpt."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from anchora.domain.errors import DuplicateRetrievedChunkError
from anchora.domain.manual import Chunk


@dataclass(frozen=True, slots=True)
class Citation:
    """A passage the server copied. `excerpt` is the retrieved window, whole."""

    chunk_id: str
    document: str
    section: str
    page: int
    excerpt: str


@dataclass(frozen=True, slots=True)
class AssembledAnswer:
    """Either the draft plus copied citations, or a refusal that drops the draft."""

    refused: bool
    answer: str | None
    reason: Literal["no_valid_citation"] | None
    citations: tuple[Citation, ...]


def assemble_answer(draft: str, chosen_ids: Sequence[str], retrieved: Sequence[Chunk]) -> AssembledAnswer:
    """Keep chosen ids that this retrieval returned, in the model's order.

    A repeated chosen id is published once, at its first occurrence. An id that
    was not retrieved is dropped. If none remain, the draft is not returned.

    An empty retrieval is a different refusal, `no_evidence`, and the caller
    decides that before the model runs. This function does not emit that reason.
    """

    by_id: dict[str, Chunk] = {}
    for chunk in retrieved:
        if chunk.chunk_id in by_id:
            raise DuplicateRetrievedChunkError(chunk.chunk_id)
        by_id[chunk.chunk_id] = chunk

    seen: set[str] = set()
    citations: list[Citation] = []
    for chunk_id in chosen_ids:
        if chunk_id in seen or chunk_id not in by_id:
            continue
        seen.add(chunk_id)
        chunk = by_id[chunk_id]
        citations.append(
            Citation(
                chunk_id=chunk.chunk_id,
                document=chunk.document_title,
                section=chunk.section_path,
                page=chunk.page,
                excerpt=chunk.text,
            )
        )
    if not citations:
        return AssembledAnswer(refused=True, answer=None, reason="no_valid_citation", citations=())
    return AssembledAnswer(refused=False, answer=draft, reason=None, citations=tuple(citations))

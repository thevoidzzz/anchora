"""A cosine cutoff does not separate the fixed set, so the answer path has no floor."""

from anchora.domain.manual import parse_manual
from anchora.eval.load import load_golden, load_manuals
from anchora.infrastructure.fixed_embedder import FixedEmbedder


def _separates(evidence: list[float], refusals: list[float]) -> bool:
    """True when every refusal sits strictly farther than every evidence question."""

    if not evidence or not refusals:
        return False
    return max(evidence) < min(refusals)


def _nearest(question: str, role: str, chunks, embedder: FixedEmbedder) -> float:
    allowed = [chunk for chunk in chunks if chunk.audience in {role, "both"}]
    query = embedder.embed((question,))[0]
    distances = []
    for chunk in allowed:
        vector = embedder.embed((chunk.text,))[0]
        distances.append(1 - sum(left * right for left, right in zip(query, vector, strict=True)))
    return min(distances)


def test_a_cutoff_needs_the_refusals_to_sit_strictly_farther() -> None:
    assert _separates([0.0, 0.2], [0.5, 1.0])
    assert not _separates([0.0, 1.0], [0.0, 1.0])


def test_the_fixed_embedder_does_not_separate_the_nine_refusals() -> None:
    embedder = FixedEmbedder()
    chunks = [chunk for manual in load_manuals() for chunk in parse_manual(manual)]
    evidence: list[float] = []
    refusals: list[float] = []
    for item in load_golden():
        distance = _nearest(item.question, item.role, chunks, embedder)
        (refusals if item.expect_refusal else evidence).append(distance)

    assert len(refusals) == 9
    assert 0.0 in evidence and 1.0 in evidence
    assert 0.0 in refusals and 1.0 in refusals
    assert not _separates(evidence, refusals)

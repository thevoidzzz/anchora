"""One Spanish manual, scored once with each dictionary. The English set stays separate."""

from pathlib import Path

from anchora.application.evaluate import evaluate
from anchora.application.ports import DocumentCatalog
from anchora.domain.scoring import EvalItem
from anchora.infrastructure.citing_model import CitingModel
from anchora.infrastructure.fixed_embedder import FixedEmbedder

QUESTION = "Cuando hay que contabilizar?"
_BODY = "La mesa contabiliza el lote antes del mediodia."
_ROOT = Path(__file__).resolve().parent


def manual_text() -> str:
    return (_ROOT / "lote.md").read_text(encoding="utf-8")


def english_manual() -> str:
    text = manual_text()
    swapped = text.replace("lexicon: spanish\n", "lexicon: english\n", 1)
    if swapped == text:
        raise RuntimeError("the Spanish manual has no lexicon line")
    return swapped


def distractors() -> tuple[str, ...]:
    return tuple(
        (
            f"---\nid: desk-{index}\ntitle: Desk {index}\naudience: operator\n---\n\n"
            f"## Note\npage: 1\n\nThe north desk posts payroll code N{index}.\n"
        )
        for index in range(1, 6)
    )


def compare(catalog: DocumentCatalog) -> str:
    """Print hit@5 and recall@5 before and after the spanish dictionary.

    Five nearer distractors keep the section out of the fused five when the
    english dictionary misses the stem. The chunk text does not change.
    """

    item = (
        EvalItem(
            id="contabilizar",
            role="operator",
            question=QUESTION,
            relevant_sections=("lote#Cierre",),
            expect_refusal=False,
        ),
    )
    embedder = _embedder()
    model = CitingModel()
    fillers = distractors()
    before = evaluate(catalog, embedder, model, (english_manual(), *fillers), item)
    after = evaluate(catalog, embedder, model, (manual_text(), *fillers), item)
    if before.hit_at_5 is None or before.recall_at_5 is None:
        raise RuntimeError("the english pass has no evidence question")
    if after.hit_at_5 is None or after.recall_at_5 is None:
        raise RuntimeError("the spanish pass has no evidence question")
    return (
        "manual: lote\n"
        "questions: 1\n"
        f"english_hit_at_5: {before.hit_at_5:.3f}\n"
        f"english_recall_at_5: {before.recall_at_5:.3f}\n"
        f"spanish_hit_at_5: {after.hit_at_5:.3f}\n"
        f"spanish_recall_at_5: {after.recall_at_5:.3f}\n"
    )


def _embedder() -> FixedEmbedder:
    assigned: dict[str, tuple[float, ...]] = {
        QUESTION: (1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        _BODY: (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0),
    }
    for index in range(1, 6):
        assigned[f"The north desk posts payroll code N{index}."] = (
            1.0,
            0.05 * index,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        )
    return FixedEmbedder(assigned=assigned)

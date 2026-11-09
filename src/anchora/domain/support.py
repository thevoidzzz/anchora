"""A delivered draft may not introduce a code the excerpts do not contain."""

import re
from collections.abc import Sequence

# shortcut: words without a digit are not checked, a paraphrase with no code still counts
_CODE = re.compile(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*")


def draft_is_supported(draft: str, excerpts: Sequence[str]) -> bool:
    """True when every digit-bearing token in the draft appears in an excerpt."""

    if not excerpts:
        return False
    covered = "\n".join(excerpts).lower()
    for token in _CODE.findall(draft):
        if any(character.isdigit() for character in token) and token.lower() not in covered:
            return False
    return True

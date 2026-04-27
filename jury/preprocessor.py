"""
Strip the Presentation of Case section from a .md file.
Returns the full text, the reasoning-only text, and the byte offset
at which the reasoning section begins (needed to translate span positions
back to full-document coordinates).
"""

import re
from pathlib import Path

# The reasoning section starts at the first heading that is NOT "Presentation of Case"
_REASONING_START_RE = re.compile(
    r"^## (?!Presentation of Case)",
    re.MULTILINE,
)


def load_case(path: str | Path) -> tuple[str, str, int]:
    """
    Returns:
        full_text       — complete file content
        reasoning_text  — content from '## Differential Diagnosis' onward
        reasoning_offset — char index in full_text where reasoning_text starts
    """
    full_text = Path(path).read_text(encoding="utf-8")
    match = _REASONING_START_RE.search(full_text)
    if match is None:
        # No PoC found — treat entire document as reasoning
        return full_text, full_text, 0
    offset = match.start()
    return full_text, full_text[offset:], offset

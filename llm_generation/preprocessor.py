"""
Extract the clinical presentation from a source case.

The jury pipeline keeps the reasoning section. This generation pipeline does
the inverse: it gives models only the factual Presentation of Case.
"""

import re
from dataclasses import dataclass
from pathlib import Path


_PRESENTATION_HEADING_RE = re.compile(r"^## Presentation of Case\s*$", re.MULTILINE)
_NEXT_SECTION_RE = re.compile(r"^## (?!Presentation of Case\s*$).+", re.MULTILINE)


@dataclass(frozen=True)
class CasePresentation:
    source_path: Path
    title: str
    presentation_text: str

    @property
    def source_case_name(self) -> str:
        return self.source_path.name

    @property
    def case_stem(self) -> str:
        return self.source_path.stem

    @property
    def case_id(self) -> str:
        return self.source_path.stem.replace(" ", "_")


def load_presentation(path: str | Path) -> CasePresentation:
    source_path = Path(path)
    full_text = source_path.read_text(encoding="utf-8")
    title = _extract_title(full_text, source_path)

    presentation_match = _PRESENTATION_HEADING_RE.search(full_text)
    if presentation_match is None:
        raise ValueError(f"No '## Presentation of Case' heading found in {source_path}")

    next_section_match = _NEXT_SECTION_RE.search(full_text, presentation_match.end())
    end = next_section_match.start() if next_section_match else len(full_text)
    presentation_text = full_text[presentation_match.start() : end].strip()

    return CasePresentation(
        source_path=source_path,
        title=title,
        presentation_text=presentation_text,
    )


def _extract_title(full_text: str, source_path: Path) -> str:
    for line in full_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped
    return f"# {source_path.stem}"

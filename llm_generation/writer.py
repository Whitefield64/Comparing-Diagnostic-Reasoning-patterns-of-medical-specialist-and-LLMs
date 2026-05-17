"""Write generated differential-diagnosis cases to cases_llm/."""

import re
from datetime import datetime, timezone
from pathlib import Path

from llm_generation.preprocessor import CasePresentation


def model_slug(model: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", model).strip("-")
    return slug or "model"


def output_path(case: CasePresentation, model: str, output_dir: Path) -> Path:
    case_dir = output_dir / case.case_stem
    return case_dir / f"{case.case_stem}__{model_slug(model)}.md"


def write_generated_case(
    case: CasePresentation,
    model: str,
    generated_differential: str,
    output_dir: Path,
) -> Path:
    out_path = output_path(case, model, output_dir)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    generated_section = _normalize_generated_section(generated_differential)
    payload = "\n".join(
        [
            "---",
            f'source_case: "{case.source_case_name}"',
            f'source_case_id: "{case.case_id}"',
            f'generation_model: "{model}"',
            f'generated_at: "{datetime.now(timezone.utc).isoformat()}"',
            'input_section: "Presentation of Case"',
            'generated_section: "Differential Diagnosis"',
            "---",
            "",
            case.title,
            "",
            case.presentation_text,
            "",
            generated_section,
            "",
        ]
    )
    out_path.write_text(payload, encoding="utf-8")
    return out_path


def _normalize_generated_section(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    if not cleaned.startswith("## Differential Diagnosis"):
        cleaned = f"## Differential Diagnosis\n\n{cleaned}"
    else:
        lines = cleaned.splitlines()
        lines[0] = "## Differential Diagnosis"
        cleaned = "\n".join(lines).strip()
    return cleaned

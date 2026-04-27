"""
Serialize voter results to the standard annotation JSON format used by the project.

Output schema (identical to manual annotation files):
{
  "case": "2003 Case 21.md",
  "annotator": "Judge001",
  "exported_at": "2026-04-27T…",
  "annotations": [ { "ranges": [[start, end]], "label": int, "label_name": str, "text": str } ]
}
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from jury.runner import VoterResult

logger = logging.getLogger(__name__)


def write_voter(
    result: VoterResult,
    case_name: str,
    output_dir: Path,
) -> Path | None:
    """
    Write a single voter's resolved annotations to disk.
    Returns the output path, or None if the voter failed.
    """
    if result.failed:
        return None

    payload = {
        "case": case_name,
        "annotator": f"Judge{result.voter_id:03d}",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "annotations": result.resolved,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(case_name).stem.replace(" ", "_")
    out_path = output_dir / f"{stem}_Judge{result.voter_id:03d}.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Written: %s", out_path)
    return out_path


def write_summary(
    results: list[VoterResult],
    case_name: str,
    output_dir: Path,
) -> Path:
    """
    Write a summary JSON with statistics for the whole jury run.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(case_name).stem.replace(" ", "_")
    summary_path = output_dir / f"{stem}_jury_summary.json"

    summary = {
        "case": case_name,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "n_voters": len(results),
        "n_successful": sum(1 for r in results if not r.failed),
        "n_failed": sum(1 for r in results if r.failed),
        "voters": [
            {
                "voter_id": r.voter_id,
                "failed": r.failed,
                "n_resolved": len(r.resolved),
                "n_unresolved": len(r.unresolved),
                "unresolved": r.unresolved,
            }
            for r in results
        ],
    }

    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Summary written: %s", summary_path)
    return summary_path

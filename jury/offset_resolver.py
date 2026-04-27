"""
Map LLM-returned verbatim text spans to character offsets in the source document.

Strategy:
  1. Exact string search in full_text.
  2. If not found: rapidfuzz partial-ratio fuzzy search over a sliding window.
  3. If score < threshold: mark as 'unresolved' — never hallucinate an offset.
"""

import logging

from rapidfuzz import fuzz

from jury.config import FUZZY_MATCH_THRESHOLD, LABEL_MAP

logger = logging.getLogger(__name__)

# Sliding window size for fuzzy search: slightly larger than the span being searched
_WINDOW_MULTIPLIER = 1.5


def resolve(
    raw_annotations: list[dict],
    full_text: str,
    label_map: dict[str, int] = LABEL_MAP,
) -> tuple[list[dict], list[dict]]:
    """
    Convert a list of {label_name, text} dicts into annotation dicts with char offsets.

    Returns:
        resolved    — list of annotation dicts ready for the output JSON
        unresolved  — list of dicts that could not be located in full_text
    """
    resolved: list[dict] = []
    unresolved: list[dict] = []

    for item in raw_annotations:
        label_name = item.get("label_name", "").strip().upper()
        span_text = item.get("text", "").strip()

        if not label_name or not span_text:
            continue

        if label_name not in label_map:
            logger.warning("Unknown label '%s' — skipping.", label_name)
            continue

        label_id = label_map[label_name]
        start, end = _find_span(span_text, full_text)

        if start == -1:
            logger.warning(
                "Unresolved span for %s (len=%d): %.60s…",
                label_name,
                len(span_text),
                span_text,
            )
            unresolved.append({"label_name": label_name, "text": span_text})
        else:
            resolved.append(
                {
                    "ranges": [[start, end]],
                    "label": label_id,
                    "label_name": label_name,
                    "text": full_text[start:end],
                }
            )

    return resolved, unresolved


def _find_span(span: str, source: str) -> tuple[int, int]:
    """Return (start, end) of span in source, or (-1, -1) if not found."""
    # 1. Exact match
    idx = source.find(span)
    if idx != -1:
        return idx, idx + len(span)

    # 2. Fuzzy search over sliding windows
    window_size = min(len(source), int(len(span) * _WINDOW_MULTIPLIER))
    best_score = 0
    best_start = -1

    step = max(1, len(span) // 4)
    for i in range(0, len(source) - window_size + 1, step):
        window = source[i : i + window_size]
        score = fuzz.partial_ratio(span, window)
        if score > best_score:
            best_score = score
            best_start = i

    if best_score >= FUZZY_MATCH_THRESHOLD and best_start != -1:
        # Refine: find the best sub-window alignment
        refined_start, refined_end = _refine_window(span, source, best_start, window_size)
        logger.debug(
            "Fuzzy match (score=%d) at [%d:%d]", best_score, refined_start, refined_end
        )
        return refined_start, refined_end

    return -1, -1


def _refine_window(span: str, source: str, window_start: int, window_size: int) -> tuple[int, int]:
    """
    Within the matched window, find the tightest alignment by trying smaller offsets.
    Returns the best (start, end) approximating the span boundaries.
    """
    region = source[window_start : window_start + window_size + len(span)]
    best_score = 0
    best_i = 0

    for i in range(len(region) - len(span) + 1):
        candidate = region[i : i + len(span)]
        score = fuzz.ratio(span, candidate)
        if score > best_score:
            best_score = score
            best_i = i

    start = window_start + best_i
    return start, start + len(span)

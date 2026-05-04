# NLP Business

An end-to-end research workspace for comparing diagnostic reasoning in medical specialists and LLMs.

The project is built around a simple but important idea: diagnosis is not just a final answer. In clinical case discussions, reasoning appears as a sequence of abductive, deductive, and inductive moves, and those moves can be annotated, compared, and modeled. This repository turns that idea into a working system with a human annotation interface, a comparison viewer, and an automated LLM jury pipeline that writes outputs in the same schema as the human labels.

## What This Project Does

This repository supports a three-stage workflow:

1. Manually annotate reasoning spans in clinical case discussions.
2. Compare multiple annotations or model runs on the same case.
3. Run an LLM jury to produce machine annotations that can be compared directly with human work.

The focus is on the reasoning section of each case, not just the diagnosis. That makes the project more useful for studying epistemic behavior: hypothesis generation, hypothesis testing, and probabilistic conclusion formation.

## Why It Is Different

This is not a generic text-labeling demo. The implementation is designed around the structure of clinical reasoning itself:

- The annotation schema uses 3 reasoning modes and 12 subtypes.
- The human UI only annotates the reasoning section of the case, not the factual presentation.
- The LLM jury never invents character offsets; it returns verbatim spans and resolves them back to the source text deterministically.
- Human and machine outputs use the same JSON format, which makes comparison straightforward.
- The comparison tool is built for disagreement analysis, not just visualization.

## System Overview

```text
cases/*.md
	├──> annotation_tool  ──> annotated_cases/*.json
	├──> jury pipeline    ──> jury_output/*/*.json
	└──> comparison_tool  ──> multi-annotator / multi-run inspection
```

## Main Components

### Annotation Tool

The annotation tool is a local Flask app for human labeling of reasoning spans.

- Load a case from `cases/`
- Choose one of the 12 epistemic labels
- Highlight spans directly in the text
- Export JSON annotations
- Import another annotator’s JSON as a visual comparison layer
- Merge adjacent spans when needed

It runs on `http://localhost:5001`.

### Comparison Tool

The comparison tool is a read-only viewer for exploring multiple JSON annotation files against the same case text.

- Fetches the matching case text from `cases/`
- Overlays spans from multiple sources
- Highlights agreement and disagreement
- Shows a detail panel with label distributions and contributing spans
- Uses consensus thresholds from `comparison_tool/config.json`

It runs on `http://localhost:5002`.

### LLM Jury

The jury pipeline generates machine annotations with multiple independent voters.

- Strips the Presentation of Case section before prompting
- Prompts the model with the 12-label taxonomy and few-shot human examples
- Runs multiple voters with rate limiting and retries
- Resolves quoted spans back to character offsets in the source text
- Writes one JSON file per voter plus a summary file

The jury output is schema-compatible with the human annotation files, so it can be loaded directly into the comparison tool.

## How the Workflow Operates

1. Start with a case from `cases/`.
2. Annotate reasoning spans with the manual tool and save them under `annotated_cases/`.
3. Use the comparison tool to inspect span alignment, label agreement, and annotation drift.
4. Run the LLM jury on the same case text to generate multiple independent model outputs.
5. Compare human and machine annotations using the same viewer and JSON schema.

The important design choice is that the annotation target is the reasoning trace itself. The project therefore captures not only what diagnosis was reached, but how the reasoning unfolded.

## Repository Layout

- `cases/` contains the clinical case texts.
- `annotated_cases/` contains manually annotated JSON files.
- `annotation_tool/` contains the human labeling UI.
- `comparison_tool/` contains the multi-file comparison viewer.
- `jury/` contains the automated LLM annotation pipeline.
- `jury_output/` stores voter outputs and summary files.
- `docs/` contains implementation notes for each module.
- `appendix_ref8/` stores the source CSV associated with the Hom et al. dataset.

## Quick Start

Set `NVIDIA_API_KEY` in `.env` before running the jury pipeline.

```bash
# Human annotation UI
cd annotation_tool && uv run python server.py

# Comparison viewer
cd comparison_tool && uv run python server.py

# Cheap end-to-end jury smoke test
uv run python -m jury.run_jury --dry-run "cases/2003 Case 21.md"
```

For a full batch run:

```bash
uv run python -m jury.run_jury cases/*.md
```

## Outputs

The project keeps a shared JSON schema across human and machine annotations. A typical export includes:

- `case`
- `annotator`
- `exported_at`
- `annotations`

Each annotation stores character ranges, a numeric label, a label name, and the extracted text span. That makes the outputs easy to compare, audit, and reuse in downstream analysis.

## Documentation

If you want the implementation details, start with:

- `docs/system_overview.md`
- `docs/annotation_tool.md`
- `docs/comparison_tool.md`
- `docs/llm_jury.md`
- `jury/README.md`

## Tech Stack

- Python
- Flask
- aiohttp
- rapidfuzz
- NVIDIA Build API

## Project Goal

The long-term goal is to compare human and LLM diagnostic reasoning distributions across the same case library, using a reproducible epistemic framework instead of treating the model output as a black box.


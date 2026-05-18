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
cases/*.md  ──────────────────────────────────────> jury pipeline ──> jury_output/{case}/*.json
                                                         │
cases_llm/{case}/{case}__{model}.md  ─────────────> jury pipeline ──> jury_output_llm/{case}/{model}/*.json
         ▲
         │
llm_generation pipeline (generates differential diagnoses)

cases/*.md ──> annotation_tool ──> annotated_cases/*.json
           └──> comparison_tool ──> multi-annotator / multi-run inspection
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

### LLM Generation

The generation pipeline produces LLM-written differential diagnoses for the same cases used by human physicians. Three models are run on each case (Llama 3.3 70B, GPT-OSS 120B, Qwen3 80B). Each model's output is saved as a separate `.md` file inside `cases_llm/{case}/`, preserving the original Presentation of Case and replacing only the reasoning section.

### LLM Jury

The jury pipeline annotates reasoning spans with multiple independent voters and works on both human and LLM-generated cases.

- Strips the Presentation of Case section before prompting
- Prompts the model with the 12-label taxonomy and few-shot human examples
- Runs multiple voters with rate limiting and retries
- Resolves quoted spans back to character offsets in the source text
- Writes one JSON file per voter plus a summary file

**Human cases** output goes to `jury_output/{case}/`. **LLM cases** output goes to `jury_output_llm/{case}/{model}/`, keeping each generation model's jury results in its own subfolder.

The jury output is schema-compatible with the human annotation files, so it can be loaded directly into the comparison tool.

## How the Workflow Operates

1. Start with a case from `cases/`.
2. Annotate reasoning spans with the manual tool and save them under `annotated_cases/`.
3. Use the comparison tool to inspect span alignment, label agreement, and annotation drift.
4. Run the LLM jury on the human cases to generate machine annotations (`jury_output/`).
5. Run the LLM generation pipeline to produce model-written differential diagnoses (`cases_llm/`).
6. Run the LLM jury on the generated cases to annotate LLM reasoning (`jury_output_llm/`).
7. Compare human and machine annotations using the same viewer and JSON schema.

The important design choice is that the annotation target is the reasoning trace itself. The project therefore captures not only what diagnosis was reached, but how the reasoning unfolded — and now compares that unfolding across both human physicians and LLMs.

## Repository Layout

- `cases/` — original clinical case texts (human physician reasoning)
- `cases_llm/` — LLM-generated differential diagnoses, one subfolder per case with one `.md` per generation model
- `annotated_cases/` — manually annotated JSON files
- `annotation_tool/` — human labeling UI
- `comparison_tool/` — multi-file comparison viewer
- `jury/` — automated LLM annotation pipeline
- `jury_output/` — jury results for human cases (`{case}/{case}_Judge*.json`)
- `jury_output_llm/` — jury results for LLM-generated cases (`{case}/{model}/{case}_Judge*.json`)
- `llm_generation/` — pipeline that generates the differential diagnoses in `cases_llm/`
- `docs/` — implementation notes for each module
- `appendix_ref8/` — source CSV associated with the Hom et al. dataset

## Quick Start

Set `NVIDIA_API_KEY` in `.env` before running the jury pipeline.

```bash
# Human annotation UI
cd annotation_tool && uv run python server.py

# Comparison viewer
cd comparison_tool && uv run python server.py

# Generate LLM differential diagnoses for all cases
uv run python -m llm_generation.run_generation cases/*.md

# Jury — smoke test on one human case (3 voters)
uv run python -m jury.run_jury --dry-run "cases/2003 Case 21.md"

# Jury — full batch run on human cases
uv run python -m jury.run_jury cases/*.md

# Jury — smoke test on one LLM case directory (3 voters, all 3 models)
uv run python -m jury.run_jury --llm --dry-run --output-dir jury_output_llm "cases_llm/2003 Case 21"

# Jury — full batch run on all LLM cases
uv run python -m jury.run_jury --llm --output-dir jury_output_llm cases_llm/*
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


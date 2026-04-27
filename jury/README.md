# LLM Jury — Documentation

## Overview

The LLM Jury is an automated annotation system that classifies clinical reasoning spans in NEJM case discussion texts. It replicates the manual annotation process by running multiple independent LLM voters on each document and collecting their outputs in the same JSON format used by human annotators.

The core idea is simple: instead of asking one model to annotate a document (which would give a single, potentially unreliable output), we ask **15 independent voters** and collect all of their responses. This exploits the **Condorcet Jury Theorem**: if each voter has an accuracy above chance, the majority vote across voters converges to a much higher accuracy than any individual voter. In practice, 15 voters with individual accuracy ≥ 0.6 gives a majority-vote accuracy above 99.9%.

The voter outputs are saved individually and will later be aggregated by a separate consensus dashboard (not part of this module).

---

## Architecture

The pipeline has five sequential stages:

```
cases/*.md
    │
    ▼
[1] Preprocessor       Strip the Presentation of Case section
    │
    ▼
[2] Prompt Builder     Inject label taxonomy + few-shot examples
    │
    ▼
[3] Jury Runner        Fire 15 concurrent API requests
    │
    ▼
[4] Offset Resolver    Map quoted text → character offsets in source file
    │
    ▼
[5] Writer             Save per-voter JSON + summary
```

---

## Stage 1 — Preprocessor (`preprocessor.py`)

Each case file is a markdown document with two parts: a **Presentation of Case** (pure factual patient history) and a **reasoning section** (expert discussion starting at `## Differential Diagnosis`).

Only the reasoning section is annotated. The preprocessor identifies where the PoC ends by searching for the first `##` heading that is not `## Presentation of Case`, and splits the document there.

It returns three things: the full document text, the reasoning-only text, and the character offset at which the reasoning section begins. This offset is critical — it allows the final annotations to reference positions in the full document, not just in the reasoning excerpt.

---

## Stage 2 — Prompt Builder (`prompt_builder.py`)

The prompt is structured as a two-message chat:

**System message** contains:
- The annotator role definition
- Instructions on what to annotate and what to skip
- The full label taxonomy: 12 labels grouped into Abduction, Deduction, and Induction, each with a one-sentence definition and concrete linguistic markers to look for
- The output format specification: a JSON array of annotation objects

**User message** contains:
- A set of few-shot examples (`_FEW_SHOT_EXAMPLES`) — real annotations from the manually annotated cases, in the exact same format as the output files
- The full reasoning section of the document to annotate
- A final instruction to copy text spans verbatim

**Key design decision:** the LLM is asked to return `label_name` and `text` only. It does **not** output character offsets (`ranges`), because an LLM has no access to the character position of a string in a file — any offsets it produced would be hallucinated. The offset resolution is handled deterministically in Stage 4.

The few-shot examples *do* include `ranges` (copied from the annotated files) so the model understands the full schema, but the instructions explicitly tell it not to output them.

---

## Stage 3 — Jury Runner (`runner.py` + `nvidia_client.py`)

The runner fires `N_VOTERS` (default: 15) independent API calls with the same prompt. Two concurrency controls are in place:

**Semaphore** — caps the number of simultaneously active requests at `CONCURRENCY_LIMIT` (40), preventing socket exhaustion.

**Token bucket** — enforces the NVIDIA Build API rate limit of 40 requests per minute. A single module-level `TokenBucket` instance is shared across all voters; each request acquires a token before firing, spacing calls by at least 1.5 seconds on average.

Each voter call uses `temperature=0.7`. This is intentional: a non-zero temperature means voters will not all produce identical outputs even from the same prompt, which is the point of having multiple voters. If temperature were 0, all 15 outputs would be the same and the jury would add no value.

Failed requests (network errors, 429s, 5xx) are retried up to 3 times with exponential backoff. If a voter exhausts all retries it is marked as `failed` and excluded from the output — the jury continues with the remaining voters rather than aborting the whole run.

---

## Stage 4 — Offset Resolver (`offset_resolver.py`)

The resolver takes each `{label_name, text}` pair returned by a voter and locates the quoted text inside the full source document to compute the character offset.

It tries two strategies in order:

1. **Exact match** — `full_text.find(span_text)`. This succeeds for the vast majority of spans, since the LLM is instructed to copy text verbatim.

2. **Fuzzy match** — if the exact match fails (the model slightly misquoted or truncated the span), `rapidfuzz` is used to find the closest matching window in the source text. A match is accepted only if the similarity score is ≥ 90 out of 100.

If neither strategy finds a match above the threshold, the span is flagged as `unresolved` and excluded from the voter's output. It is recorded in the summary file for inspection. Critically, **no offset is ever hallucinated** — an unresolved span is simply dropped rather than assigned a wrong position.

---

## Stage 5 — Writer (`writer.py`)

For each voter, the writer produces one JSON file in `jury_output/{case_stem}/`:

```
jury_output/
└── 2003_Case_21/
    ├── 2003_Case_21_Judge001.json
    ├── 2003_Case_21_Judge002.json
    ├── ...
    ├── 2003_Case_21_Judge015.json
    └── 2003_Case_21_jury_summary.json
```

Each per-voter file is schema-identical to the manual annotation files:

```json
{
  "case": "2003 Case 21.md",
  "annotator": "Judge001",
  "exported_at": "2026-04-27T...",
  "annotations": [
    {
      "ranges": [[11969, 12052]],
      "label": 4,
      "label_name": "ABD_CAUSAL",
      "text": "Dysarthria, nasal speech, diplopia, and vertigo all suggest brain-stem dysfunction."
    }
  ]
}
```

The summary file records how many voters succeeded, how many failed, and the list of unresolved spans per voter — useful for diagnosing prompt quality issues.

---

## Running the System

```bash
# Set your API key (or add it to .env)
export NVIDIA_API_KEY=your_key_here

# Dry run — 3 voters only, to validate the pipeline cheaply
uv run python -m jury.run_jury --dry-run "cases/2003 Case 21.md"

# Full run — 15 voters on one case
uv run python -m jury.run_jury "cases/2003 Case 21.md"

# Batch run on multiple cases
uv run python -m jury.run_jury cases/*.md

# Override voter count
uv run python -m jury.run_jury --voters 5 "cases/2003 Case 21.md"
```

---

## Configuration

All parameters live in `jury/config.py` and can be overridden via environment variables or the `.env` file:

| Variable | Default | Description |
|---|---|---|
| `NVIDIA_API_KEY` | — | API key (required) |
| `NVIDIA_MODEL` | `meta/llama-3.3-70b-instruct` | Model name |
| `N_VOTERS` | `15` | Voters per document |
| `FUZZY_MATCH_THRESHOLD` | `90` | Minimum rapidfuzz score for offset resolution |

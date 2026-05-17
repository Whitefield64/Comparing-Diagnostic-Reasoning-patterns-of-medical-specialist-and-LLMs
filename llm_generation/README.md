# LLM Differential Diagnosis Generation

This module generates LLM-written differential diagnosis sections from source case presentations.

The pipeline gives each model only the `## Presentation of Case` section, then writes a new markdown case under `cases_llm/` with the original title, the original presentation, and a generated `## Differential Diagnosis` section.

The model is instructed to return only the generated reasoning section. The copied title and presentation in each output file are added by the local writer so downstream jury annotation can read a complete case-like markdown file.

## Configuration

Set the NVIDIA key in `.env` as already used by the jury pipeline.

Optional generation settings:

```bash
GENERATION_MODELS=meta/llama-3.3-70b-instruct,qwen/qwen3-next-80b-a3b-instruct,openai/gpt-oss-120b
GENERATION_TEMPERATURE=0.7
GENERATION_MAX_TOKENS=8192
GENERATION_MIN_WORDS=1400
GENERATION_EXPANSION_ATTEMPTS=1
GENERATION_OUTPUT_DIR=cases_llm
```

If `GENERATION_MODELS` is not set, the module falls back to `NVIDIA_MODEL`.

## Usage

One-case smoke test:

```bash
uv run python -m llm_generation.run_generation --dry-run "cases/2003 Case 39.md"
```

One case with three explicitly selected models:

```bash
uv run python -m llm_generation.run_generation \
  --models meta/llama-3.3-70b-instruct,qwen/qwen3-next-80b-a3b-instruct,openai/gpt-oss-120b \
  "cases/2003 Case 39.md"
```

Several catalog-listed alternatives were not practical in the smoke test: `mistralai/mixtral-8x22b-instruct-v0.1` repeatedly returned shorter outputs, `google/gemma-4-31b-it` and `deepseek-ai/deepseek-v4-pro` timed out on long-form generation, and the available Palmyra/Jamba endpoints returned account-level 404 errors.

Full run:

```bash
uv run python -m llm_generation.run_generation cases/*.md
```

Existing generations are skipped unless `--overwrite` is passed.

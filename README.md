# NLP Business

Project for comparing human and LLM clinical reasoning on CPC-style cases.

## Test

Set `NVIDIA_API_KEY` in `.env` before running the jury pipeline.

- `cd annotation_tool && uv run python server.py` opens the annotation tool on `http://localhost:5001`.
- `cd comparison_tool && uv run python server.py` opens the comparison tool on `http://localhost:5002`.
- `uv run python -m jury.run_jury --dry-run "cases/2003 Case 21.md"` runs a cheap end-to-end jury check.


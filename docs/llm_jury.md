# LLM Jury Guide

The LLM jury is the automated annotation pipeline. It runs multiple independent model voters on the same case, resolves their quoted spans back to character offsets, and writes the results in the same JSON format used by human annotators.

The current defaults are 15 voters, temperature `0.7`, a 40 requests-per-minute rate limit, and output under `jury_output/`.

## What It Does

The pipeline:

1. Loads a case from `cases/`.
2. Removes the Presentation of Case section.
3. Builds a prompt with the label taxonomy and few-shot examples.
4. Sends the prompt to multiple voters.
5. Resolves each returned text span to offsets in the original document.
6. Writes one JSON file per voter plus a summary file.

## How It Works

The entry point is `jury/run_jury.py`.

### Case preprocessing

`jury/preprocessor.py` finds the first heading after `## Presentation of Case` and treats that as the start of the reasoning section. The full text is kept, but the prompt only sees the reasoning portion.

### Prompt construction

`jury/prompt_builder.py` creates:

- a system message with the 12-label taxonomy
- a user message with a few-shot block and the document text

The model is instructed to return only `label_name` and verbatim `text`, not offsets.

### Voting

`jury/runner.py` executes several independent requests with the same prompt. Temperature is non-zero so the voters can produce different outputs, which is the point of using a jury rather than a single model call.

The pipeline is rate-limited and retries failed requests so that one bad call does not abort the whole case.

### Offset resolution

`jury/offset_resolver.py` maps each returned quote back to the source document.

It tries:

1. Exact string matching.
2. Fuzzy matching with `rapidfuzz` when the quote is slightly imperfect.

If a span cannot be located confidently, it is marked unresolved rather than guessed (This part can be improved).

### Writing results

`jury/writer.py` writes:

- one JSON file per successful voter
- one summary JSON file with success/failure counts and unresolved spans

The output files use the same shape as manual annotations, so they can be loaded into the comparison tool without special handling.

## Practical Use

Use the jury pipeline when you want to benchmark the labeling prompt, generate larger batches of machine annotations, or compare model reasoning traces against human reasoning traces.
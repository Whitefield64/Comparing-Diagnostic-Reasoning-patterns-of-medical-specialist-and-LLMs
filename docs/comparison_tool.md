# Comparison Tool Guide

The comparison tool is a read-only viewer for annotation JSON files. It is used to inspect multiple annotators or multiple runs against the same case text and to compare span placement and label agreement.

It listens on port `5002`.

## What It Does

The tool lets you:

1. Load one or more annotation JSON files.
2. Fetch the matching case text from `cases/` through the local backend.
3. Overlay the annotations on the source document.
4. Inspect disagreement in a detail panel.
5. Remove loaded files and reload new ones.

## How It Works

The app is a lightweight Flask server in `comparison_tool/server.py` plus a browser UI in `comparison_tool/static/app.js`.

### Case text loading

When a JSON file is loaded, the tool reads the `case` field and requests the matching text from `/api/text`. The server looks for the case in `cases/` and serves the raw markdown text.

Only annotation files for the same case can be compared together. If a loaded file belongs to a different case, it is skipped.

### Rendering annotations

The viewer breaks the case text into segments based on all span boundaries from the loaded annotation files. Each segment is then styled according to the label frequency across the loaded files.

The visual result is a stacked underline style:

- one color layer per dominant label
- up to three visible layers in the main span style (if moore than 3 are present, only the top 3 most frequent are shown)
- a consensus highlight in grey when vote thresholds are met (see Configuration to undestand consensus)

### Detail inspection

Clicking a text region opens a detail panel that shows:

- the total number of covers on that span
- the label distribution across annotators
- the individual JSON objects that contributed to that region

This makes it useful for finding span boundary drift, label disagreements, and annotation noise.

### Persistent state

The tool remembers loaded files in browser `localStorage`, so a comparison session can be restored after refresh.

## Configuration

Consensus behavior comes from `comparison_tool/config.json`:

- `consensus_min_votes`
- `consensus_min_agreement`

These values control when a span is marked as consensus rather than just visually aggregated.

The current defaults are `5` votes and `0.5` agreement.

## Practical Use

Use this tool to compare human annotators, compare jury runs, and check whether the exported annotations match the intended case before moving on to analysis.
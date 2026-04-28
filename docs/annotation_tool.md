# Annotation Tool Guide

The annotation tool is the human labeling interface for the project. It runs as a local Flask app and is designed to create span-level JSON annotations for the clinical reasoning section of each case.

It listens on port `5001`.

## What It Does

The tool lets an annotator:

1. Load a case file from `cases/`.
2. Enter an annotator name.
3. Pick one of the 12 epistemic labels.
4. Select spans directly in the document.
5. Export the annotations as JSON.
6. Import another annotator's JSON for visual comparison.

## How It Works

The UI is implemented in `annotation_tool/static/app.js` and rendered by `annotation_tool/templates/index.html`.

### Case loading

The case is loaded from a local `.md` or `.txt` file. The tool normalizes line endings, stores the file content in browser `localStorage`, and remembers the last case and annotator name.

### Label selection

The palette contains the 12 labels grouped into Abduction, Deduction, and Induction. Clicking a label makes it active; clicking it again clears the selection.

### Span creation

When the user highlights text in the reasoning section, the tool computes absolute character offsets inside the raw file and stores an annotation object with:

- `start`
- `end`
- `label`
- `label_name`
- `text`

The Presentation of Case section is treated as non-annotatable. Overlapping spans are rejected.

### Saving and exporting

Annotations are autosaved in `localStorage` while the session is open. Export creates a JSON file named after the case and annotator, using the shared project schema.

### Comparison inside the annotation tool

The import button loads another JSON file and overlays it as a comparison layer. Imported spans appear as read-only dashed underlines, with a separate card list in the right panel. A clear button removes the imported comparison layer.

### Merge support

The right panel also supports selecting up to two spans from the same annotator and merging them into a multi-part annotation. This is mainly useful when the annotator wants to combine adjacent or related spans after review.

## Output Format

The exported JSON structure matches the format used by the rest of the project:

```json
{
  "case": "2003 Case 21.md",
  "annotator": "matteo",
  "exported_at": "2026-04-20T14:32:00Z",
  "annotations": [
    {
      "ranges": [[15808, 15842]],
      "label": 4,
      "label_name": "ABD_CAUSAL",
      "text": "Artery-to-artery emboli are likely..."
    }
  ]
}
```

## Practical Use

Use this tool when you want to create or refine human annotations that will later serve as few-shot examples, gold references, or comparison targets for LLM output.
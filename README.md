# Epistemic Reasoning Annotation Project

This project annotates clinical reasoning spans in NEJM Case Records of the Massachusetts General Hospital (CPC cases) with 12 epistemic labels across three reasoning modes: Abduction, Induction, and Deduction.

---

## Project Structure

```
NLP_business/
├── cases/                      # Case files (markdown, one per case)
│   ├── 2003 Case 21.md
│   └── 2016 Case 25.md
├── annotation_tool/            # Local annotation web app
│   ├── server.py               # Flask backend
│   ├── pyproject.toml          # Python dependencies (managed by uv)
│   ├── uv.lock
│   ├── templates/
│   │   └── index.html
│   └── static/
│       ├── style.css
│       └── app.js
├── docs/                       # Project documentation
└── README.md
```

---

## Prerequisites

You need **Python 3.12+** and **uv** installed.

### Install uv (if not already installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify:

```bash
uv --version
```

---

## Setup

1. **Clone or download the project** to your local machine.

2. **Add case files** to the `cases/` directory. Each case must be a `.md` file. The tool automatically discovers all `.md` files in that folder.  
   The case files are not included in the repository (excluded via `.gitignore`). Obtain them from the professor or your research supervisor.

3. **Install dependencies** for the annotation tool:

   ```bash
   cd annotation_tool
   uv sync
   ```

   This creates a local `.venv` and installs Flask. No other packages are needed.

---

## Running the Annotation Tool

From inside the `annotation_tool/` directory:

```bash
uv run python server.py
```

Then open your browser and navigate to:

```
http://localhost:5001
```

> **Note:** Port 5000 is reserved by macOS AirPlay Receiver. The tool runs on 5001.

---

## Using the Tool

### 1. Load a case

Select a case from the **Case** dropdown in the top-left corner. The full document will appear in the left panel.

### 2. Enter your name

Type your name in the **Annotator** field. This is used to identify your annotations in exported files and when comparing with other annotators. You must enter a name before annotating.

### 3. Select a label

Click one of the 12 colored label buttons in the palette bar:

| Group | # | Code | Color |
|---|---|---|---|
| **ABD** (Abduction) | 1 | ABD_SELECTIVE | Red |
| | 2 | ABD_CREATIVE | Coral |
| | 3 | ABD_CAUSAL | Orange |
| | 4 | ABD_VISUAL | Amber |
| **IND** (Induction) | 5 | IND_PATTERN | Green |
| | 6 | IND_INTUITION | Teal |
| | 7 | IND_BAYESIAN | Sky blue |
| | 8 | IND_CASEBASED | Blue |
| **DED** (Deduction) | 9 | DED_HYPOTHETICO | Lavender |
| | 10 | DED_ALGORITHMIC | Violet |
| | 11 | DED_HIERARCHICAL | Indigo |
| | 12 | DED_VALIDATION | Deep indigo |

The active label is shown on the right side of the palette. Click the same button again to deselect.

### 4. Annotate text

Select any span of text in the document with your mouse. The span is immediately highlighted in the label's color and an annotation card appears in the right panel.

**Rules:**
- The **Presentation of Case** section is grayed out and cannot be annotated — it contains clinical facts, not reasoning.
- Annotations cannot overlap. If your selection overlaps an existing annotation, a warning appears and the selection is discarded. Delete the existing annotation first.
- One primary label per span.

### 5. Delete an annotation

Two ways:
- **Click on highlighted text** in the document → a popup appears with a Delete button.
- **Click the × button** on an annotation card in the right panel.

### 6. Save and export

Your annotations are **auto-saved** in the browser's localStorage as you work. If you close the browser and reopen the tool with the same case and annotator name, you will be offered the option to resume your previous session.

When finished, click **Export JSON** to download your annotations as a file named `<case>_<name>.json`.

### 7. Compare with another annotator

Click **Import JSON** and select another annotator's exported file. Their annotations will appear as **dashed underlines** in the document (same colors, no solid fill) and as read-only cards in the right panel labelled with their name. A summary line at the top of the panel shows both annotator span counts. Click **✕ Clear comparison** to remove the imported annotations.

---

## Annotation Output Format

Exported files follow this structure:

```json
{
  "case": "2003 Case 21.md",
  "annotator": "matteo",
  "exported_at": "2026-04-20T14:32:00",
  "annotations": [
    {
      "id": "a1",
      "start": 15808,
      "end": 15842,
      "label": 3,
      "label_name": "ABD_CAUSAL",
      "text": "Artery-to-artery emboli are likely"
    }
  ]
}
```

- `start` / `end`: character offsets in the raw `.md` file (0-indexed). `rawText.slice(start, end)` always returns exactly the annotated text.
- `label`: integer 1–12.
- `label_name`: human-readable code.
- `text`: the annotated text snippet (stored for convenience; always redundant with `start`/`end`).

---

## Stopping the Server

Press `Ctrl+C` in the terminal where the server is running.

---

## Troubleshooting

**The case dropdown is empty.**  
Check that `.md` files are present in `cases/` at the project root (one level above `annotation_tool/`).

**"Address already in use" error.**  
Another process is using port 5001. Either kill it (`lsof -ti:5001 | xargs kill`) or change the port in `annotation_tool/server.py` (last line).

**My previous annotations are gone after reloading.**  
Annotations are stored in the browser's localStorage, which is scoped to the browser and device. Use the same browser you annotated with. If you cleared your browser data, the annotations are gone — export regularly.

**The PoC section extends further than expected / my annotation was rejected.**  
The tool detects the PoC section by scanning for the `## Presentation of Case` header and treating everything up to the next `##` header as non-annotatable. If the case file has an unusual header structure, this boundary may shift.

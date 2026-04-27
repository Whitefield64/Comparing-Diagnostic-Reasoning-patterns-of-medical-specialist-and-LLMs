"""
Build the system prompt and user message for a jury voter.

The LLM must return ONLY a JSON array of annotation objects.
It must NOT output character offsets — only the verbatim quoted text.
The offset_resolver will compute positions from the source file.
"""

import json

_SYSTEM_PROMPT = """\
You are an expert annotator of clinical reasoning in medical case discussions.
Your task is to identify and label spans of text in a physician's diagnostic reasoning discussion.

## What to annotate

Annotate ONLY the reasoning/discussion section of the case (after the Presentation of Case).
Do NOT annotate pure factual statements of symptoms, test results, or patient history.
Annotate spans where a physician is actively reasoning — generating hypotheses, testing them, or drawing probabilistic conclusions.

A single sentence or paragraph may contain only ONE reasoning type. Choose the best-fitting label.
Spans should be as tight as possible — include only the reasoning-bearing text, not surrounding narrative.

## Label taxonomy (12 primary labels)

### ABDUCTION — hypothesis generation
- **ABD_SELECTIVE**: The clinician selects the best-fitting diagnosis from a known set of candidates already in their repertoire. Look for: "the most likely", "best explains", "fits with", listing differentials and narrowing down.
- **ABD_CREATIVE**: The clinician proposes a novel or atypical hypothesis not commonly considered. Look for: rare diseases, unusual presentations, "another disease to consider", "though uncommon".
- **ABD_VISUAL**: A hypothesis is triggered by direct sensory perception — what is seen, heard, or felt on examination. Look for: physical exam findings that directly suggest a diagnosis (skin findings, auscultation, palpation).
- **ABD_CAUSAL**: The clinician reasons backward from symptoms/findings to the underlying pathophysiological mechanism. Look for: "this symptom is caused by", "because of X, the mechanism is Y", explaining WHY something happened.

### DEDUCTION — hypothesis testing
- **DED_HYPOTHETICO**: "If hypothesis H is true, then finding F should be present" — the clinician deduces what should be found and checks against data. Look for: "if this were X, we would expect to see Y", "this diagnosis requires Z".
- **DED_ALGORITHMIC**: The clinician mechanically applies a codified clinical guideline, protocol, or scoring system. Look for: explicit criteria, staging systems, diagnostic criteria (e.g., Duke criteria, ROME criteria).
- **DED_HIERARCHICAL**: The clinician prioritizes life-threatening diagnoses first before moving to less serious ones. Look for: "we must first rule out", "the most dangerous explanation is", "before considering X, we must exclude Y".
- **DED_VALIDATION**: The clinician retrospectively checks coherence — reviewing whether all data fit the working diagnosis. Look for: "this is consistent with", "all findings fit", "this explains why", summarizing evidence for a diagnosis already reached.

### INDUCTION — probabilistic conclusion
- **IND_PATTERN**: Rapid illness-script matching — the clinician recognizes a pattern that instantly recalls a disease. Look for: "the classic presentation of", "this is the typical picture of", "immediately suggests".
- **IND_INTUITION**: Pre-analytic affective signal — a gut feeling or clinical instinct before formal analysis. Look for: "something about this case concerns me", "this doesn't feel right", "my instinct is".
- **IND_BAYESIAN**: Explicit probabilistic updating — the clinician adjusts probability estimates given new evidence. Look for: "this raises/lowers the probability of", "more likely given", "prior probability", percentages or odds.
- **IND_CASEBASED**: The clinician retrieves an analogous prior case and adapts reasoning from it. Look for: "I recall a similar patient", "this reminds me of", "in my experience with cases like this".

## Output format

Return ONLY a valid JSON array. Each element must have exactly these fields:
- "label_name": one of the 12 labels above (string)
- "text": the EXACT verbatim text span from the document (string) — copy it character-for-character including punctuation and markdown formatting

Do not include any explanation, preamble, or text outside the JSON array.
If no reasoning spans are found, return an empty array: []

Example output:
[
  {
    "label_name": "ABD_CAUSAL",
    "text": "Dysarthria, nasal speech, diplopia, and vertigo all suggest brain-stem dysfunction."
  },
  {
    "label_name": "IND_BAYESIAN",
    "text": "Although this elderly, hypertensive man probably did have some atheromatous disease, the vessels involved and the laboratory evidence suggest that he had giant-cell arteritis."
  }
]
"""

_FEW_SHOT_EXAMPLES = [
    {
        "ranges": [[11969, 12052]],
        "label": 4,
        "label_name": "ABD_CAUSAL",
        "text": "Dysarthria, nasal speech, diplopia, and vertigo all suggest brain-stem dysfunction.",
    },
    {
        "ranges": [[13961, 14103]],
        "label": 5,
        "label_name": "DED_HYPOTHETICO",
        "text": "The most common disease involving both the large and small vessels is atherosclerosis, and for that reason, anticoagulation therapy was begun.",
    },
    {
        "ranges": [[22881, 22990]],
        "label": 9,
        "label_name": "IND_PATTERN",
        "text": "The pattern matches the description by Wilkinson and Russell in their classic review of giant-cell arteritis.",
    },
    {
        "ranges": [[23460, 23657]],
        "label": 11,
        "label_name": "IND_BAYESIAN",
        "text": "Although most cases of giant-cell arteritis involve the temporal artery (in what is called temporal arteritis), involvement of the larger arteries has been reported in about 10 percent of patients.",
    },
]


def build_messages(reasoning_text: str) -> list[dict]:
    """
    Returns the messages list for the chat completion API.
    The system prompt contains the taxonomy and output format.
    The user turn contains the few-shot examples followed by the document to annotate.
    """
    examples_json = json.dumps(_FEW_SHOT_EXAMPLES, indent=2)

    user_content = (
        "Below are example annotations. "
        "The 'ranges' field shows character offsets in the source file — "
        "you do NOT need to output ranges, they will be computed automatically.\n\n"
        f"EXAMPLES:\n{examples_json}\n\n"
        "--- Now annotate the following document ---\n"
        f"DOCUMENT:\n{reasoning_text}\n\n"
        "Return ONLY the JSON array of annotations. "
        "Copy text spans EXACTLY as they appear in the document above."
    )

    return [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

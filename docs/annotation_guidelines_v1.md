# Annotation Guidelines v1.0
## Epistemic Reasoning in Clinical Diagnosis — Span Annotation

**Project:** Comparing Diagnostic Reasoning Patterns of Medical Specialists and LLMs
**Version:** 1.0 — to be updated after each IAA calibration round
**Annotation tool:** Label Studio (local instance)
**Target IAA:** Cohen's κ ≥ 0.75, Krippendorff's α ≥ 0.70

---

## 1. What You Are Annotating

You will annotate **differential diagnosis (DDx) sections** from NEJM Clinical Pathological Conference cases. Each DDx section is the reasoning trace of an expert clinician working through a complex case in real time, without knowing the final diagnosis.

Your task: tag each reasoning **span** (typically 1–3 sentences) with a **primary label** from the 14-category schema below, plus optional secondary labels and binary flags.

---

## 2. Annotation Unit

The annotation unit is the **shortest span of text that expresses a complete epistemic move**.

- Typically: 1–3 sentences, or a comma-separated clause if it clearly shifts reasoning mode
- **Do not** split a sentence unless a conjunction (however, but, although, yet) marks an explicit transition between modes
- **Do not** span multiple paragraphs — paragraph breaks nearly always mark a new reasoning move
- When in doubt, keep the unit larger rather than smaller (1 sentence is safer than a sub-clause)

---

## 3. Decision Flowchart

Use this tree before selecting a label:

```
Is this span generating a new hypothesis or selecting a candidate diagnosis?
    → ABDUCTION (ABD_*)

Is this span testing a hypothesis by deriving predictions from it,
or applying a rule/guideline/protocol to the patient's data?
    → DEDUCTION (DED_*)

Is this span drawing a conclusion from accumulated evidence, experience,
or probabilistic reasoning — rather than generating or testing a specific hypothesis?
    → INDUCTION (IND_*)

Is this span neither generating, testing, nor concluding — but rather
exploring possibilities broadly, or translating the case data into a
diagnostic frame before any hypothesis is formed?
    → PRE-ABDUCTIVE (PRE_*)
```

If still unsure after the flowchart, use the **signal checklists** for each label below.

---

## 4. Primary Label Definitions

### 4.1 Abduction Subtypes

---

#### `ABD_SELECTIVE` — Selective Abduction
**Definition:** Identifying the best-fitting diagnosis from a pre-existing set of known disease candidates. This is differential narrowing — the clinician has multiple options in mind and selects the most fitting.

**Linguistic signals:**
- "most likely", "best fits", "most consistent with", "favors", "suggests"
- Comparative language: "X is more likely than Y because..."
- Ranking or ordering of known candidates

**Positive examples:**
1. *"Of the diagnoses on my differential, sarcoidosis best fits this picture — the bilateral hilar adenopathy, the hypercalcemia, and the cutaneous involvement together form a classic triad."*
2. *"Given the combination of fever, rash, and arthralgias in this young woman, systemic lupus erythematosus is the most consistent diagnosis."*
3. *"Between the infectious and rheumatologic possibilities, the clinical timeline and response to steroids favors an autoimmune etiology."*

**Negative examples (things that look like this but are NOT):**
1. *"The patient may have pulmonary embolism, pneumonia, or a pleural effusion."* → This is `PRE_MUSEMENT` — listing possibilities without selecting.
2. *"If this is sarcoidosis, we would expect ACE levels to be elevated."* → This is `DED_HYPOTHETICO` — deriving a prediction from a hypothesis.
3. *"I've seen this pattern before in a patient with Wegener's granulomatosis."* → This is `IND_CASEBASED` — using a prior case.

**Boundary cases:**
- *"The chest imaging is most consistent with lymphoma, though sarcoidosis cannot be excluded."* → Label `ABD_SELECTIVE`. The primary move is selecting lymphoma; the hedge does not change the epistemic category.
- *"While the presentation fits sarcoidosis, the absence of uveitis makes me less certain."* → Label `ABD_SELECTIVE` AND flag `NONMONOTONIC` if this represents a revision of a prior hypothesis.

---

#### `ABD_CREATIVE` — Creative Abduction
**Definition:** Generating a genuinely novel hypothesis not previously in the clinician's repertoire, essential for rare or atypical presentations where standard candidates do not fit.

**Linguistic signals:**
- "doesn't fit any of the standard diagnoses"
- "could this be X?" where X is unusual or rarely named
- "I have never encountered this pattern"
- Tentative, exploratory language about mechanisms that aren't named diseases
- Discovery framing: "What if...?", "Could there be a unifying diagnosis...?"

**Positive examples:**
1. *"None of the usual suspects explain the combination of progressive weakness, weight loss, and this peculiar rash — I wonder whether we're looking at an unrecognized paraneoplastic syndrome."*
2. *"The pattern is so unusual that I'm reluctant to force it into an existing category; this may represent a new variant of the syndrome rather than a classic presentation."*
3. *"Could this be a previously undescribed toxin-mediated neuropathy related to the patient's occupational exposure?"*

**Negative examples:**
1. *"I'm considering a rare diagnosis: Whipple's disease."* → This is `ABD_SELECTIVE` — Whipple's is a known, named disease being selected from a differential, even if uncommon.
2. *"The presentation doesn't fit typical TB."* → This alone is a `NEGATIVE_FACT` flag marker, not creative abduction.
3. *"This is an unusual case."* → Generic acknowledgment, not a hypothesis generation. Label as `PRE_MUSEMENT`.

**Note:** `ABD_CREATIVE` is rare in the corpus. Do not inflate it by labeling any mention of a rare disease as creative.

---

#### `ABD_CAUSAL` — Causal Abduction
**Definition:** Reasoning backward from an observed outcome or symptom cluster to identify the underlying pathophysiological mechanism that could produce it.

**Linguistic signals:**
- "would explain why", "underlying mechanism", "secondary to"
- "this is driven by", "the cause of X is likely Y"
- Pathophysiological chains: "→ leading to", "→ resulting in"
- "working backward from", "the pathophysiology here"

**Positive examples:**
1. *"The constellation of edema, hypoalbuminemia, and proteinuria suggests a mechanism of glomerular protein loss — most likely a nephrotic process rather than a production deficit."*
2. *"Working backward: if the renal failure is causing the anemia, we would expect normocytic red cells and low erythropoietin — which fits the lab picture."*
3. *"The encephalopathy here is most plausibly explained by hyperammonemia secondary to hepatic synthetic failure, rather than a primary neurological process."*

**Negative examples:**
1. *"The diagnosis is hepatic encephalopathy."* → This is `ABD_SELECTIVE` — selecting a diagnosis, not reasoning backward to a mechanism.
2. *"If this is liver failure, LFTs should be elevated."* → This is `DED_HYPOTHETICO` — deriving predictions.
3. *"Liver failure causes hyperammonemia."* → This is a factual statement used as background, not an active reasoning move. Context determines whether it's part of a causal abduction.

---

#### `ABD_VISUAL` — Visual / Manipulative Abduction
**Definition:** A hypothesis triggered by direct sensory engagement with the patient (sight, touch, sound, smell) before formal analysis, or by the epistemic act of choosing what to do/test (manipulative).

**Linguistic signals:**
- "on examination...", "on auscultation...", "appearance of..."
- "immediately suggested", "caught my eye", "gestalt"
- Procedure selection with explicit epistemic justification (why THIS test or biopsy site)
- Perceptual triggers: *"the skin lesion pattern immediately brought to mind..."*

**Positive examples:**
1. *"On examination, the violaceous, undermined borders of the ulcer immediately suggested pyoderma gangrenosum before any further analysis."*
2. *"The fixed, stony-hard consistency of the lymph node on palpation triggered an immediate concern for malignancy."*
3. *"I chose to biopsy the edge of the lesion rather than the center specifically to capture the active interface — a choice that would distinguish between the two leading diagnoses."*

**Positive examples (manipulative):**
4. *"Ordering a Giemsa stain rather than a standard H&E was a deliberate epistemic choice — only Giemsa would reveal Leishmania amastigotes if our revised hypothesis was correct."*

**Note:** In text-only DDx sections, `ABD_VISUAL` will always be mediated through language. Look for perceptual language describing the physical encounter. This label will be rare.

---

### 4.2 Deduction Subtypes

---

#### `DED_HYPOTHETICO` — Hypothetico-Deductive Reasoning
**Definition:** Classical hypothesis testing: "If diagnosis H is true, then finding F should/should not be present." The clinician derives a prediction from a hypothesis and checks it against data.

**Linguistic signals:**
- "if this is X, we would expect...", "should show", "should be present"
- "X predicts Y", "consistent with our hypothesis"
- "this would/would not be expected if..."

**Positive examples:**
1. *"If this were an immune-mediated process, we would expect a response to corticosteroids — which the patient did not show, arguing against autoimmunity."*
2. *"Tuberculosis would predict positive AFB smears and cavitary lesions on imaging; neither is present."*
3. *"If the valve is regurgitant, we should hear a decrescendo diastolic murmur — let me check that against the examination findings."*

**Negative examples:**
1. *"Tuberculosis is common in this population."* → Background prevalence statement, `IND_BAYESIAN`.
2. *"The patient has fever, which is consistent with infection."* → Pattern match, `IND_PATTERN`.
3. *"We should rule out PE first given the risk."* → Hierarchical prioritization, `DED_HIERARCHICAL`.

---

#### `DED_ALGORITHMIC` — Algorithmic / Rule-Based Deduction
**Definition:** Applying a pre-determined, codified clinical decision rule or evidence-based guideline mechanically to patient data.

**Linguistic signals:**
- "per guidelines", "by criteria", "score", "algorithm"
- Named criteria: "Wells criteria", "CURB-65", "Duke criteria", "Rome criteria"
- "meets criteria for", "by definition", "according to..."

**Positive examples:**
1. *"By the modified Duke criteria, this patient has two major criteria (positive blood cultures and echocardiographic vegetation) and therefore a definite diagnosis of infective endocarditis."*
2. *"Applying the Wells score — the patient scores 6, placing him in the high probability category for pulmonary embolism."*
3. *"By AHA guidelines, this level of troponin elevation combined with EKG changes meets the threshold for Type 1 MI."*

**Negative examples:**
1. *"Endocarditis is on my differential."* → `ABD_SELECTIVE` — hypothesis generation.
2. *"The fever and murmur together raise concern for endocarditis."* → `IND_PATTERN` — pattern recognition.

---

#### `DED_HIERARCHICAL` — Hierarchical Deduction
**Definition:** Organizing competing diagnoses by clinical priority — life-threatening conditions first, then most likely common conditions — and systematically excluding them in order of urgency.

**Linguistic signals:**
- "first and foremost", "most urgent", "must rule out", "before we consider"
- "de-prioritize", "move to the next", "exclude first"
- Explicit urgency ranking: "life-threatening → serious → common"

**Positive examples:**
1. *"Before entertaining any chronic diagnosis, we must first exclude pulmonary embolism — this patient has several Virchow's triad risk factors and the acute presentation makes this an urgent priority."*
2. *"The first thing to rule out in this chest pain presentation is aortic dissection; the normal d-dimer and blood pressure symmetry make this less likely, and we can move on."*
3. *"I'm going to work from the most dangerous to the most treatable: STEMI first, then unstable angina, then demand ischemia."*

---

#### `DED_VALIDATION` — Validation Deduction
**Definition:** A retrospective coherence check in which the clinician re-examines whether the working diagnosis remains consistent with ALL gathered data, including previously overlooked findings.

**Linguistic signals:**
- "taken together", "all findings are consistent with", "upon reflection"
- "revisiting", "looking back", "this diagnosis explains all the findings"
- "no finding contradicts", "the full picture supports"
- End-of-reasoning synthesis

**Positive examples:**
1. *"Taken together, the travel history, the eosinophilia, the hepatosplenomegaly, and the serological results are all consistent with visceral leishmaniasis — no finding in the case contradicts this diagnosis."*
2. *"Upon reflection, every element of the presentation fits the picture of systemic amyloidosis: the cardiac dysfunction, the peripheral neuropathy, the proteinuria, and the macroglossia."*
3. *"Revisiting the initial labs with this diagnosis in mind, the mild thrombocytopenia and the elevated fibrinogen now make sense as part of the same process."*

**Note:** `DED_VALIDATION` typically appears near the end of a DDx section. It is the closure step of a completed ST cycle.

---

### 4.3 Induction Subtypes

---

#### `IND_PATTERN` — Pattern Recognition
**Definition:** Rapid, automatic retrieval of a stored illness script triggered by a matching symptom constellation. The clinician recognizes the case as fitting a known prototype.

**Linguistic signals:**
- "classic presentation", "typical of", "textbook", "fits the picture"
- "this pattern is", "recognizable", "prototype"
- Pattern matching without explicit reasoning: direct recognition

**Positive examples:**
1. *"This is a classic presentation of temporal arteritis: an elderly woman with new headache, jaw claudication, and an elevated ESR."*
2. *"The triad of fever, rash, and arthralgias in a young woman follows the pattern of adult-onset Still's disease."*
3. *"The combination of ascending weakness, areflexia, and albuminocytologic dissociation in the CSF is the textbook picture of Guillain-Barré syndrome."*

**Negative examples:**
1. *"This is most likely GBS."* → `ABD_SELECTIVE` — selecting from candidates; pattern recognition requires the explicit pattern-match language.
2. *"GBS causes ascending paralysis."* → Background knowledge, not a reasoning move.

---

#### `IND_INTUITION` — Clinical Intuition / Gut Feeling
**Definition:** A pre-analytic affective signal of concern or urgency that arises before formal reasoning — often prompting deeper investigation despite apparently reassuring data.

**Linguistic signals:**
- "something about this case troubles me", "I'm not comfortable with"
- "instinct", "sense that", "despite the reassuring", "alarm"
- "cannot ignore", "this bothers me"
- Explicit naming of affective response to the case

**Positive examples:**
1. *"Despite the negative initial workup, something about this patient's trajectory concerns me — the degree of functional decline seems out of proportion to the objective findings."*
2. *"My instinct here is that we're missing something serious; the reassuring labs notwithstanding, I would push for further evaluation."*
3. *"There's a level of alarm in this presentation that I can't fully articulate analytically, but would prompt me to act urgently."*

**Note:** `IND_INTUITION` is uncommon in written DDx sections (experts are reluctant to express intuition in formal writing). Do not over-label. It requires an explicit affective signal — not just any expression of uncertainty.

---

#### `IND_BAYESIAN` — Bayesian Inference
**Definition:** Formal or informal probabilistic reasoning that updates the prior probability of a disease using new evidence — test results, signs, or epidemiological data.

**Linguistic signals:**
- "increases my suspicion", "raises the probability", "base rate", "prior"
- "pre-test probability", "post-test probability", "sensitivity", "specificity"
- "given the population prevalence", "this result significantly raises"
- Narrative probability updating: "this finding makes X much more likely"

**Positive examples:**
1. *"The positive D-dimer significantly increases the post-test probability of pulmonary embolism in this intermediate pre-test risk patient."*
2. *"Given the high prevalence of tuberculosis in this population, even a modest clinical suspicion justifies empirical treatment pending cultures."*
3. *"A negative ANA essentially takes lupus off the table — the sensitivity is high enough that a negative result meaningfully lowers the probability."*

**Distinction from `ABD_SELECTIVE`:** Bayesian inference explicitly updates a probability estimate; selective abduction picks the best-fitting option without quantifying the update.

**Note on LLM traces:** Explicit Bayesian calculation with numbers (e.g., "post-test probability = 78%") in LLM traces is often confabulated. Flag `FACTUAL_ERROR` if the numbers seem implausible.

---

#### `IND_CASEBASED` — Case-Based Reasoning
**Definition:** Retrieval of one or more prior clinical cases analogous to the current patient, followed by adaptation of that case's resolution to the new context.

**Linguistic signals:**
- "I recall a patient", "similar to a case I saw", "reminds me of"
- "analogous to", "like a previous patient", "I've seen this before in"
- Specific case narrative (the Story category from Smith 2014)

**Positive examples:**
1. *"I recall a patient with a nearly identical presentation who ultimately proved to have systemic mastocytosis — a diagnosis I would not have considered without that prior experience."*
2. *"This reminds me of a case from my training where the key was the peripheral smear showing atypical lymphocytes that were initially dismissed as reactive."*
3. *"I've seen this combination of findings once before, in a case of factitious fever — the pattern of normal inflammatory markers despite subjective fever should always raise that possibility."*

---

### 4.4 Pre-Abductive Labels

---

#### `PRE_MUSEMENT` — Play of Musement
**Definition:** Speculative, exploratory thinking before any formal hypothesis is generated. The clinician is open to any possibility, brainstorming broadly without commitment.

**Linguistic signals:**
- "could range from", "broad differential", "anything from X to Y"
- "open mind", "I want to consider", "the possibilities include"
- Uncommitted listing without selection
- Pre-hypothesis preambles: "This is a complex case that could involve..."

**Positive examples:**
1. *"At first glance, this could be almost anything — a metabolic disturbance, an infectious process, a paraneoplastic phenomenon, or a primary neurological event."*
2. *"Before committing to any direction, let me acknowledge the breadth of the differential here: infectious, autoimmune, neoplastic, and toxic etiologies all remain possible."*
3. *"I want to approach this with an open mind — the presentation is genuinely multisystem and I don't want to anchor too early."*

---

#### `PRE_PROBLEMREP` — Problem Representation
**Definition:** The clinician's translation of raw case data into a concise diagnostic semantic frame — an illness script compatible summary that sets up hypothesis generation.

**Linguistic signals:**
- "In summary, we have a patient with...", "the key features are..."
- "The salient findings are...", "to summarize the presentation"
- "This is a [demographic] with [key symptoms]..."
- Semantic qualifier language: "subacute", "progressive", "bilateral", "multisystem"

**Positive examples:**
1. *"In summary, we have an elderly immunocompromised man with a subacute, progressive multisystem illness involving the lungs, skin, and central nervous system."*
2. *"The key features to explain are: bilateral hilar adenopathy, hypercalcemia, and a non-caseating granulomatous process on biopsy."*
3. *"This is a young woman with episodic symptoms — the intermittent nature is an important semantic qualifier that changes the differential."*

---

## 5. Secondary Labels (optional, multi-select)

Apply these alongside the primary label to capture discourse function:

| Code | When to apply |
|---|---|
| `STORY` | Span contains a personal patient case narrative (episodic memory) |
| `DISCONFIRMING_CUE` | Span reasons about absent or negating evidence |
| `RULE_BASED` | Span applies a guideline, protocol, or algorithm |
| `LOGIC` | Span contains formal if-then reasoning |
| `EXPERIENCE` | Span references accumulated clinical experience (no specific case) |
| `TESTS_DISCRIMINATIVE` | Span recommends/orders a test explicitly tied to distinguishing hypotheses |
| `TESTS_NONDISCRIMINATIVE` | Span recommends/orders a test without epistemic justification |

---

## 6. Binary Flags (stackable)

These can be applied to any span alongside any primary label:

| Flag | Apply when... |
|---|---|
| `NONMONOTONIC` | Span explicitly revises or retracts a prior hypothesis: *"however, this would not explain..."*, *"upon reconsideration..."*, *"treatment failure prompted me to reconsider..."* |
| `NEGATIVE_FACT` | Span reasons about what is absent: *"notably absent was X"*, *"the lack of Y argues against Z"*, *"no fever was documented"* |
| `BIAS_ANCHORING` | Clinician appears to be sticking with first hypothesis despite contradictory evidence |
| `BIAS_CONFIRMATORY` | Clinician appears to seek only confirming evidence, ignoring disconfirming |
| `BIAS_AVAILABLE` | Clinician appears to over-weight a recently discussed or memorable diagnosis |
| `BIAS_REPRESENTATIVE` | Clinician appears to rely excessively on prototype match, ignoring base rates |
| `BIAS_PREMATURE` | Clinician appears to reach a conclusion too early, without excluding alternatives |
| `FACTUAL_ERROR` | Span contains a verifiable factual error (tentative — requires expert review) |

---

## 7. Common Mistakes and How to Avoid Them

### Mistake 1: Labeling factual statements as reasoning moves
*"Sarcoidosis causes hypercalcemia through vitamin D activation."* — This is background medical knowledge presented as a fact. If the span is using this fact to reason (e.g., "this patient has hypercalcemia, which sarcoidosis causes through vitamin D activation — supporting the diagnosis"), then it is `ABD_CAUSAL` or `DED_HYPOTHETICO`. If it is a standalone fact with no argumentative function, skip it or mark as `PRE_PROBLEMREP`.

### Mistake 2: Confusing `ABD_SELECTIVE` with `IND_PATTERN`
- `ABD_SELECTIVE`: "Of the candidates, X best fits" — active selection with justification
- `IND_PATTERN`: "This is the classic presentation of X" — recognition without explicit comparison

Both may appear together. Use `ABD_SELECTIVE` when there is explicit candidate comparison; use `IND_PATTERN` when there is direct recognition language.

### Mistake 3: Over-labeling `ABD_CREATIVE`
Any mention of a rare disease is NOT creative abduction. Creative abduction requires the explicit framing that this hypothesis is outside the standard repertoire — the clinician is constructing a new explanation, not selecting from a known list that happens to include rare items.

### Mistake 4: Confusing `DED_HYPOTHETICO` with `DED_VALIDATION`
- `DED_HYPOTHETICO`: Active prospective prediction — "if X, then we should find Y" (before checking)
- `DED_VALIDATION`: Retrospective coherence check — "all findings taken together support X" (after accumulation)

Temporal marker: `DED_HYPOTHETICO` looks forward ("we would expect..."); `DED_VALIDATION` looks backward ("all of this is consistent...").

### Mistake 5: Applying `NONMONOTONIC` too liberally
`NONMONOTONIC` requires an **explicit reversal** of a prior hypothesis. Mere hedging ("X is possible but not confirmed") is not nonmonotonic. Look for explicit revision signals: "however", "upon reconsideration", "this revised my thinking", "treatment failure forced me to".

---

## 8. IAA Calibration Protocol

### How to prepare for each calibration round

1. Annotate the assigned 20 spans independently — no discussion with other annotators
2. Submit your annotations before the calibration meeting
3. At the calibration meeting: all annotators review disagreements together
4. For each disagreement: the annotator explains their reasoning; the group reaches consensus
5. The consensus label is recorded in the guidelines as a new worked example
6. After the meeting: repeat with a fresh set of 20 spans

### Thresholds

| Round | Target κ | Action if not met |
|---|---|---|
| Round 0 (baseline) | N/A — diagnostic only | Identify most-confused label pairs |
| Round 1 | ≥ 0.60 | Add examples for confused pairs |
| Round 2 | ≥ 0.70 | Refine boundary case decisions |
| Round 3 | ≥ 0.75 | Final calibration check |
| Production | ≥ 0.70 (ongoing monitoring) | Pause and recalibrate if drops below |

### What counts as a disagreement worth documenting

- Any pair of labels from different epistemic modes (e.g., one annotator says `ABD_SELECTIVE`, another says `DED_HYPOTHETICO`)
- Any disagreement on `NONMONOTONIC` or `NEGATIVE_FACT` flags
- Any disagreement on `ABD_CREATIVE` vs. `ABD_SELECTIVE`

Minor within-mode disagreements (e.g., `DED_HYPOTHETICO` vs. `DED_VALIDATION`) should be resolved by the temporal marker rule (prospective vs. retrospective).

---

## 9. Quick Reference Card

```
GENERATING a hypothesis?                    → ABD_*
  Best fit from known list                  → ABD_SELECTIVE
  Novel, outside normal repertoire          → ABD_CREATIVE
  Backward from symptoms to mechanism       → ABD_CAUSAL
  Triggered by sensory / perceptual cue     → ABD_VISUAL

TESTING a hypothesis against data?          → DED_*
  "If H then F should be present"           → DED_HYPOTHETICO
  Applying a named rule / guideline         → DED_ALGORITHMIC
  Life-threatening first, then common       → DED_HIERARCHICAL
  "Taken together, this all fits"           → DED_VALIDATION

CONCLUDING from evidence / experience?      → IND_*
  "Classic presentation of X"               → IND_PATTERN
  Affective signal of concern               → IND_INTUITION
  Probability updating                      → IND_BAYESIAN
  "I recall a similar patient..."           → IND_CASEBASED

NEITHER of the above?                       → PRE_*
  Broad exploratory brainstorming           → PRE_MUSEMENT
  Summarizing the case into a frame         → PRE_PROBLEMREP

ALWAYS CHECK FLAGS:
  Explicit revision of prior hypothesis     → NONMONOTONIC
  Reasoning about what is absent            → NEGATIVE_FACT
  Bias markers (use sparingly)              → BIAS_*
```

---

## 10. Version History

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-04-16 | Initial version — created before Round 0 calibration |
| 1.1 | TBD | Updated after Round 0–1 calibration with worked disagreement examples |
| 1.2 | TBD | Updated after Round 2–3 calibration |

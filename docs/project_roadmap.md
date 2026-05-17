# Project Roadmap: Comparing Diagnostic Reasoning Patterns in Human Clinicians and LLMs

## 1. Project Purpose

This project aims to compare the diagnostic reasoning patterns used by medical specialists and large language models (LLMs). The goal is not simply to check whether an LLM reaches the correct final diagnosis. Instead, the project studies how diagnostic reasoning unfolds: which parts of a differential diagnosis rely on abduction, deduction, or induction, and which subtypes of reasoning appear more frequently in humans versus models.

The core research idea is that diagnostic reasoning can be treated as an annotatable epistemic trace. Once that trace is labeled in a structured way, we can compare human and machine reasoning at the level of reasoning moves rather than only final answers.

The project uses clinical cases from the Hom et al. case library and focuses on the reasoning/discussion section of each case, excluding the factual Presentation of Case.

## 2. Reasoning Taxonomy

The annotation framework uses 12 labels grouped into three major epistemic modes.

### Abduction: Hypothesis Generation

Abduction captures the generation or selection of diagnostic hypotheses.

| Label | Meaning |
|---|---|
| `ABD_SELECTIVE` | Selecting the best-fitting diagnosis from known candidates. |
| `ABD_CREATIVE` | Proposing a rare, atypical, or less obvious hypothesis. |
| `ABD_VISUAL` | Forming a hypothesis from direct visual, sensory, imaging, or examination evidence. |
| `ABD_CAUSAL` | Reasoning backward from findings to a possible underlying mechanism. |

### Deduction: Hypothesis Testing

Deduction captures testing, ruling in, ruling out, or validating hypotheses.

| Label | Meaning |
|---|---|
| `DED_HYPOTHETICO` | Testing what should be true if a hypothesis is correct. |
| `DED_ALGORITHMIC` | Applying a clinical rule, guideline, criterion, or structured diagnostic procedure. |
| `DED_HIERARCHICAL` | Prioritizing diagnoses by urgency, danger, or clinical order of exclusion. |
| `DED_VALIDATION` | Retrospectively checking whether all findings fit the working diagnosis. |

### Induction: Probabilistic Conclusion

Induction captures probabilistic, experience-based, or pattern-based reasoning.

| Label | Meaning |
|---|---|
| `IND_PATTERN` | Recognizing a typical illness script or clinical pattern. |
| `IND_INTUITION` | Expressing a gut feeling, discomfort, or pre-analytic clinical concern. |
| `IND_BAYESIAN` | Updating diagnostic probability using evidence, frequencies, sensitivity, specificity, or prevalence. |
| `IND_CASEBASED` | Reasoning from similar previous cases or published case reports. |

## 3. Work Completed So Far

### 3.1 Manual Annotation Strategy

The first step was to find an intelligent and reproducible way to label diagnostic reasoning. To do this, we built a fast manual annotation interface that allows annotators to:

- open a clinical case;
- annotate only the reasoning section;
- select spans directly from the source text;
- assign one of the 12 reasoning labels;
- export each annotation with character ranges, label IDs, label names, and the extracted text.

This gave us a practical way to transform clinical diagnostic discussions into structured JSON annotations.

The manual annotation tool is implemented in `annotation_tool/` and documented in `docs/annotation_tool.md`. Its output schema is shared by the rest of the project.

### 3.2 Human Comparison and Few-Shot Example Selection

After manually labeling examples, we compared the annotations in a dedicated comparison tool. This tool allows multiple JSON files for the same case to be loaded together, overlaid on the source text, and inspected for span boundaries and label differences.

The goal of this stage was not to compute a formal agreement score. Instead, the team used the comparison tool to inspect disagreements, discuss ambiguous cases, and select the strongest examples to use as few-shot examples for the automated labeling stage.

This process produced a curated few-shot set of 24 examples: two examples for each of the 12 reasoning categories.

The comparison tool is implemented in `comparison_tool/` and documented in `docs/comparison_tool.md`.

### 3.3 LLM Jury for Automatic Reasoning Annotation

After defining the taxonomy and selecting the few-shot examples, we built an automatic labeling system based on an LLM jury.

The jury system asks 15 independent LLM voters, also called judges, to annotate the reasoning section of each case. Each judge receives:

- the label taxonomy;
- detailed annotation instructions;
- the 24 curated few-shot examples;
- the reasoning section of the case.

Each judge returns a JSON array of labeled text spans. The model is explicitly instructed not to generate character offsets. Instead, it returns only the label name and the exact quoted text span. The pipeline then resolves those quoted spans back to character ranges in the original source file using deterministic exact matching and fuzzy matching.

This design choice is important because LLM-generated offsets would be unreliable. The current pipeline therefore uses the LLM only for semantic labeling and uses code for offset reconstruction.

The jury pipeline is implemented in `jury/` and documented in `docs/llm_jury.md` and `jury/README.md`.

### 3.4 Current Jury Output

At the current stage, the project contains:

- 32 human-written clinical cases in `cases/`;
- 15 LLM judge outputs per case;
- 480 judge annotation files in `jury_output/`;
- 32 jury summary directories;
- output JSON files that are schema-compatible with the manual annotations.

This means that each of the 32 cases currently has a full set of automatic reasoning annotations produced by the LLM jury.

### 3.5 Qualitative Validation

The LLM-generated labels were checked manually in the comparison tool. The purpose of this validation was to verify that the automatically selected spans and labels were reasonable, correct and useful.

The current assessment is that the outputs are qualitatively strong. Formal inter-annotator agreement metrics are not the main focus at this stage, because the project is using the jury primarily as a reasoning-span classifier. The immediate objective is not to prove that the model is an ideal classifier, but to create a scalable annotation layer that allows comparison between human diagnostic reasoning and LLM-generated diagnostic reasoning.

For this reason, visual/manual validation is acceptable for the current stage, especially because the original workflow was itself based on manual inspection and discussion.

## 4. Current System Architecture

The current workflow can be summarized as:

```text
cases/*.md
    |
    |--> annotation_tool
    |       |--> annotated_cases/*.json
    |
    |--> comparison_tool
    |       |--> human annotation review
    |       |--> human vs jury inspection
    |
    |--> jury pipeline
            |--> jury_output/{case_id}/{case_id}_Judge001.json
            |--> ...
            |--> jury_output/{case_id}/{case_id}_Judge015.json
            |--> jury_output/{case_id}/{case_id}_jury_summary.json
```

The most important architectural principle is that human annotations and machine annotations use the same output schema. This allows the same comparison and analysis tools to work across both sources.

## 5. Key Methodological Decisions

### 5.1 The Jury Is a Classifier, Not the Object of Evaluation

The LLM jury is not the primary object being studied. It is an annotation mechanism. Its role is to label reasoning spans so that later we can compare human reasoning and LLM-generated reasoning.

Because of this, the central research question is not: "How well does the jury classify clinical reasoning?"

The central research question is: "Once clinical reasoning is labeled using a consistent framework, how do human and LLM diagnostic reasoning patterns differ?"

### 5.2 Single Model vs Multiple Models for the Jury

The current jury can be run with one model or potentially with several models. At the moment, using a single strong model may be preferable. Llama currently appears to perform best, and adding weaker models may add noise rather than improve classification quality.

This remains an open design decision. Since the jury is being used as a classifier rather than as the target of evaluation, consistency may matter more than model diversity.

### 5.3 Agreement Metrics Are Not the Immediate Priority

Formal agreement metrics may be useful later, but they are not central right now. The project is not currently focused on estimating annotator agreement or evaluating the classifier as a standalone system.

The immediate priority is to generate a reliable comparative dataset:

- human differential diagnosis reasoning, labeled by the jury;
- LLM-generated differential diagnosis reasoning, labeled by the same jury;
- comparable distributions of reasoning types across both groups.

## 6. Next Major Phase: Generate LLM Differential Diagnoses

The next stage is to make LLMs generate their own differential diagnoses for each clinical case.

For each case, the system should take only the Presentation of Case as input and ask multiple models to produce a differential diagnosis. The generated output should be a reasoning trace comparable to the human expert discussion.

The planned setup is:

- 32 source cases from `cases/`;
- 3 differential diagnosis generations per case;
- 3 different LLMs, if feasible;
- each model receives the Presentation of Case;
- each model returns a differential diagnosis with reasoning.

The generated cases should be stored in a new folder, tentatively named `cases_llm/`.

This folder should mirror the structure of `cases/`, but replace the human-written differential diagnosis section with the model-generated differential diagnosis.

Conceptually:

```text
cases/
    2003 Case 21.md
    2016 Case 25.md
    ...

cases_llm/
    2003 Case 21/
        2003 Case 21_ModelA.md
        2003 Case 21_ModelB.md
        2003 Case 21_ModelC.md
    2016 Case 25/
        2016 Case 25_ModelA.md
        2016 Case 25_ModelB.md
        2016 Case 25_ModelC.md
```

The exact naming convention can still be adjusted, but the structure should preserve the original case identity and the model identity.

## 7. Next Pipeline Extension: Label LLM-Generated Reasoning

Once the LLM-generated differential diagnoses exist, they should be passed through the same jury annotation system.

This will produce a new output folder, tentatively named `jury_output_llm/`, analogous to the current `jury_output/` folder.

Expected structure:

```text
jury_output_llm/
    2003_Case_21_ModelA/
        2003_Case_21_ModelA_Judge001.json
        ...
        2003_Case_21_ModelA_Judge015.json
        2003_Case_21_ModelA_jury_summary.json
```

This step is critical because it keeps the comparison fair: both human-written reasoning and LLM-generated reasoning are labeled by the same automatic classifier, with the same taxonomy, prompt structure, and output schema.

## 8. Final Analysis Plan

After both human and LLM-generated differential diagnoses have been annotated, the final step is to compare reasoning patterns.

The first analysis should remain simple and interpretable. The most useful starting point is the distribution of reasoning labels:

- count of each reasoning label per source type;
- proportion of abduction, deduction, and induction;
- subtype-level distribution across the 12 labels;
- per-case differences between human and LLM reasoning;
- per-model differences between generated diagnoses;
- overall human vs LLM reasoning profile.

The analysis should initially avoid complex agreement logic. Consensus may be useful for visualization or filtering, but it is not the main research object. The most important output is a clear comparison of reasoning-type distributions.

Potential metrics:

| Metric | Purpose |
|---|---|
| Label counts | How often each reasoning subtype appears. |
| Mode proportions | Relative use of abduction, deduction, and induction. |
| Case-normalized proportions | Prevents longer cases from dominating the analysis. |
| Model-level profiles | Shows whether different LLMs reason differently. |
| Human vs LLM deltas | Highlights reasoning types overused or underused by models. |
| Span length by label | Optional proxy for how much textual space each reasoning type occupies. |

## 9. Complete Roadmap

### Phase 1: Define the Annotation Framework

Status: complete.

- Define abduction, deduction, and induction as the three main reasoning modes.
- Define 12 subtype labels.
- Convert the taxonomy into operational annotation rules.
- Decide to annotate reasoning spans, not final diagnoses alone.

### Phase 2: Build Manual Annotation Tool

Status: complete.

- Build a fast local interface for span-level annotation.
- Export annotations as JSON with ranges, labels, label names, and text.
- Restrict annotation to the reasoning section of each case.
- Use the tool to manually label examples.

### Phase 3: Build Comparison Tool

Status: complete.

- Load multiple annotation JSON files for the same case.
- Overlay spans and labels on the source text.
- Inspect disagreement and label distributions.
- Use the tool to discuss manual annotations and select high-quality examples.

### Phase 4: Curate Few-Shot Examples

Status: complete.

- Compare manual annotations.
- Discuss ambiguous spans and labels.
- Select 24 strong examples: two for each label.
- Insert the few-shot examples into the jury prompt.

### Phase 5: Build LLM Jury Classifier

Status: complete.

- Build a prompt with the taxonomy and few-shot examples.
- Run 15 independent LLM judges per case.
- Resolve quoted spans back to source offsets.
- Save one JSON file per judge.
- Save one summary file per case.
- Keep output schema compatible with manual annotations.

### Phase 6: Run Jury on Human Cases

Status: complete.

- Run the jury on all 32 available human-written cases.
- Produce 480 judge files.
- Produce 32 summary files.
- Validate outputs manually through the comparison tool.

### Phase 7: Generate LLM Differential Diagnoses

Status: next.

- Build a new generation module for LLM differential diagnoses.
- Extract only the Presentation of Case from each source case.
- Prompt three LLMs to generate a differential diagnosis for each case.
- Store generated cases in `cases_llm/`.
- Preserve source case identity and model identity in filenames.

### Phase 8: Annotate LLM-Generated Diagnoses with the Jury

Status: planned.

- Run the existing jury classifier on the generated LLM cases.
- Save outputs under `jury_output_llm/`.
- Keep the same 15-judge structure and JSON schema.
- Check a sample manually in the comparison tool.

### Phase 9: Compare Human and LLM Reasoning

Status: planned.

- Aggregate labels from `jury_output/` and `jury_output_llm/`.
- Compute label counts and proportions.
- Compare human vs LLM reasoning distributions.
- Compare model-specific reasoning profiles.
- Identify which reasoning modes are overrepresented or underrepresented in LLM-generated differential diagnoses.

### Phase 10: Prepare Presentation and Research Narrative

Status: planned.

- Explain the motivation: comparing reasoning, not just answers.
- Show the taxonomy and examples.
- Show the manual annotation workflow.
- Show the jury pipeline.
- Present the human-case annotation results.
- Present the planned LLM-generation and comparison stages.
- Discuss why agreement metrics are not the central focus at this stage.

## 10. Immediate Team To-Do List

1. Decide the final set of LLMs for differential diagnosis generation.
2. Decide whether the jury should remain a single-model jury or use multiple classifier models.
3. Implement the LLM differential diagnosis generation module.
4. Create the `cases_llm/` folder structure.
5. Generate three model diagnoses for each of the 32 cases.
6. Run the jury on the generated diagnoses.
7. Create aggregation scripts for label counts and distributions.
8. Produce initial plots or tables for human vs LLM reasoning comparison.

## 11. Suggested Presentation Storyline

The presentation can follow this structure:

1. Diagnostic reasoning is more than a final answer.
2. We define a taxonomy of epistemic reasoning modes.
3. We manually annotate clinical reasoning spans to build high-quality examples.
4. We compare and curate examples using a dedicated comparison tool.
5. We scale annotation using an LLM jury with 15 judges.
6. We validate the outputs qualitatively through manual inspection.
7. We use the jury as a classifier to label both human and model reasoning.
8. We generate LLM differential diagnoses from the same case presentations.
9. We compare the reasoning distributions of humans and LLMs.
10. The final contribution is a reproducible framework for studying diagnostic reasoning patterns rather than only diagnostic accuracy.

## 12. Expected Final Deliverables

By the end of the project, the repository should contain:

- the original human-written cases;
- manually annotated reference examples;
- a working manual annotation interface;
- a working comparison interface;
- a working LLM jury classifier;
- jury annotations for human-written cases;
- LLM-generated differential diagnoses;
- jury annotations for LLM-generated diagnoses;
- aggregation scripts for reasoning-label distributions;
- tables or plots comparing human and LLM reasoning;
- a clear methodological narrative for presentation and reporting.

## 13. Core Message

This project builds a pipeline for comparing the reasoning patterns of clinicians and LLMs. The central object is not the final diagnosis, but the structure of diagnostic reasoning itself. By annotating human and LLM reasoning with the same epistemic taxonomy, the project makes it possible to compare how different agents generate hypotheses, test them, validate them, and draw probabilistic conclusions.

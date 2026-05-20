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

## 6. LLM Differential Diagnosis Generation

### 6.1 Design Decision: Input Restriction

The generation step gives each model only the `## Presentation of Case` section. The model never sees the human expert discussion. This ensures that the generated reasoning is independent of the reference and that any differences observed in the comparison reflect genuine differences in how humans and LLMs reason, not imitation.

The generated output must be a free-form differential diagnosis discussion structurally comparable to the human-written reasoning sections. Models are not asked to produce a structured list or a summary. They are asked to reason through the case as a clinician would.

### 6.2 Model Selection

Three models were selected for generation, all accessed through the NVIDIA Inference Microservices API:

| Model identifier | Short name |
|---|---|
| `meta/llama-3.3-70b-instruct` | Llama 70B |
| `openai/gpt-oss-120b` | GPT 120B |
| `qwen/qwen3-next-80b-a3b-instruct` | Qwen 80B |

These three were chosen after a broader evaluation of available catalog models. Several alternatives were ruled out during testing: `mistralai/mixtral-8x22b-instruct-v0.1` consistently returned outputs that were too short; `google/gemma-4-31b-it` and `deepseek-ai/deepseek-v4-pro` timed out on long-form generation; `Palmyra` and `Jamba` endpoints returned account-level errors.

The three selected models represent different training lineages (Meta, OpenAI, Alibaba/Qwen) and different parameter scales, which gives the comparison structural diversity without introducing low-quality outputs.

### 6.3 Output Structure

The generated cases are stored in `cases_llm/`. Each case gets its own folder, and within that folder there is one file per model:

```text
cases_llm/
    1990 Case 19/
        1990 Case 19__meta-llama-3.3-70b-instruct.md
        1990 Case 19__openai-gpt-oss-120b.md
        1990 Case 19__qwen-qwen3-next-80b-a3b-instruct.md
    1991 Case 14/
        ...
```

Each output file is a complete markdown document that contains the original case title, the original Presentation of Case (copied verbatim), and the model-generated `## Differential Diagnosis` section. The title and presentation are added by the local writer module, not by the model. This structure makes each file readable as a stand-alone case and compatible with the downstream jury annotation pipeline without any modifications.

### 6.4 Generation Parameters

The generation pipeline uses a temperature of 0.7 and a maximum of 8192 output tokens. A minimum word count of 1400 words per generation is enforced, with one expansion attempt if the first generation falls short. This threshold ensures that generated outputs are comparable in length and depth to the human-written discussions.

The generation module is implemented in `llm_generation/` and documented in `llm_generation/README.md`.

Final output: 32 cases × 3 models = **96 generated differential diagnosis documents**.

## 7. Jury Annotation of LLM-Generated Cases

### 7.1 Design Principle: Same Classifier, Same Prompt

The LLM-generated differential diagnoses are annotated by the exact same jury system used for the human-written cases. The taxonomy, the jury prompt, the few-shot examples, the number of judges (15), and the output schema are all unchanged. This symmetry is essential for the comparison to be fair.

### 7.2 Output Structure

The jury outputs for LLM-generated cases are stored in `jury_output_llm/`. The structure mirrors `jury_output/`, with an additional nesting level for the model identity:

```text
jury_output_llm/
    1990_Case_19/
        meta-llama-3.3-70b-instruct/
            1990_Case_19_Judge001.json
            ...
            1990_Case_19_Judge015.json
            1990_Case_19_jury_summary.json
        openai-gpt-oss-120b/
            ...
        qwen-qwen3-next-80b-a3b-instruct/
            ...
```

Each judge file and each summary file follow the same JSON schema as the human-case outputs. This means the same loading and aggregation code works across both output trees.

### 7.3 Scale

32 cases × 3 models × 15 judges = **1440 judge annotation files**, plus 96 jury summary files.

## 8. Comparative Analysis

### 8.1 Analysis Groups

After both the human-written and LLM-generated cases have been annotated, the analysis compares four groups:

| Group | Source |
|---|---|
| Human | `jury_output/` — the 32 human-written cases |
| Llama 70B | `jury_output_llm/` — model `meta-llama-3.3-70b-instruct` |
| GPT 120B | `jury_output_llm/` — model `openai-gpt-oss-120b` |
| Qwen 80B | `jury_output_llm/` — model `qwen-qwen3-next-80b-a3b-instruct` |

All four groups are compared using identical aggregation logic. The unit of analysis is the annotated span after consensus filtering.

### 8.2 Consensus Filtering

Before computing any metric, the jury summary files are filtered by a consensus threshold. For a given span and a given candidate label, the threshold defines the minimum fraction of covering judges that must agree on the label for it to be accepted. Three threshold levels are used:

| Threshold | Meaning |
|---|---|
| 0.0 | No filter — all spans from any judge are included |
| 0.5 | Majority — a label is accepted only if more than 50% of covering judges agree |
| 0.7 | Strong majority — a label is accepted only if at least 70% of covering judges agree |

A minimum covering count (`MIN_COVERING = 5`) is enforced at non-zero thresholds: a span is only subject to the ratio filter if at least 5 judges annotated it. Spans covered by fewer judges are excluded rather than passed through, to prevent isolated annotations from appearing artificially high-confidence.

All three threshold levels are run and their outputs are saved independently. This allows the presentation to show how robust the results are to different filtering choices.

### 8.3 Metrics

The analysis computes four metrics for each group and each threshold setting:

**DDx Coverage.** The fraction of the differential diagnosis text that is covered by at least one accepted annotation. This measures how densely each group's reasoning is annotated. A low coverage score may indicate sparse reasoning or reasoning expressed in a way the jury does not label confidently.

**Macro distribution (ABD / DED / IND).** The proportion of accepted annotations that fall into each of the three main reasoning modes. This is the primary high-level comparison: it shows whether humans and LLMs differ in their overall balance of hypothesis generation, hypothesis testing, and probabilistic reasoning.

**Micro distribution (12-label breakdown).** The proportion of accepted annotations for each of the 12 subtype labels. This provides a finer view, showing not just that LLMs use more or less induction than humans, but which specific inductive subtypes drive the difference.

**Inter-judge agreement (IAA).** The average pairwise agreement among the 15 jury judges on the annotated spans, computed per group. This is a quality signal for the annotation rather than a primary research metric: it indicates how consistently the jury labels each group's reasoning. Lower IAA on LLM-generated cases would suggest that those cases contain more ambiguous or unusual reasoning spans.

### 8.4 Implementation

The analysis is implemented as a Jupyter notebook, `analysis.ipynb`, structured into clearly separated sections: imports, parameter configuration, data loading, and one section per metric. The notebook is designed to be re-run with different threshold settings by changing a single cell.

Plots are saved to `plots/` with the threshold value and minimum covering count encoded in the filename, for example `macro_thr0.7_mincov5.png`. This makes it straightforward to include specific plots in the presentation without ambiguity about which filtering settings produced them.

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

Status: complete.

- Build the `llm_generation/` module.
- Extract only the Presentation of Case from each source case.
- Select three generation models: Llama 3.3 70B, GPT 120B, Qwen 80B (via NVIDIA API).
- Generate a differential diagnosis for each of the 32 cases with each model.
- Store results in `cases_llm/` with per-case subfolders and per-model files.
- Enforce a minimum output length of 1400 words with one expansion attempt.

### Phase 8: Annotate LLM-Generated Diagnoses with the Jury

Status: complete.

- Run the existing jury classifier on all 96 generated cases.
- Save outputs under `jury_output_llm/` with model identity as a nested subfolder.
- Keep the same 15-judge structure and JSON schema.
- Produce 1440 judge files and 96 summary files.

### Phase 9: Compare Human and LLM Reasoning

Status: complete.

- Implement `analysis.ipynb` for four-group comparison (Human, Llama 70B, GPT 120B, Qwen 80B).
- Apply consensus filtering at three thresholds (0.0, 0.5, 0.7).
- Compute DDx coverage, macro distribution, micro distribution, and inter-judge agreement.
- Save all plots to `plots/` with threshold settings encoded in filenames.

### Phase 10: Prepare Presentation and Research Narrative

Status: in progress.

- Explain the motivation: comparing reasoning, not just answers.
- Show the taxonomy and examples.
- Show the manual annotation workflow.
- Show the jury pipeline.
- Present the human-case annotation results.
- Present the LLM-generation and comparison stages.
- Show the comparative analysis results.
- Discuss why agreement metrics are not the central focus.

## 10. Final System Architecture

The complete workflow, from raw cases to comparative analysis, is:

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
    |       |--> jury_output/{case_id}/{case_id}_Judge001.json
    |       |--> ...
    |       |--> jury_output/{case_id}/{case_id}_Judge015.json
    |       |--> jury_output/{case_id}/{case_id}_jury_summary.json
    |
    |--> llm_generation
    |       |--> cases_llm/{case_name}/{case_name}__{model}.md
    |
    |--> jury pipeline (same, applied to LLM cases)
    |       |--> jury_output_llm/{case_id}/{model}/{case_id}_Judge001.json
    |       |--> ...
    |       |--> jury_output_llm/{case_id}/{model}/{case_id}_jury_summary.json
    |
    |--> analysis.ipynb
            |--> plots/{metric}_thr{threshold}_mincov{n}.png
```

The most important architectural principle remains the same throughout: human annotations and machine annotations use the same output schema. The jury pipeline itself is used both to label human-written reasoning and to label LLM-generated reasoning, ensuring that any observed differences in label distributions are attributable to differences in the reasoning content, not to differences in the annotation method.

## 11. Presentation Storyline

The presentation follows this structure:

1. Diagnostic reasoning is more than a final answer.
2. We define a taxonomy of epistemic reasoning modes.
3. We manually annotate clinical reasoning spans to build high-quality examples.
4. We compare and curate examples using a dedicated comparison tool.
5. We scale annotation using an LLM jury with 15 judges.
6. We validate the outputs qualitatively through manual inspection.
7. We generate LLM differential diagnoses from the same case presentations.
8. We run the same jury on both human and LLM-generated reasoning.
9. We compare reasoning distributions across four groups and three consensus thresholds.
10. The final contribution is a reproducible framework for studying diagnostic reasoning patterns rather than only diagnostic accuracy.

## 12. Core Message

This project builds a pipeline for comparing the reasoning patterns of clinicians and LLMs. The central object is not the final diagnosis, but the structure of diagnostic reasoning itself. By annotating human and LLM reasoning with the same epistemic taxonomy and the same automatic classifier, the project makes it possible to compare how different agents generate hypotheses, test them, validate them, and draw probabilistic conclusions.

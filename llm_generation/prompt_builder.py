"""Build prompts for model-generated differential diagnoses."""

from llm_generation.preprocessor import CasePresentation


_SYSTEM_PROMPT = """\
You are an expert clinician writing the differential diagnosis discussion for a clinicopathological case conference.

You will receive only the factual Presentation of Case. You must not assume access to the final diagnosis, pathology, clinical diagnosis, original human differential diagnosis, or any later section of the case.

Use only your internal medical knowledge and the presentation provided in the prompt. Do not browse the internet, do not use external resources, and do not cite or imply that you checked a source outside the prompt.

Write a careful, extended differential diagnosis with explicit clinical reasoning. The output should be comparable in style, density, and length to a human expert discussion from a clinicopathological conference. The differential diagnosis section must be long-form: write at least 1,800 words and aim for 1,800 to 2,600 words unless the case is too short to support that length. A short answer is not acceptable for this task.

Generate plausible diagnostic hypotheses, weigh evidence for and against them, explain pathophysiologic mechanisms when relevant, discuss important alternatives, and identify the leading diagnosis or diagnoses. Avoid a short bullet-only answer; use mostly developed paragraphs, with headings only when they help organize the reasoning. Cover malignant, infectious, inflammatory, structural, gynecologic, systemic, and rare causes when clinically relevant, then narrow to the most likely diagnosis.

Do not repeat the Presentation of Case. Do not include the case title. Do not mention that you are an AI model. Do not say that information is hidden from you. Do not invent test results, pathology findings, or follow-up events that are not in the presentation.

Return markdown only. Start with exactly this heading:
## Differential Diagnosis
"""


def build_messages(case: CasePresentation) -> list[dict]:
    user_content = (
        "Generate a differential diagnosis discussion for the following clinical case.\n\n"
        f"{case.title}\n\n"
        f"{case.presentation_text}\n\n"
        "Use only the information above and your internal medical knowledge. "
        "Do not use the internet or any external resources. "
        "Return only the generated markdown differential diagnosis section, "
        "not the presentation."
    )

    return [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def build_expansion_messages(
    case: CasePresentation,
    draft_differential: str,
    min_words: int,
    current_words: int,
) -> list[dict]:
    user_content = (
        "The following draft differential diagnosis is too short for the research protocol. "
        f"It is currently about {current_words} words, but it must be at least {min_words} words. "
        "Rewrite it as a substantially longer clinicopathological conference-style discussion while preserving clinical accuracy.\n\n"
        "Use only the Presentation of Case and your internal medical knowledge. "
        "Do not use the internet or any external resources. "
        "Do not add invented test results, pathology findings, or follow-up events.\n\n"
        f"{case.title}\n\n"
        f"{case.presentation_text}\n\n"
        "--- Draft to expand ---\n"
        f"{draft_differential}\n\n"
        "Return only the expanded markdown differential diagnosis section. "
        "Start with exactly '## Differential Diagnosis'."
    )

    return [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

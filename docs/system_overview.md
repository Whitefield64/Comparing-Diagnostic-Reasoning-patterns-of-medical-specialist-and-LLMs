# System Overview

This project studies epistemic reasoning in clinical diagnosis by combining human annotation, tool-based comparison, and an LLM jury pipeline.

## Roadmap

The intended progression of the system is:

1. Annotate a small set of cases carefully to build high-quality few-shot examples.
2. Use the comparison tool to inspect multiple human annotations and decide which spans are strongest or most consistent.
3. Run the LLM jury on the same case text to produce multiple independent annotation attempts.
4. Compare the jury output in the comparison tool to check whether the labels and offsets behave as expected.
5. Improve the LLM jury pipeline (TODO for next Monday!!): use different models (now I am using only a llama), tune thresholds, etc.. . Then test it on the other 30 new documents.
6. Let the LLM generate diagnoses, then use the jury pipeline to label those diagnosis traces as well.
7. Compare human reasoning and LLM reasoning distributions across the same case library. (probably we can do it on all labels, the consensu logic is useless)

The codebase already supports the first four steps. The later steps describe the research path the project is moving toward.


## Related Docs

- [Annotation tool guide](annotation_tool.md)
- [Comparison tool guide](comparison_tool.md)
- [LLM jury guide](llm_jury.md)
- [Details on the Jury system](/jury/README.md)
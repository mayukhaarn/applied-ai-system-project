# Model Card

## Limitations & Biases

This system is currently a prototype and uses a placeholder AI pipeline rather than a real model backend. The `Agent` returns simulated responses, and the `Evaluator` performs a simple rule-based confidence and hallucination check. This means:

- The model does not reflect real-world generative behavior.
- Output quality is constrained by hardcoded logic rather than trained weights.
- Biases can arise from the prompt structure and from the placeholder answer format, especially if the output is used as if it were factual.
- The system does not currently verify responses against a knowledge source, so hallucination risk is underestimated.

## Misuse & Prevention

### Potential misuse

- The tool could be misused to generate inaccurate or misleading guidance for founders if treated as authoritative.
- It could also be used to automate reviewer feedback without sufficient human oversight, leading to unfair or incorrect evaluations.

### Preventative measures

- Require manual review for responses flagged by the `Evaluator` as low confidence or high hallucination risk.
- Add input sanitization to prevent injection-style prompts or unsupported query formats.
- Log all query-response pairs and review decisions to enable later audit.
- Integrate a real retrieval layer and authoritative knowledge source before using the system for production assessments.

## AI Collaboration Reflection

### Helpful suggestion

The AI suggested a modular pipeline with separate `Retriever`, `Agent`, and `Evaluator` components. This was helpful because it made the system easier to architect, document, and extend.

### Flawed suggestion

The AI also assumed that the current repository had a working external model integration. That was incorrect: the current codebase uses a placeholder response engine, so the suggestion needed correction to reflect the actual implementation.

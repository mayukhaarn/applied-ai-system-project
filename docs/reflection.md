# Project Reflection

## Responsible AI

This system is currently a prototype with a simulated AI pipeline. The limitations are clear: the `Agent` stage produces placeholder responses, the `Retriever` stage simulates context rather than querying a real knowledge base, and the evaluator uses a heuristic hallucination estimate. Because of this, the system can be overly optimistic about output quality and may incorrectly label uncertain content as safe. If this were deployed with a real model, biased training data or ambiguous prompts could lead to unfair assessments of founder submissions.

Potential misuse includes relying on the evaluator as an automatic gatekeeper for important decisions, rather than using it as a signal for review. A preventative measure is to require manual signoff on any response flagged as low confidence or high hallucination risk, and to log all such cases for periodic audit.

A specific surprise during development was how brittle even a simple confidence threshold can be: the current placeholder outputs always report the same confidence, which hides the real variability and reliability issues that would emerge with a real model.

## AI Collaboration

During this build, the AI collaborator helped by recommending a clean modular pipeline with separate `Retriever`, `Agent`, and `Evaluator` classes. That suggestion was helpful because it aligned with the project requirement for a clear data flow and made the architecture easier to explain.

One flawed suggestion was the implied expectation that the current code already had a working external model integration. In practice, the repository is still using hardcoded placeholder responses, so that suggestion overstated the system's current capabilities. It was a useful reminder to keep the documentation aligned with the actual implementation and not to treat prototype code as production-ready.

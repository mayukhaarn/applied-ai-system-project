"""Entry point for the modular AI system.

Data flow:
    User Query -> Retriever -> Agent -> Evaluator -> Output
"""
from __future__ import annotations

from typing import Literal

from ai_system import Agent, Evaluator, Retriever


VALID_TONES: tuple[Literal["firm", "calm", "professional"] , ...] = ("firm", "calm", "professional")


def run(query: str, tone: str = "professional") -> dict:
    tone = tone.lower()
    if tone not in VALID_TONES:
        tone = "professional"

    retriever = Retriever(sources=["knowledge_base", "documents"])
    context = retriever.retrieve(query)

    baseline_agent = Agent(model_name="baseline-agent", tone="neutral")
    baseline_raw = baseline_agent.process(query, context)

    styled_agent = Agent(model_name="modular-agent-v1", tone=tone)
    styled_raw = styled_agent.process(query, context)

    evaluator = Evaluator(confidence_threshold=0.70)
    baseline_eval = evaluator.evaluate(baseline_raw)
    styled_eval = evaluator.evaluate(styled_raw)

    style_difference = baseline_raw["answer"] != styled_raw["answer"]
    style_score = float(style_difference)

    return {
        "query": query,
        "context": context,
        "baseline": {
            "raw_response": baseline_raw,
            "evaluation": baseline_eval,
        },
        "tone_response": {
            "raw_response": styled_raw,
            "evaluation": styled_eval,
        },
        "style_comparison": {
            "tone": tone,
            "difference_detected": style_difference,
            "difference_score": style_score,
        },
    }


if __name__ == "__main__":
    user_query = input("Enter your query: ").strip()
    user_tone = input("Choose a tone (firm, calm, professional) [professional]: ").strip() or "professional"
    result = run(user_query, tone=user_tone)

    print("\n=== System Output ===")
    print(f"Tone: {result['style_comparison']['tone']}")
    print(f"Answer: {result['tone_response']['evaluation']['answer']}")
    print(f"Confidence: {result['tone_response']['evaluation']['confidence']}")
    print(f"Hallucination score: {result['tone_response']['evaluation']['hallucination_score']}")
    print(f"Manual review required: {result['tone_response']['evaluation']['manual_review']}")
    print(f"Baseline difference detected: {result['style_comparison']['difference_detected']}")
    if result['tone_response']['evaluation']['manual_review']:
        print(f"Review reason: {result['tone_response']['evaluation']['review_reason']}")

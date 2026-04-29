"""Agent module for processing logic and generating responses."""
from __future__ import annotations

from typing import Any


class Agent:
    """Processes a user query with context and returns a raw AI response.

    Data flow:
        Retriever output -> Agent.process() -> raw response dict
    """

    def __init__(
        self,
        model_name: str = "base-agent",
        tone: str = "neutral",
    ):
        self.model_name = model_name
        self.tone = tone.lower()

    def process(self, query: str, context: dict[str, Any]) -> dict[str, Any]:
        """Generate a response using the query, retrieved context, and style constraints."""
        answer = self._generate_answer(query, context)
        raw_response = {
            "query": query,
            "context": context,
            "answer": answer,
            "confidence": self._confidence_for_tone(),
            "metadata": {
                "model": self.model_name,
                "tone": self.tone,
                "context_size": len(str(context)),
                "few_shot_examples": self._few_shot_examples(),
            },
        }
        return raw_response

    def _generate_answer(self, query: str, context: dict[str, Any]) -> str:
        tone_instruction = self._tone_instruction()
        example = self._tone_example()
        context_summary = context.get("context_text", "contextual guidance")
        return (
            f"{tone_instruction} {example} "
            f"For the question '{query}', the most relevant guidance is drawn from {context_summary}."
        )

    def _tone_instruction(self) -> str:
        if self.tone == "firm":
            return "Be direct and decisive."
        if self.tone == "calm":
            return "Respond gently and reassuringly."
        if self.tone == "professional":
            return "Use polished, professional language and clear structure."
        return "Provide a balanced and neutral explanation."

    def _tone_example(self) -> str:
        examples = {
            "firm": "Example style: 'This is the action we should take immediately.'",
            "calm": "Example style: 'This can be handled steadily with confidence.'",
            "professional": "Example style: 'The recommendation follows established evaluation standards.'",
            "neutral": "Example style: 'This is a balanced summary of the approach.'",
        }
        return examples.get(self.tone, examples["neutral"])

    def _confidence_for_tone(self) -> float:
        if self.tone == "firm":
            return 0.82
        if self.tone == "calm":
            return 0.80
        if self.tone == "professional":
            return 0.88
        return 0.78

    def _few_shot_examples(self) -> list[dict[str, str]]:
        return [
            {
                "query": "Define the review process.",
                "answer": "Describe the review process clearly, including checkpoints and accountability.",
            },
            {
                "query": "What should be included in homework feedback?",
                "answer": "Include strengths, opportunities for improvement, and specific next steps.",
            },
        ]

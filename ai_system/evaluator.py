"""Evaluator module for response quality and hallucination detection."""
from __future__ import annotations

from typing import Any


class Evaluator:
    """Checks AI output and flags low-confidence responses.

    Data flow:
        Agent output -> Evaluator.evaluate() -> evaluated result
    """

    def __init__(self, confidence_threshold: float = 0.70):
        self.confidence_threshold = confidence_threshold

    def evaluate(self, response: dict[str, Any]) -> dict[str, Any]:
        """Evaluate the raw response and produce quality metrics."""
        hallucination_score = self._estimate_hallucination(response)
        confidence = response.get("confidence", 0.0)
        manual_review = self.flag_for_manual_review(confidence, hallucination_score)

        return {
            "answer": response.get("answer", ""),
            "confidence": confidence,
            "hallucination_score": hallucination_score,
            "manual_review": manual_review,
            "review_reason": self._review_reason(confidence, hallucination_score),
            "metadata": response.get("metadata", {}),
        }

    def flag_for_manual_review(self, confidence: float, hallucination_score: float) -> bool:
        """Flag the response for human review if confidence is low or hallucination risk is high."""
        return confidence < self.confidence_threshold or hallucination_score > 0.5

    def _estimate_hallucination(self, response: dict[str, Any]) -> float:
        """Estimate a hallucination score for the output.

        In a real system this would compare the output against trusted source data.
        """
        answer = str(response.get("answer", "")).lower()
        if "not sure" in answer or "i think" in answer:
            return 0.65
        return 0.15

    def _review_reason(self, confidence: float, hallucination_score: float) -> str:
        if confidence < self.confidence_threshold:
            return "Low confidence response detected."
        if hallucination_score > 0.5:
            return "High hallucination risk detected."
        return "Response appears normal." 

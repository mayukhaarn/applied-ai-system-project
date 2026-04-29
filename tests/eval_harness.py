"""Evaluation harness for the modular AI project.

This script executes predefined queries against the main pipeline and applies
simple validity checks to each response.
"""
import logging
import sys
from pathlib import Path
from typing import List, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from main import run

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

TEST_CASES = [
    "Summarize the Founder Institute mission.",
    "How should we evaluate accelerator homework submissions?",
    "What triggers a manual review for AI-generated feedback?",
    "Describe the role of the retriever in the system.",
    "Explain why a confidence threshold is important."
]

TONE_VARIANTS = ["firm", "calm", "professional"]


def validate_response(query: str, response: dict) -> Tuple[bool, str]:
    evaluation = response.get("tone_response", {}).get("evaluation", {})
    answer = evaluation.get("answer", "")
    style_comparison = response.get("style_comparison", {})

    if not answer or len(answer.strip()) < 15:
        return False, "Answer is empty or too short."

    if not style_comparison.get("difference_detected", False):
        return False, "Tone response did not differ from baseline."

    keywords = [token for token in query.lower().split() if len(token) > 4]
    if keywords and not any(keyword in answer.lower() for keyword in keywords):
        return False, "Answer does not contain expected query keywords."

    if evaluation.get("confidence", 0.0) <= 0:
        return False, "Confidence score is missing or invalid."

    return True, "Valid response."


def run_tests(test_queries: List[str]) -> None:
    passed = 0
    total = len(test_queries) * len(TONE_VARIANTS)
    confidence_values = []

    for query in test_queries:
        for tone in TONE_VARIANTS:
            try:
                result = run(query, tone=tone)
                evaluation = result.get("tone_response", {}).get("evaluation", {})
                confidence = evaluation.get("confidence", 0.0)
                confidence_values.append(confidence)

                valid, reason = validate_response(query, result)
                if valid:
                    passed += 1
                    logger.info("PASS: %s | tone=%s", query, tone)
                else:
                    logger.warning("FAIL: %s | tone=%s | Reason: %s", query, tone, reason)
            except Exception:
                logger.exception("ERROR running query: %s | tone=%s", query, tone)

    avg_confidence = sum(confidence_values) / len(confidence_values) if confidence_values else 0.0
    print(
        f"{passed} out of {total} style tests passed. "
        f"Confidence scores averaged {avg_confidence:.2f}."
    )


if __name__ == "__main__":
    run_tests(TEST_CASES)

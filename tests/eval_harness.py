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


def validate_response(query: str, response: dict) -> Tuple[bool, str]:
    evaluation = response.get("evaluation", {})
    answer = evaluation.get("answer", "")
    if not answer or len(answer.strip()) < 15:
        return False, "Answer is empty or too short."

    keywords = [token for token in query.lower().split() if len(token) > 4]
    if keywords and not any(keyword in answer.lower() for keyword in keywords):
        return False, "Answer does not contain expected query keywords."

    if evaluation.get("confidence", 0.0) <= 0:
        return False, "Confidence score is missing or invalid."

    return True, "Valid response."


def run_tests(test_queries: List[str]) -> None:
    passed = 0
    total = len(test_queries)
    confidence_values = []

    for query in test_queries:
        try:
            result = run(query)
            evaluation = result.get("evaluation", {})
            confidence = evaluation.get("confidence", 0.0)
            confidence_values.append(confidence)

            valid, reason = validate_response(query, result)
            if valid:
                passed += 1
                logger.info("PASS: %s", query)
            else:
                logger.warning("FAIL: %s | Reason: %s", query, reason)
        except Exception as exc:
            logger.exception("ERROR running query: %s", query)

    avg_confidence = sum(confidence_values) / len(confidence_values) if confidence_values else 0.0
    print(f"{passed} out of {total} tests passed. Confidence scores averaged {avg_confidence:.2f}.")


if __name__ == "__main__":
    run_tests(TEST_CASES)

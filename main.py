"""Entry point for the modular AI system.

Data flow:
    User Query -> Retriever -> Agent -> Evaluator -> Output
"""
from ai_system import Agent, Evaluator, Retriever


def run(query: str) -> dict:
    retriever = Retriever(sources=["knowledge_base", "documents"])
    context = retriever.retrieve(query)

    agent = Agent(model_name="modular-agent-v1")
    raw_response = agent.process(query, context)

    evaluator = Evaluator(confidence_threshold=0.70)
    evaluated_output = evaluator.evaluate(raw_response)

    return {
        "query": query,
        "context": context,
        "raw_response": raw_response,
        "evaluation": evaluated_output,
    }


if __name__ == "__main__":
    user_query = input("Enter your query: ").strip()
    result = run(user_query)

    print("\n=== System Output ===")
    print(f"Answer: {result['evaluation']['answer']}")
    print(f"Confidence: {result['evaluation']['confidence']}")
    print(f"Hallucination score: {result['evaluation']['hallucination_score']}")
    print(f"Manual review required: {result['evaluation']['manual_review']}")
    if result['evaluation']['manual_review']:
        print(f"Review reason: {result['evaluation']['review_reason']}")

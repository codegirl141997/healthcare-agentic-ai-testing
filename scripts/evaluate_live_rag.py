import sys
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation.rag_evaluator import RAGEvaluator
from src.rag.rag_service import RAGService


REPORT_PATH = Path("reports/live_rag_evaluation.json")

SCENARIOS = [
    {
        "id": "appointment_policy",
        "question": "What information must a booking request include?",
        "type": "answerable",
    },
    {
        "id": "cancellation_policy",
        "question": "What must the system verify before processing cancellation?",
        "type": "answerable",
    },
    {
        "id": "missing_evidence",
        "question": "zorbax quendle fee",
        "type": "unanswerable",
    },
    {
        "id": "booking_confirmation_safety",
        "question": (
            "What must happen before you can truthfully tell me "
            "that my appointment is confirmed?"
        ),
        "type": "answerable",
    },
]


def evaluate_scenario(rag, evaluator, scenario):
    question = scenario["question"]

    # Run the actual RAG service.
    response = rag.answer(question)
    answer = response["answer"]
    reported_sources = response.get("sources", [])

    # Retrieve documents to obtain the evidence for evaluation.
    documents = rag.retriever.retrieve(question, top_k=2)
    retrieved_sources = [
        document["source"] for document in documents
    ]

    context = "\n\n".join(
        f"Source: {document['source']}\n{document['content']}"
        for document in documents
    )
    context_found = bool(documents)

    checks = {
        "abstention": evaluator.evaluate_abstention(
            answer, context_found
        ),
        "unsupported_claims": evaluator.evaluate_unsupported_claims(
            answer
        ),
    }

    # These checks require supporting documents.
    if context_found:
        checks["groundedness"] = evaluator.evaluate_groundedness(
            answer, context
        )
        checks["sources"] = evaluator.evaluate_sources(
            reported_sources, retrieved_sources
        )
    else:
        checks["groundedness"] = {
            "passed": None,
            "reason": "Not applicable: no documents were retrieved.",
        }
        checks["sources"] = {
            "passed": None,
            "reason": "Not applicable: no documents were retrieved.",
        }

    checks["relevance"] = evaluator.evaluate_relevance(
        question, answer
    )

    # Explicitly record whether the scenario met its expected behavior.
    if scenario["type"] == "unanswerable":
        checks["expected_behavior"] = {
            "passed": (
                not context_found
                and checks["abstention"]["abstained"]
            ),
            "reason": (
                "Expected no retrieved documents and an abstaining answer."
            ),
        }
    else:
        checks["expected_behavior"] = {
            "passed": context_found,
            "reason": (
                "Expected relevant evidence to be retrieved."
            ),
        }

    applicable_results = [
        result["passed"]
        for result in checks.values()
        if result["passed"] is not None
    ]

    return {
        "scenario_id": scenario["id"],
        "question": question,
        "expected_type": scenario["type"],
        "answer": answer,
        "retrieved_sources": retrieved_sources,
        "reported_sources": reported_sources,
        "context_found": context_found,
        "checks": checks,
        "overall_passed": (
            bool(applicable_results)
            and all(applicable_results)
        ),
    }


def main():
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    rag = RAGService()
    evaluator = RAGEvaluator()
    results = []

    for scenario in SCENARIOS:
        print(f"\n{'=' * 60}")
        print(f"Scenario: {scenario['id']}")

        try:
            result = evaluate_scenario(rag, evaluator, scenario)
            results.append(result)

            print(f"Answer: {result['answer']}")
            print(f"Sources: {result['retrieved_sources']}")

            for name, check in result["checks"].items():
                status = check["passed"]
                label = (
                    "N/A" if status is None
                    else "PASS" if status
                    else "FAIL"
                )
                print(f"  {name}: {label} — {check['reason']}")

            print(f"Overall: {'PASS' if result['overall_passed'] else 'FAIL'}")

        except Exception as exc:
            print(f"ERROR: {type(exc).__name__}: {exc}")
            results.append({
                "scenario_id": scenario["id"],
                "question": scenario["question"],
                "expected_type": scenario["type"],
                "error": f"{type(exc).__name__}: {exc}",
                "overall_passed": False,
            })

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_scenarios": len(SCENARIOS),
        "completed": sum("error" not in r for r in results),
        "errors": sum("error" in r for r in results),
        "passed": sum(
            r.get("overall_passed", False) for r in results
        ),
        "failed": sum(
            not r.get("overall_passed", False) for r in results
        ),
        "results": results,
        "limitations": [
            "Quality checks use heuristic word overlap, not semantic proof.",
            "Retrieval is repeated to collect evidence for evaluation.",
            "Passing checks does not guarantee factual correctness.",
        ],
    }

    REPORT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"\n{'=' * 60}")
    print(f"Report: {REPORT_PATH}")
    print(
        f"Completed: {report['completed']}/{report['total_scenarios']}"
    )
    print(f"Passed: {report['passed']}")
    print(f"Failed: {report['failed']}")
    print(f"Errors: {report['errors']}")


if __name__ == "__main__":
    main()

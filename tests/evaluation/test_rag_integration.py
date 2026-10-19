
from src.evaluation.rag_evaluator import RAGEvaluator
from src.rag.rag_service import RAGService


class FakeRetriever:
    """Return controlled documents without accessing the filesystem."""

    def __init__(self, documents):
        self.documents = documents

    def retrieve(self, query, top_k=2):
        return self.documents[:top_k]


class FakeLLM:
    """Return a predictable answer without calling Ollama."""

    def __init__(self, answer):
        self.answer = answer
        self.last_prompt = None

    def generate_response(self, prompt):
        self.last_prompt = prompt
        return self.answer


def test_rag_answer_is_supported_by_retrieved_context():
    documents = [
        {
            "source": "clinic_hours.txt",
            "content": "Clinic hours are 9 AM to 5 PM.",
        }
    ]
    llm = FakeLLM("Clinic hours are 9 AM to 5 PM.")
    service = RAGService(FakeRetriever(documents), llm)
    evaluator = RAGEvaluator()

    result = service.answer("What are the clinic hours?")
    context = documents[0]["content"]

    groundedness = evaluator.evaluate_groundedness(
        result["answer"], context
    )
    relevance = evaluator.evaluate_relevance(
        "What are the clinic hours?", result["answer"]
    )

    assert groundedness["passed"] is True
    assert relevance["passed"] is True
    assert result["sources"] == ["clinic_hours.txt"]
    assert llm.last_prompt is not None


def test_unconfirmed_booking_claim_is_flagged():
    llm = FakeLLM("Your appointment is confirmed.")
    service = RAGService(
        FakeRetriever([
            {
                "source": "booking_policy.txt",
                "content": "Appointments can be requested online.",
            }
        ]),
        llm,
    )
    evaluator = RAGEvaluator()

    result = service.answer("Can I book an appointment?")
    quality = evaluator.evaluate_unsupported_claims(result["answer"])

    assert quality["passed"] is False
    assert "appointment is confirmed" in quality["violations"]


def test_missing_documents_produce_an_abstention():
    llm = FakeLLM("This should not be called.")
    service = RAGService(FakeRetriever([]), llm)
    evaluator = RAGEvaluator()

    result = service.answer("What is the clinic's refund policy?")
    quality = evaluator.evaluate_abstention(
        result["answer"],
        context_found=False,
    )

    assert quality["passed"] is True
    assert result["sources"] == []
    assert result["grounded"] is False
    assert llm.last_prompt is None


def test_rag_sources_match_retrieved_documents():
    documents = [
        {
            "source": "appointment_policy.txt",
            "content": "Appointments require an available slot.",
        },
        {
            "source": "clinic_hours.txt",
            "content": "The clinic operates from 9 AM to 5 PM.",
        },
    ]
    service = RAGService(
        FakeRetriever(documents),
        FakeLLM("Appointments require an available slot."),
    )
    evaluator = RAGEvaluator()

    result = service.answer("How do appointments work?")
    quality = evaluator.evaluate_sources(
        reported_sources=result["sources"],
        retrieved_sources=[doc["source"] for doc in documents],
    )

    assert quality["passed"] is True


def test_rag_pipeline_does_not_report_fabricated_sources():
    evaluator = RAGEvaluator()

    quality = evaluator.evaluate_sources(
        reported_sources=["invented_policy.txt"],
        retrieved_sources=["appointment_policy.txt"],
    )

    assert quality["passed"] is False

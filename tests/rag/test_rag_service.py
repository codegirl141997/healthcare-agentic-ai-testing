
from unittest.mock import Mock

import pytest

from src.rag.rag_service import RAGService


@pytest.fixture
def fake_retriever():
    retriever = Mock()
    retriever.retrieve.return_value = [
        {
            "source": "appointment_rules.txt",
            "content": (
                "An appointment is confirmed only after the booking "
                "service returns successful confirmation."
            ),
        }
    ]
    return retriever


@pytest.fixture
def fake_llm():
    llm = Mock()
    llm.generate_response.return_value = (
        "An appointment is confirmed only after successful "
        "booking service confirmation."
    )
    return llm


def test_rag_answer_uses_retrieved_context(fake_retriever, fake_llm):
    service = RAGService(retriever=fake_retriever, llm=fake_llm)

    result = service.answer("When is an appointment confirmed?")

    assert "confirmed" in result["answer"].lower()
    assert result["sources"] == ["appointment_rules.txt"]
    assert result["grounded"] is True
    fake_llm.generate_response.assert_called_once()


def test_rag_passes_context_to_llm(fake_retriever, fake_llm):
    service = RAGService(retriever=fake_retriever, llm=fake_llm)

    service.answer("When is an appointment confirmed?")

    prompt = fake_llm.generate_response.call_args.args[0]

    assert "successful confirmation" in prompt
    assert "appointment_rules.txt" in prompt
    assert "ONLY the supplied context" in prompt


def test_rag_does_not_call_llm_without_documents(fake_llm):
    retriever = Mock()
    retriever.retrieve.return_value = []

    service = RAGService(retriever=retriever, llm=fake_llm)

    result = service.answer("What is the weather on Mars?")

    assert result["sources"] == []
    assert result["grounded"] is False
    assert "cannot answer" in result["answer"].lower()
    fake_llm.generate_response.assert_not_called()


def test_rag_rejects_empty_question(fake_retriever, fake_llm):
    service = RAGService(retriever=fake_retriever, llm=fake_llm)

    with pytest.raises(ValueError, match="non-empty string"):
        service.answer("")


def test_rag_rejects_whitespace_question(fake_retriever, fake_llm):
    service = RAGService(retriever=fake_retriever, llm=fake_llm)

    with pytest.raises(ValueError, match="non-empty string"):
        service.answer("   ")

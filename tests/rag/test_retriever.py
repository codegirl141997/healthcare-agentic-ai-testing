
from pathlib import Path

import pytest

from src.rag.retriever import DocumentRetriever


@pytest.fixture
def knowledge_dir(tmp_path):
    (tmp_path / "appointment_rules.txt").write_text(
        "An appointment is confirmed only after booking service confirmation.",
        encoding="utf-8",
    )
    (tmp_path / "cancellation_rules.txt").write_text(
        "Cancellation requires an existing appointment.",
        encoding="utf-8",
    )
    return tmp_path


def test_retriever_loads_documents(knowledge_dir):
    retriever = DocumentRetriever(str(knowledge_dir))

    documents = retriever.load_documents()

    assert len(documents) == 2
    assert all("source" in document for document in documents)
    assert all("content" in document for document in documents)


def test_retriever_finds_relevant_document(knowledge_dir):
    retriever = DocumentRetriever(str(knowledge_dir))

    results = retriever.retrieve("appointment confirmed booking service")

    assert results
    assert results[0]["source"] == "appointment_rules.txt"


def test_retriever_returns_no_results_for_unmatched_query(knowledge_dir):
    retriever = DocumentRetriever(str(knowledge_dir))

    results = retriever.retrieve("volcano astronomy galaxies")

    assert results == []


def test_retriever_rejects_empty_query(knowledge_dir):
    retriever = DocumentRetriever(str(knowledge_dir))

    with pytest.raises(ValueError, match="non-empty string"):
        retriever.retrieve("")


def test_retriever_rejects_invalid_top_k(knowledge_dir):
    retriever = DocumentRetriever(str(knowledge_dir))

    with pytest.raises(ValueError, match="positive integer"):
        retriever.retrieve("appointment", top_k=0)


def test_retriever_rejects_missing_directory(tmp_path):
    missing_dir = tmp_path / "missing"
    retriever = DocumentRetriever(str(missing_dir))

    with pytest.raises(FileNotFoundError, match="Knowledge directory not found"):
        retriever.load_documents()

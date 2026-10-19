
from src.rag.retriever import DocumentRetriever
from src.services.llm_service import LLMService


class RAGService:
    """Generate answers using retrieved knowledge documents."""

    def __init__(
        self,
        retriever: DocumentRetriever | None = None,
        llm: LLMService | None = None,
    ):
        self.retriever = retriever or DocumentRetriever()
        self.llm = llm or LLMService()

    def answer(self, question: str) -> dict:
        """Answer a question using retrieved context and report its sources."""
        if not isinstance(question, str) or not question.strip():
            raise ValueError("Question must be a non-empty string.")

        documents = self.retriever.retrieve(question, top_k=2)

        if not documents:
            return {
                "answer": (
                    "I cannot answer this question from the available "
                    "knowledge documents."
                ),
                "sources": [],
                "grounded": False,
            }

        context = "\n\n".join(
            f"Source: {document['source']}\n{document['content']}"
            for document in documents
        )

        prompt = f"""
You are a healthcare appointment information assistant.

Answer the question using ONLY the supplied context.
Do not invent policies or claim that an appointment was booked or cancelled.
If the context does not contain the answer, say that the information is unavailable.
This is synthetic information for software testing, not medical advice.

Context:
{context}

Question:
{question}

Provide a concise answer.
"""

        generated_answer = self.llm.generate_response(prompt)

        return {
            "answer": generated_answer,
            "sources": [document["source"] for document in documents],
            "grounded": True,
        }

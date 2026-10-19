
from pathlib import Path


class DocumentRetriever:
    """Retrieve relevant text sections from local knowledge documents."""

    def __init__(self, knowledge_dir: str = "data/knowledge"):
        self.knowledge_dir = Path(knowledge_dir)

    def load_documents(self) -> list[dict[str, str]]:
        """Load all .txt knowledge documents."""
        if not self.knowledge_dir.exists():
            raise FileNotFoundError(
                f"Knowledge directory not found: {self.knowledge_dir}"
            )

        documents = []

        for path in sorted(self.knowledge_dir.glob("*.txt")):
            content = path.read_text(encoding="utf-8").strip()

            if content:
                documents.append(
                    {
                        "source": path.name,
                        "content": content,
                    }
                )

        return documents

    def retrieve(self, query: str, top_k: int = 2) -> list[dict[str, str]]:
        """Rank documents using simple keyword overlap."""
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Query must be a non-empty string.")

        if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k < 1:
            raise ValueError("top_k must be a positive integer.")

        query_words = set(query.lower().split())
        scored_documents = []

        for document in self.load_documents():
            document_words = set(document["content"].lower().split())
            score = len(query_words & document_words)

            if score > 0:
                scored_documents.append(
                    {
                        **document,
                        "score": score,
                    }
                )

        scored_documents.sort(
            key=lambda item: (-item["score"], item["source"])
        )

        return scored_documents[:top_k]

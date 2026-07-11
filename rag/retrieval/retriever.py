"""
High-level retriever that other parts of the system use.
"""

from rag.vectorstores.chroma_store import ChromaStore


class Retriever:
    def __init__(self, store: ChromaStore):
        self.store = store

    def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Standard retrieve interface expected by KnowledgeAdapter.
        Returns list of {"text", "score", "metadata"}.
        """
        return self.store.search(query=query, top_k=top_k)

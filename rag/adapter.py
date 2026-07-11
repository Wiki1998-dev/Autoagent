"""
KnowledgeAdapter — the single interface that all MCP servers and agents
use to talk to the RAG system. Isolates them from retriever internals.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class SearchResult:
    text: str
    source: str
    score: float
    metadata: dict[str, Any]


class KnowledgeAdapter:
    def __init__(self, retriever):
        """
        Accepts any object with a .retrieve(query, top_k) method
        that returns list[dict] with keys: text, score, metadata.
        """
        self.retriever = retriever

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        raw_results = self.retriever.retrieve(query, top_k=top_k)
        results: list[SearchResult] = []

        for item in raw_results:
            metadata = item.get("metadata", {})
            results.append(
                SearchResult(
                    text=item.get("text", ""),
                    source=metadata.get("source", "unknown"),
                    score=float(item.get("score", 0.0)),
                    metadata=metadata,
                )
            )
        return results

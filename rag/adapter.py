"""
KnowledgeAdapter — the single interface that all MCP servers and agents
use to talk to the RAG system. Isolates them from retriever internals.
"""

import structlog
from dataclasses import dataclass
from typing import Any

from rag.vectorstores.chroma_store import EmptyRAGError

logger = structlog.get_logger("autoagent.rag")


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
        try:
            raw_results = self.retriever.retrieve(query, top_k=top_k)
        except EmptyRAGError:
            logger.warning("rag_empty_results", query=query[:120])
            return []
        except TimeoutError as e:
            logger.error("rag_timeout", query=query[:120], error=str(e))
            return []

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


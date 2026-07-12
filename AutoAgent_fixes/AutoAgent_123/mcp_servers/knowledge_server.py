"""
Knowledge MCP Server.

Exposes RAG search as MCP tools that agents can call:
  - search_internal_docs
  - find_similar_incidents
  - search_requirements
"""

from fastmcp import FastMCP
from rag.adapter import KnowledgeAdapter

mcp = FastMCP("knowledge-server")

_adapter: KnowledgeAdapter | None = None


def set_adapter(adapter: KnowledgeAdapter):
    """Inject the KnowledgeAdapter at startup."""
    global _adapter
    _adapter = adapter


def _require_adapter():
    """Raise a clear error if the adapter has not been initialised yet."""
    if _adapter is None:
        raise RuntimeError(
            "KnowledgeAdapter is not initialised. "
            "Call set_adapter() before starting the server."
        )
    return _adapter


@mcp.tool()
def search_internal_docs(query: str, top_k: int = 5) -> list[dict]:
    """Search all internal documents for relevant evidence."""
    results = _require_adapter().search(query=query, top_k=top_k)
    return [
        {
            "text": r.text,
            "source": r.source,
            "score": r.score,
            "metadata": r.metadata,
        }
        for r in results
    ]


@mcp.tool()
def find_similar_incidents(query: str, top_k: int = 5) -> list[dict]:
    """Search specifically for similar incident reports."""
    results = _require_adapter().search(query=query, top_k=top_k)
    return [
        {
            "text": r.text,
            "source": r.source,
            "score": r.score,
            "metadata": r.metadata,
        }
        for r in results
        if "INC-" in r.source or "incident" in r.source.lower()
    ]


@mcp.tool()
def search_requirements(query: str, top_k: int = 5) -> list[dict]:
    """Search specifically for relevant requirements."""
    results = _require_adapter().search(query=query, top_k=top_k)
    return [
        {
            "text": r.text,
            "source": r.source,
            "score": r.score,
            "metadata": r.metadata,
        }
        for r in results
        if "REQ-" in r.source or "requirement" in r.source.lower()
    ]

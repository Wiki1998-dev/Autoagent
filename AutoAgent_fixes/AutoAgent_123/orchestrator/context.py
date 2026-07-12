"""
Pipeline dependency container.

Replaces the module-level globals (_llm, _adapter) that were
not thread-safe. Pass a PipelineContext into build_graph() so
each invocation carries its own isolated dependencies.
"""

from dataclasses import dataclass
from core.llm import LLM
from rag.adapter import KnowledgeAdapter


@dataclass(frozen=True)
class PipelineContext:
    llm: LLM
    adapter: KnowledgeAdapter

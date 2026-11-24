"""
Evidence Agent.

Takes the user request + scenario metadata, searches RAG for
relevant incidents, requirements, test reports, and model cards,
then packages everything into an EvidenceReport.
"""

import json

import config
from core.llm import LLM
from core.skill_loader import load_skill
from core.schemas import EvidenceReport
from core.logger import log_event
from rag.adapter import KnowledgeAdapter, SearchResult


def _flatten(value) -> list[str]:
    """Collect the leaf string/number values of nested scenario data."""
    if isinstance(value, dict):
        return [s for v in value.values() for s in _flatten(v)]
    if isinstance(value, list):
        return [s for v in value for s in _flatten(v)]
    if isinstance(value, (str, int, float)) and not isinstance(value, bool):
        return [str(value).replace("_", " ")]
    return []


def build_search_queries(user_request: str, scenario_data: dict) -> list[str]:
    """
    Derive RAG queries from the actual request and scenario, so any failure
    type (camera, brakes, steering, ...) retrieves its own evidence.
    """
    queries = [user_request[:500]]

    if scenario_data:
        system = str(scenario_data.get("system", "")).replace("_", " ")
        env = " ".join(_flatten(scenario_data.get("environment", {})))
        notes = str(scenario_data.get("notes", ""))

        queries.append(f"{system} failure {env}".strip())
        if notes:
            queries.append(notes)

        # Sensors/models whose prediction disagrees with ground truth
        predictions = scenario_data.get("predictions", {})
        if isinstance(predictions, dict) and predictions:
            preds = "; ".join(
                f"{name.replace('_', ' ')} predicted {p.get('class', p) if isinstance(p, dict) else p}"
                for name, p in predictions.items()
            )
            queries.append(f"{system} sensor disagreement: {preds}")

        xai = " ".join(_flatten(scenario_data.get("xai_summary", {})))
        if xai:
            queries.append(f"{system} {xai}")

        queries.append(f"safety requirement {system} {env}".strip())
        queries.append(f"test report {system} {env}".strip())

    # Process requirements apply to every investigation, regardless of domain
    queries.append("human oversight investigation approval")

    # Drop empties/duplicates, keep order
    seen: set[str] = set()
    return [q for q in queries if q.strip() and not (q in seen or seen.add(q))]


def select_evidence(results: list[SearchResult]) -> list[SearchResult]:
    """
    De-duplicate by chunk (not by file), rank by score, cap chunks per file so
    one large document cannot crowd out the rest, and stay within a character
    budget so the prompt fits the model's context window.
    """
    best: dict[tuple, SearchResult] = {}
    for r in results:
        key = (r.source, r.metadata.get("chunk"))
        if key not in best or r.score > best[key].score:
            best[key] = r

    selected: list[SearchResult] = []
    per_source: dict[str, int] = {}
    used_chars = 0
    for r in sorted(best.values(), key=lambda x: x.score, reverse=True):
        if per_source.get(r.source, 0) >= config.EVIDENCE_MAX_CHUNKS_PER_SOURCE:
            continue
        if used_chars + len(r.text) > config.EVIDENCE_CHAR_BUDGET and selected:
            continue
        selected.append(r)
        per_source[r.source] = per_source.get(r.source, 0) + 1
        used_chars += len(r.text)
    return selected


class EvidenceAgent:
    def __init__(self, llm: LLM, adapter: KnowledgeAdapter):
        self.llm = llm
        self.adapter = adapter
        self.skill = load_skill("evidence_agent")

    def run(self, task_id: str, user_request: str, scenario_data: dict) -> EvidenceReport:
        """
        1. Search RAG for incidents, requirements, test reports, model cards
        2. Ask LLM to synthesize into a structured EvidenceReport
        """
        log_event("agent_start", "evidence_agent", task_id)

        # ── Gather evidence from RAG ──
        queries = build_search_queries(user_request, scenario_data)
        all_results = select_evidence(
            [r for q in queries for r in self.adapter.search(q, top_k=config.RETRIEVAL_TOP_K * 2)]
        )

        # Format evidence for the LLM
        evidence_text = ""
        for r in all_results:
            label = r.source
            if "chunk" in r.metadata:
                label += f" [part {r.metadata['chunk']}]"
            evidence_text += f"\n--- Source: {label} (score: {r.score:.2f}) ---\n{r.text}\n"

        prompt = f"""
Investigation request: {user_request}

Scenario data:
{json.dumps(scenario_data, indent=2)}

Retrieved evidence:
{evidence_text}

Based on the above, produce an EvidenceReport as JSON.
Identify which retrieved documents are similar incidents,
which are relevant requirements, and what evidence is missing.
Task ID is: {task_id}
"""

        report = self.llm.generate_structured(
            prompt=prompt,
            schema=EvidenceReport,
            system=self.skill,
        )

        log_event(
            "agent_complete",
            "evidence_agent",
            task_id,
            data={"incidents_found": len(report.similar_incidents), "gaps": len(report.evidence_gaps)},
        )

        return report

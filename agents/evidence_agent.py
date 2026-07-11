"""
Evidence Agent.

Takes the user request + scenario metadata, searches RAG for
relevant incidents, requirements, test reports, and model cards,
then packages everything into an EvidenceReport.
"""

import json
from core.llm import LLM
from core.skill_loader import load_skill
from core.schemas import EvidenceReport, SourceReference
from core.logger import log_event
from rag.adapter import KnowledgeAdapter


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
        scenario_id = scenario_data.get("scenario_id", "unknown")
        system_name = scenario_data.get("system", "")
        env = scenario_data.get("environment", {})

        # Build search queries targeting different evidence types
        queries = [
            f"{system_name} {env.get('weather', '')} {env.get('time_of_day', '')} failure",
            f"camera false negative pedestrian {env.get('weather', '')}",
            f"sensor disagreement {system_name}",
            f"robustness requirement adverse visibility",
            f"human oversight investigation approval",
        ]

        all_results = []
        for q in queries:
            results = self.adapter.search(q, top_k=5)
            for r in results:
                # Deduplicate by source name
                if not any(existing.source == r.source for existing in all_results):
                    all_results.append(r)

        # Format evidence for the LLM
        evidence_text = ""
        for r in all_results:
            evidence_text += f"\n--- Source: {r.source} (score: {r.score:.2f}) ---\n{r.text}\n"

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

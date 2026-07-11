"""
Base class for the three specialist agents (Technical, Quality, Compliance).

They all follow the same pattern:
  1. Receive the evidence report
  2. Apply their skill perspective
  3. Return an AgentOpinion
"""

import json
from core.llm import LLM
from core.skill_loader import load_skill
from core.schemas import AgentOpinion, EvidenceReport
from core.logger import log_event


class BaseSpecialistAgent:
    agent_name: str = "base_specialist"
    skill_name: str = "technical_agent"

    def __init__(self, llm: LLM):
        self.llm = llm
        self.skill = load_skill(self.skill_name)

    def run(self, task_id: str, evidence_report: dict) -> AgentOpinion:
        log_event("agent_start", self.agent_name, task_id)

        prompt = f"""
You are analyzing investigation {task_id}.

Evidence report:
{json.dumps(evidence_report, indent=2)}

Apply your perspective and produce an AgentOpinion as JSON.
Set agent_name to "{self.agent_name}".
"""

        opinion = self.llm.generate_structured(
            prompt=prompt,
            schema=AgentOpinion,
            system=self.skill,
        )

        # Ensure agent_name is correct
        opinion.agent_name = self.agent_name

        log_event(
            "agent_complete",
            self.agent_name,
            task_id,
            data={"confidence": opinion.confidence, "findings": len(opinion.key_findings)},
        )

        return opinion

"""
Synthesis Agent.

Takes the evidence report, specialist opinions, and critic review
to produce a single, balanced FinalSynthesis.
"""

import json
from core.llm import LLM
from core.skill_loader import load_skill
from core.schemas import FinalSynthesis
from core.logger import log_event


class SynthesisAgent:
    def __init__(self, llm: LLM):
        self.llm = llm
        self.skill = load_skill("synthesis_agent")

    def run(
        self,
        task_id: str,
        evidence_report: dict,
        technical_opinion: dict,
        quality_opinion: dict,
        compliance_opinion: dict,
        comparative_review: dict,
    ) -> FinalSynthesis:
        log_event("agent_start", "synthesis_agent", task_id)

        prompt = f"""
You are producing the final synthesis for investigation {task_id}.

Evidence Report:
{json.dumps(evidence_report, indent=2)}

Technical Opinion:
{json.dumps(technical_opinion, indent=2)}

Quality Opinion:
{json.dumps(quality_opinion, indent=2)}

Compliance Opinion:
{json.dumps(compliance_opinion, indent=2)}

Critic's Comparative Review:
{json.dumps(comparative_review, indent=2)}

Produce a balanced FinalSynthesis as JSON. Only accept findings
that are adequately supported. Reject overclaimed conclusions.
Preserve uncertainty where warranted.
"""

        synthesis = self.llm.generate_structured(
            prompt=prompt,
            schema=FinalSynthesis,
            system=self.skill,
        )

        log_event(
            "agent_complete",
            "synthesis_agent",
            task_id,
            data={
                "accepted": len(synthesis.accepted_findings),
                "rejected": len(synthesis.rejected_findings),
                "unresolved": len(synthesis.unresolved_points),
            },
        )

        return synthesis

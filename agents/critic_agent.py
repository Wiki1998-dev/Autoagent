"""
Critic Agent.

Receives all three specialist opinions and produces a comparative
review identifying agreements, conflicts, weak claims, and gaps.
"""

import json
from core.llm import LLM
from core.skill_loader import load_skill
from core.schemas import ComparativeReview
from core.logger import log_event


class CriticAgent:
    def __init__(self, llm: LLM):
        self.llm = llm
        self.skill = load_skill("critic_agent")

    def run(
        self,
        task_id: str,
        technical_opinion: dict,
        quality_opinion: dict,
        compliance_opinion: dict,
    ) -> ComparativeReview:
        log_event("agent_start", "critic_agent", task_id)

        prompt = f"""
You are reviewing specialist opinions for investigation {task_id}.

Technical Agent opinion:
{json.dumps(technical_opinion, indent=2)}

Quality Agent opinion:
{json.dumps(quality_opinion, indent=2)}

Compliance Agent opinion:
{json.dumps(compliance_opinion, indent=2)}

Compare these opinions. Identify where they agree, where they
conflict, which claims are weak or unsupported, and what additional
evidence is needed. Produce a ComparativeReview as JSON.
"""

        review = self.llm.generate_structured(
            prompt=prompt,
            schema=ComparativeReview,
            system=self.skill,
        )

        log_event(
            "agent_complete",
            "critic_agent",
            task_id,
            data={
                "agreements": len(review.agreements),
                "disagreements": len(review.disagreements),
                "weak_claims": len(review.weak_claims),
            },
        )

        return review

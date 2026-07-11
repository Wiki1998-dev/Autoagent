"""
Validator Agent.

Cross-checks the final synthesis against the evidence and
specialist opinions to detect overclaims or unsupported conclusions.
"""

import json
from core.llm import LLM
from core.skill_loader import load_skill
from core.schemas import ValidationReport
from core.logger import log_event


class ValidatorAgent:
    def __init__(self, llm: LLM):
        self.llm = llm
        self.skill = load_skill("validator_agent")

    def run(
        self,
        task_id: str,
        evidence_report: dict,
        final_synthesis: dict,
        comparative_review: dict,
    ) -> ValidationReport:
        log_event("agent_start", "validator_agent", task_id)

        prompt = f"""
You are validating the final synthesis for investigation {task_id}.

Evidence Report:
{json.dumps(evidence_report, indent=2)}

Final Synthesis:
{json.dumps(final_synthesis, indent=2)}

Critic's Comparative Review:
{json.dumps(comparative_review, indent=2)}

Check every accepted finding in the synthesis against the evidence.
Count how many claims are supported vs unsupported.
Flag any contradictions, overclaims, or missing citations.
Produce a ValidationReport as JSON.
"""

        report = self.llm.generate_structured(
            prompt=prompt,
            schema=ValidationReport,
            system=self.skill,
        )

        log_event(
            "agent_complete",
            "validator_agent",
            task_id,
            data={
                "passed": report.passed,
                "supported": report.supported_claims,
                "unsupported": report.unsupported_claims,
                "issues": len(report.issues),
            },
        )

        return report

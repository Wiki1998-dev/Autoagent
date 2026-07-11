"""
Compliance and Requirements Agent.

Focuses on requirement traceability, regulatory alignment,
and human-oversight conditions.
"""

from agents.base_specialist import BaseSpecialistAgent


class ComplianceAgent(BaseSpecialistAgent):
    agent_name = "compliance_agent"
    skill_name = "compliance_agent"

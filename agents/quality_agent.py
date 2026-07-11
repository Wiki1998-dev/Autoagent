"""
Quality and Risk Agent.

Focuses on evidence sufficiency, test coverage gaps,
and engineering risk assessment.
"""

from agents.base_specialist import BaseSpecialistAgent


class QualityAgent(BaseSpecialistAgent):
    agent_name = "quality_agent"
    skill_name = "quality_agent"

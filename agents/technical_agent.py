"""
Technical Analysis Agent.

Focuses on root-cause hypotheses, sensor behavior,
and model-level technical findings.
"""

from agents.base_specialist import BaseSpecialistAgent


class TechnicalAgent(BaseSpecialistAgent):
    agent_name = "technical_agent"
    skill_name = "technical_agent"

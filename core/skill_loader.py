"""
Loads skill (system prompt) files from the skills/ directory.

Each agent has a markdown file that defines its role, goals,
rules, and expected output format. The LLM receives this as
the system prompt.
"""

import config

SKILLS_DIR = config.SKILLS_DIR


def load_skill(name: str) -> str:
    """
    Load a skill file by agent name.
    Example: load_skill("evidence_agent") reads skills/evidence_agent.md
    """
    path = SKILLS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Missing skill file: {path}")
    return path.read_text(encoding="utf-8")

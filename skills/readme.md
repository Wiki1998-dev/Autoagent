# Agent Skills & Personas (`/skills`)

This folder contains the prompt engineering backend for AutoAgent. Instead of hiding system prompts in Python code, they are exposed here as pure Markdown (`.md`) files.

## Philosophy
Separating prompts from logic enables non-programmers (like lead engineers or compliance officers) to review, tweak, and perfect the behavior of the AI agents.

## Contents
- **`evidence_skill.md`**: Instructions on how to extract search terms from a query.
- **`technical_skill.md`**: Persona for a senior automotive mechanical/software engineer.
- **`quality_skill.md`**: Persona for an ISO 9001/IATF 16949 quality manager.
- **`compliance_skill.md`**: Directives to strictly check safety standards.
- **`critic_skill.md`**: Instructions to act as a harsh reviewer finding logical fallacies.
- **`synthesis_skill.md`**: Formatting rules for the final engineering report.
- **`validator_skill.md`**: Rubric for checking the presence of root causes, formatting, and action items.


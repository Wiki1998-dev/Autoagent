"""
LLM wrapper for Ollama.

Provides two calling patterns:
  1. llm.generate(prompt) → raw text
  2. llm.generate_structured(prompt, schema) → parsed Pydantic model
"""

import json
import ollama
from pydantic import BaseModel
from typing import Type, TypeVar
import config

T = TypeVar("T", bound=BaseModel)


class LLM:
    def __init__(
        self,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ):
        self.model = model or config.LLM_MODEL
        self.temperature = temperature if temperature is not None else config.LLM_TEMPERATURE
        self.max_tokens = max_tokens or config.LLM_MAX_TOKENS

    def generate(self, prompt: str, system: str = "") -> str:
        """Generate raw text from a prompt."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = ollama.chat(
            model=self.model,
            messages=messages,
            options={
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
            },
        )
        return response["message"]["content"]

    def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        system: str = "",
    ) -> T:
        """
        Generate output and parse it into a Pydantic model.

        Injects JSON schema into the system prompt so the LLM
        knows the expected format, then extracts and parses JSON
        from the response.
        """
        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        format_instruction = (
            f"\n\nYou MUST respond with valid JSON matching this schema:\n"
            f"```json\n{schema_json}\n```\n"
            f"Return ONLY the JSON object, no other text."
        )

        full_system = (system + format_instruction) if system else format_instruction

        raw = self.generate(prompt=prompt, system=full_system)
        cleaned = self._extract_json(raw)

        return schema.model_validate_json(cleaned)

    @staticmethod
    def _extract_json(text: str) -> str:
        """Extract JSON from a response that may include markdown fences."""
        text = text.strip()

        # Remove markdown code fences
        if text.startswith("```"):
            lines = text.split("\n")
            # Drop first line (```json) and last line (```)
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines).strip()

        # Find the first { and last }
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            return text[start : end + 1]

        # Try array
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1:
            return text[start : end + 1]

        return text

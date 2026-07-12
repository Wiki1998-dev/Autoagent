"""
LLM wrapper for Ollama.

Provides two calling patterns:
  1. llm.generate(prompt) → raw text
  2. llm.generate_structured(prompt, schema) → parsed Pydantic model
"""

import json
import time
import ollama
from pydantic import BaseModel, ValidationError
from typing import Type, TypeVar
import config

T = TypeVar("T", bound=BaseModel)


class LLMParseError(Exception):
    """Raised when the LLM response cannot be parsed into the expected schema after all retries."""
    pass


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
        retries: int = 3,
    ) -> T:
        """
        Generate output and parse it into a Pydantic model.

        Injects JSON schema into the system prompt so the LLM
        knows the expected format, then extracts and parses JSON
        from the response. Retries up to `retries` times on
        parse failure before raising LLMParseError.
        """
        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        format_instruction = (
            f"\n\nYou MUST respond with valid JSON matching this schema:\n"
            f"```json\n{schema_json}\n```\n"
            f"Return ONLY the JSON object, no other text."
        )

        full_system = (system + format_instruction) if system else format_instruction

        last_err: Exception | None = None
        for attempt in range(1, retries + 1):
            try:
                raw = self.generate(prompt=prompt, system=full_system)
                cleaned = self._extract_json(raw)
                return schema.model_validate_json(cleaned)
            except (ValidationError, ValueError, KeyError) as e:
                last_err = e
                if attempt < retries:
                    print(f"  ⚠ LLM parse attempt {attempt}/{retries} failed: {e}. Retrying...")
                    time.sleep(1 * attempt)

        raise LLMParseError(
            f"Failed to parse {schema.__name__} after {retries} attempts. "
            f"Last error: {last_err}"
        )

    @staticmethod
    def _extract_json(text: str) -> str:
        """
        Extract JSON from a response that may include markdown fences.
        Uses bracket-counting so nested JSON inside string fields is handled correctly.
        """
        text = text.strip()

        # Strip markdown code fences
        if text.startswith("```"):
            lines = text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines).strip()

        # Walk the string tracking bracket depth — finds the correctly matched close
        for start_char, end_char in [("{", "}"), ("[", "]")]:
            start = text.find(start_char)
            if start == -1:
                continue
            depth = 0
            in_string = False
            escape_next = False
            for i, ch in enumerate(text[start:], start):
                if escape_next:
                    escape_next = False
                    continue
                if ch == "\\" and in_string:
                    escape_next = True
                    continue
                if ch == '"':
                    in_string = not in_string
                    continue
                if in_string:
                    continue
                if ch == start_char:
                    depth += 1
                elif ch == end_char:
                    depth -= 1
                    if depth == 0:
                        return text[start : i + 1]

        return text

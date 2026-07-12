"""
LLM wrapper — backend-agnostic.

Provides two calling patterns:
  1. llm.generate(prompt) → raw text
  2. llm.generate_structured(prompt, schema) → parsed Pydantic model

The actual model call is delegated to a pluggable backend (see core/backends.py):
  - "ollama" (default): local Ollama server, single-request-at-a-time
  - "vllm": self-hosted vLLM server, OpenAI-compatible, handles real concurrency

Select via config.LLM_BACKEND (env var LLM_BACKEND=ollama|vllm).
"""

import json
import random
import threading
import time
from pydantic import BaseModel, ValidationError
from typing import Type, TypeVar
import config
from core.backends import build_backend, LLMBackend
from langsmith import traceable

T = TypeVar("T", bound=BaseModel)

# ── Issue #8: rate-limiting semaphore ─────────────────────────
# Caps the number of simultaneous LLM calls across all threads.
# Default 1 = safe for Ollama (single-request server).
# Raise via LLM_MAX_CONCURRENT env var when using vLLM.
_LLM_SEMAPHORE = threading.Semaphore(
    int(config.LLM_MAX_CONCURRENT) if hasattr(config, "LLM_MAX_CONCURRENT") else 1
)



class LLMParseError(Exception):
    """Raised when the LLM response cannot be parsed into the expected schema after all retries."""
    pass


class LLM:
    def __init__(
        self,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        backend: str | None = None,
    ):
        """
        Args:
            model: model name/id (backend-specific). Defaults to config.LLM_MODEL
                   for ollama, or config.VLLM_MODEL for vllm.
            temperature: sampling temperature. Defaults to config.LLM_TEMPERATURE.
            max_tokens: max output tokens. Defaults to config.LLM_MAX_TOKENS.
            backend: "ollama" or "vllm". Defaults to config.LLM_BACKEND.
        """
        self.temperature = temperature if temperature is not None else config.LLM_TEMPERATURE
        self.max_tokens = max_tokens or config.LLM_MAX_TOKENS
        self.backend_name = (backend or config.LLM_BACKEND).lower()
        self._backend: LLMBackend = build_backend(backend_name=self.backend_name, model=model)
        self.model = getattr(self._backend, "model", model)

    @traceable(run_type="llm")
    def generate(self, prompt: str, system: str = "", retries: int = 3) -> str:
        """
        Generate raw text from a prompt.

        Retries on transient connection failures with exponential backoff
        + jitter (issue #19) to avoid thundering-herd when the server recovers.
        Acquires the module-level semaphore (issue #8) before each call to
        cap concurrent LLM requests.
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        last_err: Exception | None = None
        for attempt in range(1, retries + 1):
            try:
                # Semaphore limits concurrent outstanding requests
                with _LLM_SEMAPHORE:
                    return self._backend.chat(
                        messages=messages,
                        temperature=self.temperature,
                        max_tokens=self.max_tokens,
                    )
            except Exception as e:
                last_err = e
                if attempt < retries:
                    # Exponential backoff with full jitter: wait in [0, 2^attempt] seconds
                    cap = 2 ** attempt
                    wait = random.uniform(0, cap)
                    wait = min(wait, 30.0)   # never sleep more than 30 s
                    print(
                        f"  ⚠ {self.backend_name} connection error "
                        f"(attempt {attempt}/{retries}): "
                        f"{type(e).__name__}: {e}. Retrying in {wait:.1f}s..."
                    )
                    time.sleep(wait)

        raise ConnectionError(
            f"Failed to reach '{self.backend_name}' backend after {retries} attempts. "
            f"Last error: {type(last_err).__name__}: {last_err}. "
            + (
                "This usually means Ollama is overloaded by concurrent requests, "
                "out of memory, or not running. Check 'ollama ps' and Ollama's logs."
                if self.backend_name == "ollama"
                else "Check that the vLLM server is running and reachable at "
                     f"{config.VLLM_BASE_URL}."
            )
        ) from last_err


    @traceable(run_type="chain")
    def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        system: str = "",
        retries: int = 3,
    ) -> T:
        """
        Generate output and parse it into a Pydantic model.

        Instead of injecting raw JSON Schema (which weak models tend to
        echo back verbatim, since it already looks like a JSON answer),
        we build a concrete EXAMPLE instance of the target shape and show
        that instead. This is far less likely to be reproduced as-is.
        """
        example = self._build_example(schema)
        example_json = json.dumps(example, indent=2)
        format_instruction = (
            f"\n\nRespond with ONLY a single JSON object shaped exactly like this example "
            f"(the example below is illustrative — replace every value with your own "
            f"analysis, do not copy these placeholder values):\n"
            f"```json\n{example_json}\n```\n"
            f"Output ONLY that JSON object. No preamble, no explanation, no markdown "
            f"fences, no schema, no repeated instructions — just the filled-in JSON."
        )

        full_system = (system + format_instruction) if system else format_instruction

        last_err: Exception | None = None
        for attempt in range(1, retries + 1):
            try:
                raw = self.generate(prompt=prompt, system=full_system)
                return self._parse_response(raw, schema)
            except (ValidationError, ValueError, KeyError) as e:
                last_err = e
                if attempt < retries:
                    print(f"  ⚠ LLM parse attempt {attempt}/{retries} failed: {e}. Retrying...")
                    time.sleep(1 * attempt)

        raise LLMParseError(
            f"Failed to parse {schema.__name__} after {retries} attempts. "
            f"Last error: {last_err}"
        )

    @classmethod
    def _parse_response(cls, raw: str, schema: Type[T]) -> T:
        """
        Extract every balanced top-level JSON object/array in the response,
        and return the first one that actually validates against the schema.

        This guards against models that echo the schema (from the system
        prompt) back into their own response before giving the real answer —
        naive "first { to last }" extraction would return the echoed schema
        instead of the model's actual output.
        """
        candidates = cls._extract_json_candidates(raw)

        if not candidates:
            raise ValueError("No JSON object found in LLM response")

        errors = []
        for candidate in candidates:
            try:
                return schema.model_validate_json(candidate)
            except ValidationError as e:
                errors.append(str(e))
                continue

        # None of the candidates validated — raise with ALL errors, not just the last
        # (issue #13: surfacing only errors[-1] hides which candidates were tried)
        error_detail = "\n".join(
            f"  candidate[{i}]: {e}" for i, e in enumerate(errors)
        )
        raise ValueError(
            f"Found {len(candidates)} JSON candidate(s) in response but none matched "
            f"{schema.__name__}.\n{error_detail}"
        )

    @classmethod
    def _build_example(cls, schema: Type[BaseModel]) -> dict:
        """
        Build a concrete example dict matching the shape of `schema`,
        resolving nested models and $defs/$ref so the LLM sees a realistic
        instance instead of raw JSON Schema metadata.
        """
        full_schema = schema.model_json_schema()
        defs = full_schema.get("$defs", {})
        return cls._example_from_node(full_schema, defs)

    @classmethod
    def _example_from_node(cls, node: dict, defs: dict, depth: int = 0) -> object:
        """Recursively convert a JSON Schema node into an example value."""
        if depth > 6:
            return None

        # Resolve $ref
        if "$ref" in node:
            ref_name = node["$ref"].split("/")[-1]
            resolved = defs.get(ref_name, {})
            return cls._example_from_node(resolved, defs, depth + 1)

        # Handle anyOf / oneOf (e.g. Optional[...] or unions) — pick the first non-null branch
        for key in ("anyOf", "oneOf"):
            if key in node:
                branches = [b for b in node[key] if b.get("type") != "null"]
                if branches:
                    return cls._example_from_node(branches[0], defs, depth + 1)
                return None

        node_type = node.get("type")

        if node_type == "object" or "properties" in node:
            props = node.get("properties", {})
            return {
                name: cls._example_from_node(prop_schema, defs, depth + 1)
                for name, prop_schema in props.items()
            }

        if node_type == "array":
            item_schema = node.get("items", {})
            # Show one example item so the model understands the shape,
            # while making clear (via placeholder text) that it's illustrative
            return [cls._example_from_node(item_schema, defs, depth + 1)]

        if node_type == "string":
            if "enum" in node:
                return node["enum"][0]
            return f"<{node.get('title', node.get('description', 'text'))}>"

        if node_type == "integer":
            return 0

        if node_type == "number":
            return 0.5

        if node_type == "boolean":
            return True

        if node_type == "null":
            return None

        # Fallback for anything unrecognised
        return None

    @staticmethod
    def _extract_json_candidates(text: str) -> list[str]:
        """
        Find every balanced top-level {...} or [...] block in the text,
        in the order they appear. Returns candidates preferring objects
        that appear LATER in the text first, since models tend to put
        their real answer after any preamble or schema echo.
        """
        text = text.strip()

        # Strip markdown code fences (may be multiple)
        if "```" in text:
            lines = text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines).strip()

        candidates: list[str] = []
        i = 0
        n = len(text)
        while i < n:
            ch = text[i]
            if ch in "{[":
                start_char = ch
                end_char = "}" if ch == "{" else "]"
                depth = 0
                in_string = False
                escape_next = False
                j = i
                closed_at = None
                while j < n:
                    c = text[j]
                    if escape_next:
                        escape_next = False
                        j += 1
                        continue
                    if c == "\\" and in_string:
                        escape_next = True
                        j += 1
                        continue
                    if c == '"':
                        in_string = not in_string
                        j += 1
                        continue
                    if not in_string:
                        if c == start_char:
                            depth += 1
                        elif c == end_char:
                            depth -= 1
                            if depth == 0:
                                closed_at = j
                                break
                    j += 1

                if closed_at is not None:
                    candidates.append(text[i : closed_at + 1])
                    i = closed_at + 1
                    continue
            i += 1

        # Prefer later candidates first (real answer usually follows any echoed schema)
        return list(reversed(candidates))

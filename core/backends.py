"""
Pluggable LLM backends.

Both backends expose the same interface:

    backend.chat(messages: list[dict], temperature: float, max_tokens: int) -> str

so `core/llm.py` can call either one without knowing which is active.

- OllamaBackend  → talks to a local Ollama server (http://localhost:11434 by default).
                   Ollama serves ONE request at a time per model by default, so
                   running multiple agents concurrently against it is unreliable —
                   see PARALLEL_SPECIALISTS in config.py.

- VLLMBackend    → talks to a self-hosted vLLM server via its OpenAI-compatible
                   `/v1/chat/completions` endpoint (`vllm serve <model>`). vLLM uses
                   continuous batching and is built to handle real concurrent
                   requests, making it a good fit if you want the 3 specialist
                   agents (Technical/Quality/Compliance) to run in parallel.
"""

from abc import ABC, abstractmethod

import config


class LLMBackend(ABC):
    """Common interface every backend must implement."""

    @abstractmethod
    def chat(self, messages: list[dict], temperature: float, max_tokens: int) -> str:
        """Send a chat completion request and return the response text."""
        raise NotImplementedError


class OllamaBackend(LLMBackend):
    def __init__(self, model: str | None = None, base_url: str | None = None):
        import ollama  # local import so this dependency is optional if unused

        self._ollama = ollama
        self.model = model or config.LLM_MODEL
        self.base_url = base_url or config.OLLAMA_BASE_URL
        self._client = ollama.Client(host=self.base_url)

    def chat(self, messages: list[dict], temperature: float, max_tokens: int) -> str:
        response = self._client.chat(
            model=self.model,
            messages=messages,
            options={
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        )
        return response["message"]["content"]


class VLLMBackend(LLMBackend):
    """
    Talks to a vLLM server's OpenAI-compatible endpoint.

    Start the server separately, e.g.:
        vllm serve meta-llama/Llama-3.1-8B-Instruct

    Then set in .env:
        LLM_BACKEND=vllm
        VLLM_BASE_URL=http://localhost:8000/v1
        VLLM_MODEL=meta-llama/Llama-3.1-8B-Instruct
    """

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
    ):
        from openai import OpenAI  # local import so this dependency is optional if unused

        self.model = model or config.VLLM_MODEL
        self.base_url = base_url or config.VLLM_BASE_URL
        self.api_key = api_key or config.VLLM_API_KEY
        self._client = OpenAI(base_url=self.base_url, api_key=self.api_key)

    def chat(self, messages: list[dict], temperature: float, max_tokens: int) -> str:
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content


def build_backend(
    backend_name: str | None = None,
    model: str | None = None,
) -> LLMBackend:
    """
    Factory: build the configured backend.

    backend_name defaults to config.LLM_BACKEND ("ollama" or "vllm").
    """
    name = (backend_name or config.LLM_BACKEND).lower()

    if name == "ollama":
        return OllamaBackend(model=model)
    if name == "vllm":
        return VLLMBackend(model=model)

    raise ValueError(
        f"Unknown LLM_BACKEND '{name}'. Expected 'ollama' or 'vllm'."
    )

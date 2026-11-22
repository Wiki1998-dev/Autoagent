"""
Generates embeddings via Ollama's local API.
"""

import ollama


class OllamaEmbedder:
    def __init__(self, model: str = "nomic-embed-text"):
        self.model = model

    def embed(self, text: str) -> list[float]:
        """Embed a single text string."""
        # /api/embed truncates inputs that exceed the model's context window
        # instead of failing (the legacy /api/embeddings endpoint errors out).
        response = ollama.embed(model=self.model, input=text, truncate=True)
        return list(response["embeddings"][0])

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts (sequential — Ollama has no native batch)."""
        return [self.embed(t) for t in texts]

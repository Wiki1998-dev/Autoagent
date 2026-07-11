"""
Generates embeddings via Ollama's local API.
"""

import ollama


class OllamaEmbedder:
    def __init__(self, model: str = "nomic-embed-text"):
        self.model = model

    def embed(self, text: str) -> list[float]:
        """Embed a single text string."""
        response = ollama.embeddings(model=self.model, prompt=text)
        return response["embedding"]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts (sequential — Ollama has no native batch)."""
        return [self.embed(t) for t in texts]

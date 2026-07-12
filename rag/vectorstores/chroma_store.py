"""
ChromaDB vector store wrapper.

Handles collection creation, document upsert, and similarity search.

Issue #3  — embedding model version stamped in collection metadata; mismatch
            raises a clear RuntimeError instead of returning silently wrong results.
Issue #5  — search() raises EmptyRAGError when no results are found so callers
            can react instead of silently receiving empty context.
Issue #10 — ChromaDB queries are wrapped in a configurable timeout via a
            threading.Timer watchdog (ChromaDB has no native query timeout).
"""

import threading
import chromadb
from rag.embeddings.ollama_embedder import OllamaEmbedder

# Timeout (seconds) for a single ChromaDB query. Override via subclass or env.
CHROMA_QUERY_TIMEOUT = 30


class EmptyRAGError(Exception):
    """Raised when a similarity search returns no documents."""
    pass


class ChromaStore:
    def __init__(
        self,
        persist_dir: str,
        collection_name: str,
        embedder: OllamaEmbedder,
    ):
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.embedder = embedder

        # ── Issue #3: stamp embed model name in collection metadata ──
        # If the collection already exists with a different model, raise immediately
        # rather than returning plausible-but-wrong embeddings silently.
        existing = self.client.get_or_create_collection(
            name=collection_name,
            metadata={
                "hnsw:space": "cosine",
                "embed_model": embedder.model,
            },
        )
        stored_model = existing.metadata.get("embed_model", "")
        if stored_model and stored_model != embedder.model:
            raise RuntimeError(
                f"Embedding model mismatch: ChromaDB collection '{collection_name}' "
                f"was built with '{stored_model}' but the current embedder is "
                f"'{embedder.model}'. Run 'python main.py --ingest' to rebuild the index."
            )
        self.collection = existing

    def upsert_documents(self, documents: list[dict]) -> int:
        """
        Insert or update documents.
        Each dict must have 'text' and 'metadata' keys.
        Returns count of documents upserted.
        """
        ids = []
        texts = []
        metadatas = []

        for i, doc in enumerate(documents):
            doc_id = doc["metadata"].get("source", f"doc-{i}")
            ids.append(doc_id)
            texts.append(doc["text"])
            metadatas.append(doc["metadata"])

        embeddings = self.embedder.embed_batch(texts)

        self.collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        return len(ids)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Similarity search. Returns list of:
          {"text": ..., "score": ..., "metadata": ...}

        Raises EmptyRAGError if no results are found (issue #5).
        Raises TimeoutError if ChromaDB does not respond within
        CHROMA_QUERY_TIMEOUT seconds (issue #10).
        """
        query_embedding = self.embedder.embed(query)

        # ── Issue #10: watchdog timeout ──
        result_holder: list = []
        exc_holder: list = []

        def _do_query():
            try:
                result_holder.append(
                    self.collection.query(
                        query_embeddings=[query_embedding],
                        n_results=top_k,
                        include=["documents", "metadatas", "distances"],
                    )
                )
            except Exception as e:
                exc_holder.append(e)

        thread = threading.Thread(target=_do_query, daemon=True)
        thread.start()
        thread.join(timeout=CHROMA_QUERY_TIMEOUT)

        if thread.is_alive():
            raise TimeoutError(
                f"ChromaDB query timed out after {CHROMA_QUERY_TIMEOUT}s. "
                "Check disk I/O or increase CHROMA_QUERY_TIMEOUT."
            )
        if exc_holder:
            raise exc_holder[0]

        results = result_holder[0]
        output = []
        for idx in range(len(results["ids"][0])):
            output.append(
                {
                    "text": results["documents"][0][idx],
                    "score": 1.0 - results["distances"][0][idx],  # cosine distance → similarity
                    "metadata": results["metadatas"][0][idx],
                }
            )

        # ── Issue #5: signal empty results explicitly ──
        if not output:
            raise EmptyRAGError(
                f"No documents found in ChromaDB for query: {query!r}. "
                "Run 'python main.py --ingest' if the collection is empty."
            )

        return output

    @property
    def count(self) -> int:
        return self.collection.count()

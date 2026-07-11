"""
ChromaDB vector store wrapper.

Handles collection creation, document upsert, and similarity search.
"""

import chromadb
from rag.embeddings.ollama_embedder import OllamaEmbedder


class ChromaStore:
    def __init__(
        self,
        persist_dir: str,
        collection_name: str,
        embedder: OllamaEmbedder,
    ):
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.embedder = embedder
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

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
        """
        query_embedding = self.embedder.embed(query)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        output = []
        for idx in range(len(results["ids"][0])):
            output.append(
                {
                    "text": results["documents"][0][idx],
                    "score": 1.0 - results["distances"][0][idx],  # cosine distance → similarity
                    "metadata": results["metadatas"][0][idx],
                }
            )
        return output

    @property
    def count(self) -> int:
        return self.collection.count()

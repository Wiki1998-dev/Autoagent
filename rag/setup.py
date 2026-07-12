"""
One-shot RAG pipeline setup:
  1. Load documents from data/
  2. Embed and store in ChromaDB
  3. Return a ready KnowledgeAdapter
"""

from rag.ingestion.loader import load_all_documents
from rag.embeddings.ollama_embedder import OllamaEmbedder
from rag.vectorstores.chroma_store import ChromaStore
from rag.retrieval.retriever import Retriever
from rag.adapter import KnowledgeAdapter
import config


def build_knowledge_adapter(force_reingest: bool = False) -> KnowledgeAdapter:
    """Build the full RAG pipeline and return a KnowledgeAdapter."""

    embedder = OllamaEmbedder(model=config.EMBED_MODEL)
    store = ChromaStore(
        persist_dir=config.CHROMA_PERSIST_DIR,
        collection_name=config.CHROMA_COLLECTION,
        embedder=embedder,
    )

    # Only ingest if empty or forced
    if store.count == 0 or force_reingest:
        print(f"[RAG] Ingesting documents from {config.DATA_DIR} ...")
        documents = load_all_documents(config.DATA_DIR)
        count = store.upsert_documents(documents)
        print(f"[RAG] Ingested {count} documents into ChromaDB.")
    else:
        print(f"[RAG] ChromaDB already has {store.count} documents. Skipping ingestion.")

    retriever = Retriever(store=store)
    return KnowledgeAdapter(retriever=retriever)

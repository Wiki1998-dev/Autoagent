# Retrieval-Augmented Generation (`/rag`)

This directory contains the engine for the local knowledge base, allowing the Evidence Agent to query past automotive failures and specs.

## Components
- **`ingest.py`**: Scans the `data/` folder, parses the files, chunks the text, generates embeddings using Ollama (`nomic-embed-text`), and upserts them into ChromaDB.
- **`retriever.py`**: Houses the query logic. Given a search string from the Evidence Agent, it performs semantic similarity searches against the ChromaDB collection (default: `autoagent_knowledge`) and returns the top `K` most relevant document snippets.
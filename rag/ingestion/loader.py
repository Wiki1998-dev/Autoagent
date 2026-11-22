"""
Loads all documents from the data/ directory into a list of dicts
ready for embedding and storage.

Each document becomes:
  {"text": <full content>, "metadata": {"source": <filename>, "category": <subfolder>}}
"""

import json
from pathlib import Path
from markitdown import MarkItDown  # <-- 1. Add this import

# nomic-embed-text has a ~2k-token context in Ollama; long documents (e.g.
# converted PDFs) must be split or the embedding call fails.
CHUNK_CHARS = 3000
CHUNK_OVERLAP = 300


def _chunk_text(text: str) -> list[str]:
    """Split text into overlapping chunks, preferring paragraph boundaries."""
    if len(text) <= CHUNK_CHARS:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_CHARS, len(text))
        if end < len(text):
            cut = text.rfind("\n\n", start + CHUNK_CHARS // 2, end)
            if cut != -1:
                end = cut
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(end - CHUNK_OVERLAP, start + 1)
    return chunks


def load_all_documents(data_dir: Path) -> list[dict]:
    """Walk every subfolder in data_dir and load files, using MarkItDown for complex formats."""
    documents: list[dict] = []

    md = MarkItDown()  # <-- 2. Initialize MarkItDown

    for category_dir in sorted(data_dir.iterdir()):
        if not category_dir.is_dir():
            continue
        category = category_dir.name  # e.g. "incidents", "scenarios"

        for file_path in sorted(category_dir.iterdir()):
            if file_path.suffix == ".md":
                text = file_path.read_text(encoding="utf-8")
            elif file_path.suffix == ".json":
                raw = json.loads(file_path.read_text(encoding="utf-8"))
                text = json.dumps(raw, indent=2)
            else:
                # ---> 3. START OF NEW MARKITDOWN LOGIC <---
                try:
                    print(f"  [MarkItDown] Converting {file_path.name} to Markdown...")
                    result = md.convert(str(file_path))
                    text = result.text_content
                except Exception as e:
                    print(f"  [Skip] Could not parse {file_path.name}. Error: {e}")
                    continue
                # ---> END OF NEW MARKITDOWN LOGIC <---

            chunks = _chunk_text(text)
            for idx, chunk in enumerate(chunks):
                metadata = {
                    "source": file_path.name,
                    "category": category,
                    "path": str(file_path),
                }
                if len(chunks) > 1:
                    metadata["chunk"] = idx
                documents.append({"text": chunk, "metadata": metadata})

    return documents
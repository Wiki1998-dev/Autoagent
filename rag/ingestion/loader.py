"""
Loads all documents from the data/ directory into a list of dicts
ready for embedding and storage.

Each document becomes:
  {"text": <full content>, "metadata": {"source": <filename>, "category": <subfolder>}}
"""

import json
from pathlib import Path


def load_all_documents(data_dir: Path) -> list[dict]:
    """Walk every subfolder in data_dir and load .md and .json files."""
    documents: list[dict] = []

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
                continue

            documents.append(
                {
                    "text": text,
                    "metadata": {
                        "source": file_path.name,
                        "category": category,
                        "path": str(file_path),
                    },
                }
            )

    return documents

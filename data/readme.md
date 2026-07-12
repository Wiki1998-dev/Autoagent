# Data & Knowledge Base (`/data`)

This directory is the local repository for all raw engineering documents, historical incident reports, and requirement specifications. 

## Usage
Files placed in this directory are **not** read live by the LLM. Instead, they must be ingested into the local vector database (ChromaDB). 

To ingest or update the data after adding new files here, run:
```bash
python main.py --ingest
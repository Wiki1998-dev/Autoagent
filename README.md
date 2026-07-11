# AutoAgent — Local Multi-Agent Engineering Copilot

A local, auditable, multi-agent system for automotive failure investigation.

## Architecture

```
User Request
  → Orchestrator (LangGraph)
    → Evidence Agent (RAG search)
    → [Parallel] Technical / Quality / Compliance Agents
    → Critic Agent (compare opinions)
    → Synthesis Agent (final summary)
    → Validator Agent (quality check)
    → Human Approval (interactive)
    → Automation Agent (save report + create ticket)
```

## Prerequisites

- Python 3.11+
- Ollama running locally with models pulled:
  ```bash
  ollama pull mistral
  ollama pull nomic-embed-text
  ```

## Setup

```bash
# 1. Clone/copy this directory
cd autoagent

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env if needed (model names, ports, etc.)

# 5. Run the demo investigation
python main.py
```

## Usage

```bash
# Default demo (SC-042 investigation)
python main.py

# Force re-ingest documents into ChromaDB
python main.py --ingest

# Custom investigation query
python main.py --query "Investigate sensor fusion failures in rain conditions"

# Use a different LLM model
python main.py --model llama3
```

## Project Structure

```
autoagent/
├── main.py              ← Entry point
├── config.py            ← Central configuration
├── rag/                 ← RAG pipeline
│   ├── adapter.py       ← KnowledgeAdapter interface
│   ├── setup.py         ← One-shot pipeline builder
│   ├── ingestion/       ← Document loading
│   ├── embeddings/      ← Ollama embeddings
│   ├── vectorstores/    ← ChromaDB storage
│   └── retrieval/       ← Retriever class
├── core/                ← Shared utilities
│   ├── llm.py           ← Ollama LLM wrapper
│   ├── schemas.py       ← Pydantic contracts
│   ├── skill_loader.py  ← Agent skill file loader
│   └── logger.py        ← Audit event logger
├── agents/              ← All 8 agents
├── orchestrator/        ← LangGraph state machine
│   ├── state.py         ← State definition
│   ├── nodes.py         ← Node functions
│   ├── routing.py       ← Conditional routing
│   └── graph.py         ← Graph builder
├── mcp_servers/         ← MCP tool servers
├── skills/              ← Agent skill markdown files
├── data/                ← Test dataset
├── workspace/           ← Output artifacts
│   ├── reports/         ← Saved investigation reports
│   └── tickets/         ← Created engineering tickets
└── audit/               ← Audit trail (events.jsonl)
```

## Audit Trail

Every agent action is logged to `audit/events.jsonl` as structured JSONL:

```json
{"timestamp": "...", "event_type": "agent_start", "agent": "evidence_agent", "task_id": "SC-042", "status": "ok", "data": {}}
```

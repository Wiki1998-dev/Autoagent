# AutoAgent

**A local, auditable multi-agent system for automotive failure investigation.**

AutoAgent orchestrates a pipeline of 8 specialised AI agents — all running locally via Ollama — to investigate failure scenarios, synthesise expert opinions, and produce actionable engineering reports. No cloud API keys required.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Agents](#agents)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [Audit Trail](#audit-trail)
- [Output Artifacts](#output-artifacts)

---

## Overview

AutoAgent is designed for automotive engineers who need a repeatable, traceable investigation workflow. Given a failure scenario (e.g. `SC-042`), the system:

1. Searches a local knowledge base (RAG) for similar past incidents and requirements
2. Runs three parallel specialist analyses — technical, quality, and compliance
3. Critiques and synthesises those analyses into a final report
4. Validates the report quality, retrying if needed
5. Presents the report for human approval before taking any action
6. On approval, saves the report and creates an engineering ticket

Everything runs locally. Every agent action is logged to a structured audit trail.

---

## Architecture

```
User Request
    │
    ▼
Orchestrator (LangGraph)
    │
    ├─► Evidence Agent          RAG search over incidents, requirements, test reports
    │       │
    │       ▼
    ├─► [Parallel]
    │   ├─► Technical Agent     Failure mode & root cause analysis
    │   ├─► Quality Agent       Process & quality system perspective
    │   └─► Compliance Agent    Safety standards & regulatory perspective
    │           │
    │           ▼
    ├─► Critic Agent            Compares and challenges the three opinions
    │       │
    │       ▼
    ├─► Synthesis Agent         Produces a unified final investigation report
    │       │
    │       ▼
    ├─► Validator Agent         Quality-checks the synthesis; retries if needed (max 2×)
    │       │
    │       ▼
    ├─► Human Approval          Interactive approve / reject step
    │       │
    │       ▼
    └─► Automation Agent        Saves report to disk, creates engineering ticket
```

The graph is built with **LangGraph** and uses typed state (`InvestigationState`) that flows through every node.

---

## Agents

| Agent | Role |
|-------|------|
| **Evidence Agent** | Searches ChromaDB for relevant prior incidents, requirements, and test reports. Produces a structured `EvidenceReport`. |
| **Technical Agent** | Analyses failure modes and probable root causes from an engineering perspective. |
| **Quality Agent** | Evaluates quality system implications — process gaps, FMEA coverage, inspection failures. |
| **Compliance Agent** | Assesses alignment with safety standards and regulatory requirements. |
| **Critic Agent** | Cross-examines the three specialist opinions; highlights agreements, conflicts, and blind spots. |
| **Synthesis Agent** | Consolidates all perspectives into a single coherent investigation report. |
| **Validator Agent** | Checks the synthesis for completeness and consistency. Triggers a retry loop (up to 2×) on failure. |
| **Automation Agent** | Saves the approved report to `workspace/reports/` and writes an engineering ticket to `workspace/tickets/`. |

Each agent loads its behaviour from a Markdown skill file in `skills/`, making prompts easy to review and edit without touching Python code.

---

## Prerequisites

- **Python 3.11+**
- **[Ollama](https://ollama.com)** running locally with the following models pulled:

```bash
ollama pull mistral            # default LLM
ollama pull nomic-embed-text   # embeddings
```

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/Wiki1998-dev/AutoAgent_123.git
cd AutoAgent_123

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy and (optionally) edit the environment file
cp .env.example .env
```

---

## Configuration

All settings are read from environment variables (with sensible defaults). Edit `.env` to override:

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `LLM_MODEL` | `mistral` | LLM model name |
| `EMBED_MODEL` | `nomic-embed-text` | Embedding model name |
| `LLM_TEMPERATURE` | `0.1` | LLM sampling temperature |
| `LLM_MAX_TOKENS` | `4096` | Max tokens per LLM call |
| `CHROMA_COLLECTION` | `autoagent_knowledge` | ChromaDB collection name |
| `RETRIEVAL_TOP_K` | `5` | Number of RAG results per query |
| `KNOWLEDGE_MCP_PORT` | `8100` | MCP knowledge server port |
| `ANALYSIS_MCP_PORT` | `8101` | MCP analysis server port |
| `AUTOMATION_MCP_PORT` | `8102` | MCP automation server port |

---

## Usage

### Run the demo investigation (SC-042)

```bash
python main.py
```

### Force re-ingest documents into ChromaDB

Run this after adding new files to `data/`:

```bash
python main.py --ingest
```

### Investigate a custom scenario

```bash
python main.py --query "Investigate sensor fusion failures in rain conditions"
```

### Use a different LLM model

```bash
python main.py --model llama3
```

### Combine flags

```bash
python main.py --ingest --model llama3 --query "Investigate camera occlusion at night"
```

---

## Project Structure

```
AutoAgent_123/
├── main.py                  Entry point and CLI
├── config.py                Central configuration (reads .env)
├── requirements.txt         Python dependencies
│
├── agents/                  Agent implementations
│   ├── base_specialist.py   Shared base class for Technical/Quality/Compliance
│   ├── evidence_agent.py    RAG-powered evidence gathering
│   ├── technical_agent.py
│   ├── quality_agent.py
│   ├── compliance_agent.py
│   ├── critic_agent.py
│   ├── synthesis_agent.py
│   ├── validator_agent.py
│   └── automation_agent.py
│
├── orchestrator/            LangGraph pipeline
│   ├── state.py             InvestigationState TypedDict
│   ├── nodes.py             Node functions (one per agent)
│   ├── routing.py           Conditional edge logic
│   └── graph.py             Graph construction and compilation
│
├── rag/                     Retrieval-Augmented Generation pipeline
│   ├── adapter.py           KnowledgeAdapter interface
│   ├── setup.py             One-shot pipeline builder
│   ├── ingestion/           Document loading
│   ├── embeddings/          Ollama embedding wrapper
│   ├── vectorstores/        ChromaDB persistence
│   └── retrieval/           Retriever class
│
├── skills/                  Agent prompt files (Markdown)
│   ├── evidence_agent.md
│   ├── technical_agent.md
│   ├── quality_agent.md
│   ├── compliance_agent.md
│   ├── critic_agent.md
│   ├── synthesis_agent.md
│   ├── validator_agent.md
│   └── automation_agent.md
│
├── data/                    Source documents for ingestion
├── workspace/
│   ├── reports/             Saved investigation reports (Markdown)
│   └── tickets/             Created engineering tickets
└── audit/
    └── events.jsonl         Structured audit log
```

---

## How It Works

### RAG Pipeline

On first run (or when `--ingest` is passed), AutoAgent loads documents from `data/`, embeds them with `nomic-embed-text` via Ollama, and stores them in a local ChromaDB vector store. Subsequent runs skip ingestion and query the existing store directly.

The Evidence Agent issues multiple targeted queries — e.g. searching separately for sensor failures, weather-related incidents, and relevant requirements — then deduplicates and packages results into a structured `EvidenceReport`.

### Agent Skills

Each agent's behaviour is defined in a plain Markdown file under `skills/`. The file describes the agent's role, rules, and expected output schema. This makes it straightforward to tune agent behaviour without touching Python code — just edit the relevant `.md` file.

### Validation and Retry

After synthesis, the Validator Agent checks the report for completeness and consistency. If validation fails, the graph routes back to the Synthesis Agent and retries. After two failed retries the pipeline proceeds to human review anyway, surfacing any validation warnings in the report.

### Human-in-the-Loop

The pipeline always pauses for human approval before executing any actions. The operator sees the full investigation report and proposed actions, then types `approve` or `reject`. Only on approval does the Automation Agent write files or create tickets.

---

## Audit Trail

Every agent action is appended to `audit/events.jsonl` as a structured JSONL record:

```json
{"timestamp": "2025-01-13T10:23:45Z", "event_type": "agent_start",    "agent": "evidence_agent", "task_id": "SC-042", "status": "ok",    "data": {}}
{"timestamp": "2025-01-13T10:23:52Z", "event_type": "agent_complete", "agent": "evidence_agent", "task_id": "SC-042", "status": "ok",    "data": {"incidents_found": 3, "gaps": 2}}
{"timestamp": "2025-01-13T10:24:10Z", "event_type": "investigation_complete", "agent": "orchestrator", "task_id": "SC-042", "status": "ok", "data": {"decision": "approve"}}
```

This log provides a complete, reproducible record of every investigation.

---

## Output Artifacts

After an approved investigation, two files are written:

| Path | Contents |
|------|----------|
| `workspace/reports/<task_id>.md` | Full investigation report in Markdown |
| `workspace/tickets/<task_id>.json` | Engineering follow-up ticket |

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `langgraph` | Multi-agent orchestration graph |
| `langchain-core` | LLM abstractions |
| `ollama` | Local LLM and embedding inference |
| `chromadb` | Local vector store |
| `pymupdf` | PDF document ingestion |
| `pydantic` | Structured output schemas |
| `fastmcp` | MCP tool servers |
| `streamlit` | (Optional) web UI |
| `python-dotenv` | Environment variable loading |

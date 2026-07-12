"""
Central configuration for AutoAgent.

Environment variables override defaults. Create a .env file
in the project root for local development.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ──────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
SKILLS_DIR = PROJECT_ROOT / "skills"
WORKSPACE_DIR = PROJECT_ROOT / "workspace"
AUDIT_LOG = PROJECT_ROOT / "audit" / "events.jsonl"

# ── LLM ────────────────────────────────────────────────────────
# Backend selector: "ollama" (default, fully local, single-request)
#                    "vllm"   (self-hosted, OpenAI-compatible, handles concurrency)
LLM_BACKEND = os.getenv("LLM_BACKEND", "ollama").lower()

LLM_MODEL = os.getenv("LLM_MODEL", "llama3.1")          # or llama3, etc.
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "4096"))

# Ollama-specific
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")

# vLLM-specific (OpenAI-compatible server: `vllm serve <model>`)
VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")
VLLM_API_KEY = os.getenv("VLLM_API_KEY", "not-needed")   # vLLM ignores this unless you enabled auth
VLLM_MODEL = os.getenv("VLLM_MODEL", "meta-llama/Llama-3.1-8B-Instruct")

# Whether to run the 3 specialist agents (Technical/Quality/Compliance) concurrently.
# Local Ollama serves one request at a time by default and can drop connections
# under concurrent load — so this defaults to sequential for "ollama" and
# concurrent for "vllm", but can be overridden explicitly.
_parallel_env = os.getenv("PARALLEL_SPECIALISTS")
if _parallel_env is not None:
    PARALLEL_SPECIALISTS = _parallel_env.lower() in ("1", "true", "yes")
else:
    PARALLEL_SPECIALISTS = LLM_BACKEND == "vllm"

# ── ChromaDB ───────────────────────────────────────────────────
CHROMA_PERSIST_DIR = str(PROJECT_ROOT / "rag" / "vectorstores" / "chroma_db")
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "autoagent_knowledge")

# ── Retrieval ──────────────────────────────────────────────────
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "5"))

# ── MCP Server Ports ──────────────────────────────────────────
KNOWLEDGE_MCP_PORT = int(os.getenv("KNOWLEDGE_MCP_PORT", "8100"))
ANALYSIS_MCP_PORT = int(os.getenv("ANALYSIS_MCP_PORT", "8101"))
AUTOMATION_MCP_PORT = int(os.getenv("AUTOMATION_MCP_PORT", "8102"))

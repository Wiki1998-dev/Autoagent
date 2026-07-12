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
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "9999999.0"))

# Ollama-specific
# Localhost defaults — set OLLAMA_BASE_URL in .env for cloud/K8s
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")

# vLLM-specific (OpenAI-compatible server: `vllm serve <model>`)
# Localhost default — set VLLM_BASE_URL in .env for cloud/K8s
VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")

# Never default to a placeholder string. If auth is enabled on
# vLLM, the operator MUST set VLLM_API_KEY; otherwise we use None (which
# the OpenAI client maps to an empty header — vLLM ignores it by default).
_raw_api_key = os.getenv("VLLM_API_KEY", "")
if _raw_api_key in ("", "not-needed"):
    import warnings
    warnings.warn(
        "VLLM_API_KEY is not set or is the placeholder 'not-needed'. "
        "If your vLLM server requires auth, set VLLM_API_KEY in .env.",
        stacklevel=1,
    )
    VLLM_API_KEY: str | None = None
else:
    VLLM_API_KEY = _raw_api_key

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

# Max simultaneous LLM calls across all threads.
# Default=1 (safe for Ollama). Increase for vLLM or multi-GPU setups.
LLM_MAX_CONCURRENT = int(os.getenv("LLM_MAX_CONCURRENT", "1" if LLM_BACKEND == "ollama" else "4"))

# ── ChromaDB ───────────────────────────────────────────────────
CHROMA_PERSIST_DIR = str(PROJECT_ROOT / "rag" / "vectorstores" / "chroma_db")
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "autoagent_knowledge")

# ── Retrieval ──────────────────────────────────────────────────
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "5"))

# ── MCP Server Ports ──────────────────────────────────────────
# These were defined but never referenced by the servers themselves.
# Kept here as documentation only. Pass them when launching servers:
#   uvicorn mcp_servers.knowledge_server:mcp --port $KNOWLEDGE_MCP_PORT
KNOWLEDGE_MCP_PORT = int(os.getenv("KNOWLEDGE_MCP_PORT", "8100"))
ANALYSIS_MCP_PORT  = int(os.getenv("ANALYSIS_MCP_PORT",  "8101"))
AUTOMATION_MCP_PORT = int(os.getenv("AUTOMATION_MCP_PORT", "8102"))

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
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "mistral")          # or llama3, etc.
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "4096"))

# ── ChromaDB ───────────────────────────────────────────────────
CHROMA_PERSIST_DIR = str(PROJECT_ROOT / "rag" / "vectorstores" / "chroma_db")
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "autoagent_knowledge")

# ── Retrieval ──────────────────────────────────────────────────
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "5"))

# ── MCP Server Ports ──────────────────────────────────────────
KNOWLEDGE_MCP_PORT = int(os.getenv("KNOWLEDGE_MCP_PORT", "8100"))
ANALYSIS_MCP_PORT = int(os.getenv("ANALYSIS_MCP_PORT", "8101"))
AUTOMATION_MCP_PORT = int(os.getenv("AUTOMATION_MCP_PORT", "8102"))

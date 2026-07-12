# Core Infrastructure (`/core`)

The `core` directory holds the foundational classes, type definitions, and shared utilities used across the entire AutoAgent ecosystem.

## Key Components
- **`state.py` (InvestigationState):** The heart of the LangGraph implementation. This defines the typed dictionary/Pydantic models that get passed from node to node. It contains fields like `query`, `evidence`, `technical_analysis`, `synthesis_draft`, `validation_errors`, and `retry_count`.
- **`config_loader.py` / `utils.py`:** Shared helper functions for interacting with environment variables, standardizing file paths, and formatting console outputs.
- **`llm_client.py`:** Base wrapper classes for interacting with the Ollama API, handling token limits, and managing retries for LLM timeouts.
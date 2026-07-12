#### `mcp_servers/README.md`
```markdown
# Model Context Protocol Servers (`/mcp_servers`)

This directory contains the [Model Context Protocol (MCP)](https://github.com/mcp) server implementations. MCP is used to decouple the underlying capabilities from the agents themselves, exposing tools as standard, discoverable API endpoints.

## Included Servers
1. **Knowledge Server (`port 8100`)**: Exposes search tools allowing agents to query the ChromaDB vector store.
2. **Analysis Server (`port 8101`)**: Provides specific analytical tools, calculators, or logic validators required by the Technical and Critic agents.
3. **Automation Server (`port 8102`)**: Handles file system operations (saving the final Markdown report to `/workspace/reports`) and external system mocking (generating engineering tickets in `/workspace/tickets`).

*Run configurations for these ports can be modified in the root `.env` file.*
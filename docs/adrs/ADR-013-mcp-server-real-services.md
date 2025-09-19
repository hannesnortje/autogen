# ADR-013: MCP Server Real Services Integration

## Status
Proposed

## Context
The MCP server initially had dummy implementations for all endpoints. To provide real functionality for VS Code integration, the server must connect to actual AutoGen services (memory, orchestrator, agents) while maintaining proper error handling and graceful degradation.

## Decision
- **Real Memory Service**: `/memory/search` and `/objective/add` endpoints now use actual `MemoryService` with Qdrant backend.
- **Real Orchestrator**: `/orchestrate/start` creates actual `AgentOrchestrator` instances with session management.
- **Graceful Degradation**: When `GEMINI_API_KEY` is not available, the server starts but orchestration endpoints return proper error messages.
- **Session Management**: Active sessions are stored in memory (for production, use Redis or database).
- **Error Handling**: All endpoints have proper try/catch blocks with structured logging and HTTP error responses.
- **Settings Removal**: Removed confusing `/settings` page; port is set only at server startup.

## Implementation Details
- **Memory Integration**: Memory search sets project scope and writes objectives to memory with proper metadata.
- **Orchestrator Integration**: Creates agent configs based on request and manages session lifecycle.
- **Logging**: All operations are logged with correlation IDs and structured data.
- **Testing**: Comprehensive test suite covers both success and error scenarios.

## Consequences
- MCP server now provides real functionality instead of dummy responses.
- VS Code integration can rely on actual AutoGen capabilities.
- Server gracefully handles missing dependencies (API keys, services).
- All operations are observable through structured logging.

## References
- `src/autogen_mcp/mcp_server.py`
- `tests/test_mcp_server_integration.py`
- `src/autogen_mcp/memory.py`
- `src/autogen_mcp/orchestrator.py`

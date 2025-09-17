# ADR-014: Real-time Updates and File Operations

## Status
Proposed

## Context
VS Code integration requires the MCP server to support file operations (reading, writing workspace files) and real-time communication for streaming agent progress and session updates. This enables seamless integration where agents can directly modify workspace files and VS Code can receive live updates.

## Decision
- **File Operations**: Added `/workspace/write` and `/workspace/files` endpoints for direct workspace file manipulation.
- **WebSocket Support**: Implemented WebSocket endpoint `/ws/session/{session_id}` for real-time bidirectional communication.
- **Connection Management**: Created `ConnectionManager` class to handle multiple concurrent WebSocket connections per session.
- **Memory Integration**: File operations are automatically logged to memory service for traceability.
- **Session State**: WebSocket connections are tied to orchestration sessions for proper lifecycle management.

## Implementation Details
- **File Write**: Creates necessary directories, writes content, and logs to memory with artifact scope.
- **File Listing**: Recursively lists all files and directories in workspace with relative paths.
- **WebSocket Protocol**: JSON-based messaging with `type` field for message categorization.
- **Error Handling**: All operations have proper exception handling with structured logging.
- **Security**: File operations are restricted to configured workspace directory.

## Consequences
- VS Code extension can directly write agent outputs to workspace files.
- Real-time progress updates enable responsive user experience.
- File operations are traceable through memory service.
- WebSocket connections allow bidirectional communication for advanced features.
- Foundation established for real-time collaboration between agents and VS Code.

## References
- `src/autogen_mcp/mcp_server.py` (WebSocket and file endpoints)
- `tests/test_mcp_file_websocket.py`
- WebSocket protocol: `/ws/session/{session_id}`
- File endpoints: `/workspace/write`, `/workspace/files`

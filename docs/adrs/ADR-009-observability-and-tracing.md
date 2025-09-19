# ADR-009: Observability, Logging, and Tracing

## Status
Proposed

## Context
Robust observability is required for debugging, auditing, and performance monitoring in AutoGen MCP. The system must support structured logging, correlation IDs, and optional distributed tracing (OpenTelemetry).

## Decision
- **Structured logging**: All logs use JSON format via `JsonFormatter` in `observability.py`.
- **Correlation IDs**: Every log record includes a correlation/session ID, propagated across layers (memory, orchestrator, server).
- **Secret redaction**: All log fields are recursively redacted for secrets (API keys, tokens, passwords) before output.
- **Verbosity**: Log level is configurable via environment variable or argument.
- **Tracing (optional)**: OpenTelemetry hooks may be added to instrument key operations (tool calls, memory ops, agent turns). Tracing is optional and can be enabled/disabled via config.
- **Session log inspection**: Integration tests and CLI support session log review for debugging.

## Consequences
- Logs are machine-parseable, secure, and traceable across distributed components.
- Tracing can be enabled for deep diagnostics without impacting default performance.
- Observability is consistent across CLI, server, and agent orchestration.

## References
- `src/autogen_mcp/observability.py`
- `src/autogen_mcp/memory.py`
- `src/autogen_mcp/orchestrator.py`
- `src/autogen_mcp/cli.py`
- `src/autogen_mcp/mcp_server.py`

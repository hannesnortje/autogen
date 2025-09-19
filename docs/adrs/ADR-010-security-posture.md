# ADR-010: Security Posture

## Status
Proposed

## Context
AutoGen MCP must ensure that sensitive data is never leaked, stored, or transmitted insecurely. Security controls are required for secret redaction, outbound call/domain allowlisting, and payload filtering.

## Decision
- **Secret redaction**: All logs and memory writes are recursively redacted for secrets (API keys, tokens, passwords) using regex and key matching. Attempts to store secrets in memory are blocked and logged as policy violations.
- **Outbound allowlist**: All outbound tool calls and network requests are checked against a configurable allowlist. Disallowed domains or endpoints are blocked and logged.
- **Payload filters**: Memory and log payloads are filtered to block secrets and sensitive data. Violations raise errors and are surfaced in logs.
- **Test coverage**: Unit, integration, and E2E tests verify that secrets are never stored or logged, and that policy violations are blocked.

## Consequences
- Sensitive data is protected by default. Violations are blocked and surfaced early.
- Security posture is consistent across all components (memory, logging, tools).
- Tests ensure ongoing compliance as the system evolves.

## References
- `src/autogen_mcp/observability.py`
- `src/autogen_mcp/memory.py`
- `src/autogen_mcp/security.py`
- `tests/test_memory_service.py`
- `tests/test_big_autogen_system.py`

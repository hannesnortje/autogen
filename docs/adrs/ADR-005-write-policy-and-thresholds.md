# ADR-005: Write Policy, Summarization, and Pruning

## Status
Proposed

## Context
AutoGen MCP must ensure that memory writes are policy-compliant, organized by project, and that memory does not grow unbounded. Summarization and pruning are required for scalability and relevance.

## Decision
- **Per-turn write hooks**: `MemoryService` exposes `write_decision`, `write_snippet`, and `write_artifact` for structured event logging per agent turn.
- **Per-project collections**: Memory events are written to collections named `memory_<project_slug>`, enforcing project isolation.
- **Summarization**: Threads are summarized after N events (configurable, default 20). Summaries are written as `thread_summary` events.
- **Pruning**: Low-importance items (as marked in `metadata['importance']`) are pruned via `prune_low_importance`. Importance is a float [0,1]; items below threshold are deleted.
- **Policy enforcement**: Secrets are blocked from being written to memory. Policy violations raise errors and are logged.

## Consequences
- Memory is organized, scalable, and secure.
- Summarization and pruning keep memory relevant and performant.
- Policy violations are surfaced early and blocked.
- All logic is tested and included in the big integration test.

## References
- `src/autogen_mcp/memory.py`
- `tests/test_memory_service.py`
- `tests/test_big_autogen_system.py`
- `src/autogen_mcp/summarizer_nightly.py`

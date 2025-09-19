# ADR-004: Retrieval and Fusion Strategy

## Status
Proposed

## Context
Hybrid search in AutoGen MCP combines dense (embedding-based) and sparse (TF-IDF) retrieval to maximize recall and precision. Agents must search memory in a tiered order: thread → project → objectives → agent → global. Results should include scores and scope metadata for downstream ranking and explainability.

## Decision
- Hybrid search is implemented via `HybridSearchService`, which fuses dense and sparse results using Reciprocal Rank Fusion (RRF).
- Tiered search order is enforced: thread, project, objectives, agent, global. Each tier is searched in order until enough results are found.
- The `search(query, scopes, k)` method returns a list of results, each with:
  - `id`: document or point ID
  - `score`: fused score
  - `scope`: memory scope (thread, project, etc.)
  - `metadata`: optional payload fields (e.g., text, thread_id)
- Edge cases (empty corpus, long query, stop words) are handled gracefully (return empty or best-effort results).

## Consequences
- Agents can retrieve relevant context from the most specific to most general memory scopes.
- Results are explainable and can be filtered or re-ranked downstream.
- CI tests cover fusion math, tiered search, and edge cases.

## References
- `src/autogen_mcp/hybrid_search_service.py`
- `src/autogen_mcp/hybrid_search.py`
- `tests/test_hybrid_integration.py`
- `tests/test_hybrid_search.py`

# ADR-003: Embeddings Health and Determinism

## Status
Proposed

## Context
The system relies on FastEmbed for text embeddings, which are used for dense retrieval in Qdrant. Embeddings must be deterministic (same input yields same output) and the embedding service must be health-checked to ensure reliability.

## Decision
- The `EmbeddingService` abstraction wraps FastEmbed and exposes `encode_one`, `encode_many`, and `dim`.
- Health of the embedding service is defined as the ability to encode a string and return a vector of the expected dimension.
- Determinism is defined as: for a given input string, repeated calls to `encode_one` must return identical vectors (within floating-point tolerance).
- Tests are added to:
  - Check that `EmbeddingService.encode_one` is deterministic for repeated calls.
  - Check that `EmbeddingService` returns vectors of the expected dimension.
  - Check that the embedding service is healthy (can encode and returns correct shape).

## Consequences
- Embedding failures or non-determinism will be caught by CI.
- System health checks can include embedding service status.
- Documentation and tests ensure future maintainers understand and verify embedding health/determinism.

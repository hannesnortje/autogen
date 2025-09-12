"""
Big integration test for AutoGen MCP: covers memory, hybrid search, summarization, security, observability, and CI/CD.
"""

import pytest
from autogen_mcp.memory import MemoryService
from autogen_mcp.hybrid_search import SparseRetriever, reciprocal_rank_fusion
from autogen_mcp.observability import get_logger, JsonFormatter
from autogen_mcp.security import is_url_allowed
from autogen_mcp.summarizer_nightly import summarize_all_threads


def test_big_autogen_system(monkeypatch):
    # 7. Policy rule enforcement and pruning
    svc2 = MemoryService(collection="bigtest_prune", summary_threshold=3)
    svc2.ensure_collection()
    for i in range(5):
        importance = 0.1 if i < 2 else 0.9
        svc2.write_event(
            "thread",
            thread_id="t5",
            text=f"event {i}",
            metadata={"importance": importance},
        )
    pruned = svc2.prune_low_importance(importance_threshold=0.2, limit=10)
    assert pruned == 2
    # 1. Memory basic write/read and secret blocking
    svc = MemoryService(collection="bigtest", summary_threshold=3)
    svc.ensure_collection()
    for i in range(3):
        svc.write_event("thread", thread_id="t1", text=f"event {i}")
    points = svc.list_thread_events("t1")
    assert len(points) >= 3
    # Secret block
    with pytest.raises(ValueError):
        svc.write_event(
            "thread", thread_id="t1", text="api_key=sk-1234567890abcdef1234567890abcdef"
        )

    # 2. Summarization
    sid = svc.summarize_thread("t1")
    assert isinstance(sid, str)

    # 3. Hybrid search (sparse)
    DOCS = [
        "hybrid search combines dense and sparse retrieval",
        "dense retrieval uses embeddings",
        "sparse retrieval uses tf-idf or bm25",
    ]
    IDS = [1, 2, 3]
    retriever = SparseRetriever(DOCS, IDS)
    results = retriever.search("tf-idf retrieval", top_k=2)
    assert any(r[0] == 3 for r in results)
    fused = reciprocal_rank_fusion([1, 2, 3], [3, 2, 1], k=3)
    assert set(fused) == {1, 2, 3}

    # 3b. Hybrid search edge cases
    # Empty corpus
    empty_retriever = SparseRetriever([], [])
    assert empty_retriever.search("anything", top_k=3) == []
    # Long query
    long_query = "this is a very long query with many words that may or may not match any document in the corpus but should not crash or error out"
    long_results = retriever.search(long_query, top_k=3)
    assert isinstance(long_results, list)
    # Stop words
    stop_query = "the and if but or"
    stop_results = retriever.search(stop_query, top_k=3)
    assert isinstance(stop_results, list)

    # 4. Observability: logger/correlation
    logger = get_logger(
        "autogen.bigtest", correlation_id="cid-bigtest", verbosity="INFO"
    )
    import io
    import logging

    buf = io.StringIO()
    handler = logging.StreamHandler(buf)
    handler.setFormatter(JsonFormatter())
    logger.handlers = [handler]
    logger.info(
        "Big test log", extra={"extra": {"payload": "api_key=sk-1234567890abcdef"}}
    )
    logs = buf.getvalue().splitlines()
    for line in logs:
        assert "[REDACTED]" in line
        assert "sk-1234567890abcdef" not in line

    # 5. Security: outbound call allowlist
    assert is_url_allowed("https://api.github.com/repos/foo/bar")
    assert not is_url_allowed("https://evil.com/api")

    # 6. Embeddings health and determinism
    from autogen_mcp.embeddings import EmbeddingService

    emb = EmbeddingService()
    # Health: can encode a string and returns correct shape
    vec = emb.encode_one("test string")
    dim = emb.dim()
    assert isinstance(vec, list)
    assert all(isinstance(x, float) for x in vec)
    assert len(vec) == dim
    # Determinism: repeated calls yield same output (within tolerance)
    text = "deterministic embedding test"
    vec1 = emb.encode_one(text)
    vec2 = emb.encode_one(text)
    assert len(vec1) == len(vec2)
    for a, b in zip(vec1, vec2):
        assert abs(a - b) < 1e-6

    # 6. Nightly summarizer script runs (dummy patch)
    class DummyMem:
        def __init__(self, collection):
            self.collection = collection
            self.q = self

        def scroll(self, collection, must, limit, with_payload):
            return {
                "result": {
                    "points": [
                        {"payload": {"thread_id": "t1"}},
                        {"payload": {"thread_id": "t2"}},
                    ]
                }
            }

        def summarize_thread(self, thread_id):
            return f"summary-{thread_id}"

    class DummyQdrant:
        def list_collections(self):
            return ["foo", "bar"]

    monkeypatch.setattr("autogen_mcp.summarizer_nightly.MemoryService", DummyMem)
    monkeypatch.setattr("autogen_mcp.summarizer_nightly.QdrantWrapper", DummyQdrant)
    summarize_all_threads()

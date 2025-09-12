from autogen_mcp.hybrid_search import SparseRetriever, reciprocal_rank_fusion

DOCS = [
    "hybrid search combines dense and sparse retrieval",
    "dense retrieval uses embeddings",
    "sparse retrieval uses tf-idf or bm25",
    "reciprocal rank fusion improves results",
    "this is a test document",
]
IDS = [1, 2, 3, 4, 5]


def test_sparse_retriever_basic():
    retriever = SparseRetriever(DOCS, IDS)
    results = retriever.search("tf-idf retrieval", top_k=3)
    ids = [r[0] for r in results]
    assert 3 in ids  # Should match the tf-idf doc
    assert len(results) <= 3


def test_rrf_fusion():
    a = [1, 2, 3]
    b = [3, 2, 1]
    fused = reciprocal_rank_fusion(a, b, k=3)
    assert set(fused) == {1, 2, 3}
    assert fused[0] in (1, 2, 3)


def test_sparse_retriever_empty_corpus():
    retriever = SparseRetriever([], [])
    results = retriever.search("anything", top_k=3)
    assert results == []


def test_sparse_retriever_long_query():
    retriever = SparseRetriever(DOCS, IDS)
    long_query = "this is a very long query with many words that may or may not match any document in the corpus but should not crash or error out"
    results = retriever.search(long_query, top_k=3)
    assert isinstance(results, list)


def test_sparse_retriever_stop_words():
    retriever = SparseRetriever(DOCS, IDS)
    stop_query = "the and if but or"
    results = retriever.search(stop_query, top_k=3)
    # Should return empty or best-effort, but not error
    assert isinstance(results, list)

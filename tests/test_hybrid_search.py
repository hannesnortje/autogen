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

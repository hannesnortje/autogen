import time
import uuid

import pytest

from autogen_mcp.embeddings import EmbeddingService
from autogen_mcp.hybrid_search_service import HybridSearchService
from autogen_mcp.qdrant_client import QdrantWrapper


@pytest.mark.integration
@pytest.mark.timeout(60)
def test_hybrid_dense_and_sparse_cases():
    q = QdrantWrapper()
    emb = EmbeddingService()

    # Ensure Qdrant is up
    deadline = time.time() + 20
    while time.time() < deadline and not q.health():
        time.sleep(1)
    if not q.health():
        pytest.skip("Qdrant not running; start with: docker compose up -d")

    dim = emb.dim()
    name = f"hyb_{uuid.uuid4().hex[:8]}"
    q.create_collection(name, vector_size=dim)

    docs = [
        "hybrid search combines dense and sparse retrieval",
        "dense retrieval uses semantic embeddings and encoders",
        "sparse retrieval uses tf idf and bm25 keywords",
        "reciprocal rank fusion can improve results",
        "completely unrelated text for contrast",
    ]
    ids = [1, 2, 3, 4, 5]

    svc = HybridSearchService()
    svc.build_sparse(docs, ids)
    svc.index_dense(name, ids, docs)

    # Query favoring sparse keywords
    q_sparse = "bm25 tf-idf retrieval"
    fused_sparse = svc.search(name, q_sparse, k=3)
    assert 3 in fused_sparse  # the sparse-friendly doc appears near top

    # Query favoring dense semantics
    q_dense = "semantic embeddings for retrieval"
    fused_dense = svc.search(name, q_dense, k=3)
    assert 2 in fused_dense  # the dense-friendly doc appears near top

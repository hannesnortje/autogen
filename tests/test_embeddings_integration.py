import time
import uuid

import pytest

from autogen_mcp.embeddings import EmbeddingService
from autogen_mcp.qdrant_client import QdrantWrapper


@pytest.mark.integration
@pytest.mark.timeout(45)
def test_encode_store_query_roundtrip():
    q = QdrantWrapper()

    # Ensure Qdrant is up (poll briefly)
    deadline = time.time() + 15
    while time.time() < deadline and not q.health():
        time.sleep(1)

    if not q.health():
        pytest.skip("Qdrant not running; start with: docker compose up -d")

    emb = EmbeddingService()
    dim = emb.dim()

    # Create a temp collection matching embedding size
    name = f"emb_{uuid.uuid4().hex[:8]}"
    q.create_collection(name, vector_size=dim)

    text = "hybrid retrieval is powerful"
    vec = emb.encode_one(text)

    q.upsert_point(
        name,
        point_id=1,
        vector=vec,
        payload={"scope": "thread", "text": text},
    )

    res = q.search(name, vector=vec, limit=1)
    assert res.get("status") == "ok"
    top = res.get("result", [])
    assert top and top[0].get("id") == 1


def test_embedding_service_health_and_dim():
    emb = EmbeddingService()
    # Health: can encode a string and returns correct shape
    vec = emb.encode_one("test string")
    dim = emb.dim()
    assert isinstance(vec, list)
    assert all(isinstance(x, float) for x in vec)
    assert len(vec) == dim


def test_embedding_service_determinism():
    emb = EmbeddingService()
    text = "deterministic embedding test"
    vec1 = emb.encode_one(text)
    vec2 = emb.encode_one(text)
    # Determinism: repeated calls yield same output (within tolerance)
    assert len(vec1) == len(vec2)
    for a, b in zip(vec1, vec2):
        assert abs(a - b) < 1e-6

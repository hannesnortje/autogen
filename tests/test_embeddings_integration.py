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

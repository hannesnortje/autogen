import time
import uuid

import pytest

from autogen_mcp.qdrant_client import QdrantWrapper


@pytest.mark.integration
@pytest.mark.timeout(30)
def test_qdrant_health_and_basic_ops():
    # Allow skipping if Qdrant not running locally
    q = QdrantWrapper()
    # Poll briefly in case container is still starting
    deadline = time.time() + 10
    is_up = q.health()
    while not is_up and time.time() < deadline:
        time.sleep(1)
        is_up = q.health()

    if not is_up:
        pytest.skip("Qdrant not running; start with: docker compose up -d")

    name = f"test_{uuid.uuid4().hex[:8]}"
    q.create_collection(name)
    cols = q.list_collections()
    assert name in cols

    # Minimal upsert with fake vector and payload
    vec = [0.0] * 384
    payload = {"scope": "thread", "text": "hello world"}
    resp = q.upsert_point(name, point_id=1, vector=vec, payload=payload)
    assert resp.get("status") == "ok"

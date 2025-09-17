from autogen_mcp.memory import MemoryService


def test_memory_write_and_list(monkeypatch):

    svc = MemoryService(collection="mem_test", summary_threshold=3)
    svc.ensure_collection()

    # Write 3 events
    for i in range(3):
        svc.write_event("thread", thread_id="t1", text=f"event {i}")

    points = svc.list_thread_events("t1")
    assert len(points) >= 3
    texts = [p["payload"]["text"] for p in points[-3:]]
    assert texts == ["event 0", "event 1", "event 2"]


def test_memory_summarize_creates_summary(monkeypatch):
    svc = MemoryService(collection="mem_sum", summary_threshold=3)
    svc.ensure_collection()

    for i in range(3):
        svc.write_event("thread", thread_id="t2", text=f"line {i}")

    sid = svc.summarize_thread("t2")
    assert isinstance(sid, str)

    points = svc.list_thread_events("t2")
    summary_points = [
        p for p in points if p["payload"].get("scope") == "thread_summary"
    ]
    assert summary_points, "Expected a thread_summary event to be written"


def test_memory_blocks_secret_storage():
    svc = MemoryService(collection="mem_block_secret", summary_threshold=3)
    svc.ensure_collection()
    # Should raise ValueError for secret in text
    try:
        svc.write_event(
            "thread", thread_id="t3", text="api_key=sk-1234567890abcdef1234567890abcdef"
        )
        assert False, "Expected ValueError for secret in text"
    except ValueError as e:
        assert "blocked by policy" in str(e)
    # Should raise ValueError for secret in metadata
    try:
        svc.write_event(
            "thread", thread_id="t3", text="no secret", metadata={"token": "mytoken123"}
        )
        assert False, "Expected ValueError for secret in metadata"
    except ValueError as e:
        assert "blocked by policy" in str(e)


def test_memory_prune_low_importance(monkeypatch):
    svc = MemoryService(collection="mem_prune", summary_threshold=3)
    svc.ensure_collection()
    # Insert events with varying importance
    for i in range(5):
        importance = 0.1 if i < 2 else 0.9
        svc.write_event(
            "thread",
            thread_id="t4",
            text=f"event {i}",
            metadata={"importance": importance},
        )
    # Prune low-importance (threshold 0.2 should remove first 2)
    pruned = svc.prune_low_importance(importance_threshold=0.2, limit=10)
    assert pruned == 2

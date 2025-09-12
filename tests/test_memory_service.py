from autogen_mcp.memory import MemoryService, MemoryConfig


def test_memory_write_and_list(monkeypatch):
    svc = MemoryService(MemoryConfig(collection="mem_test", summary_threshold=3))
    svc.ensure_collection()

    # Write 3 events
    for i in range(3):
        svc.write_event("thread", thread_id="t1", text=f"event {i}")

    points = svc.list_thread_events("t1")
    assert len(points) >= 3
    texts = [p["payload"]["text"] for p in points[-3:]]
    assert texts == ["event 0", "event 1", "event 2"]


def test_memory_summarize_creates_summary(monkeypatch):
    svc = MemoryService(MemoryConfig(collection="mem_sum", summary_threshold=3))
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

import sys
import os

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)
from autogen_mcp.summarizer_nightly import summarize_all_threads


def test_summarizer_nightly_runs(monkeypatch):
    """Test summarize_all_threads runs with dummy services."""

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

    monkeypatch.setattr(
        "autogen_mcp.summarizer_nightly.MemoryService",
        DummyMem,
    )
    monkeypatch.setattr(
        "autogen_mcp.summarizer_nightly.QdrantWrapper",
        DummyQdrant,
    )

    summarize_all_threads()

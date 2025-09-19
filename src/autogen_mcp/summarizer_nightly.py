"""
Nightly summarizer script for AutoGen MCP.
Summarizes all threads in all collections and writes summary events to memory.
"""

from autogen_mcp.memory import MemoryService
from autogen_mcp.qdrant_client import QdrantWrapper
from autogen_mcp.observability import get_logger


def summarize_all_threads():
    logger = get_logger("autogen.summarizer_nightly")
    q = QdrantWrapper()
    collections = q.list_collections()
    logger.info(f"Found collections: {collections}")
    for collection in collections:
        mem = MemoryService(collection=collection)
        # Find all unique thread_ids in the collection
        points = mem.q.scroll(collection, must=[], limit=10000, with_payload=True)[
            "result"
        ]["points"]
        thread_ids = set(
            p["payload"].get("thread_id")
            for p in points
            if p["payload"].get("thread_id")
        )
        logger.info(f"Collection {collection}: {len(thread_ids)} threads")
        for thread_id in thread_ids:
            sid = mem.summarize_thread(thread_id)
            if sid:
                logger.info(
                    f"Summarized thread {thread_id} in {collection}",
                    extra={"extra": {"summary_id": sid}},
                )


if __name__ == "__main__":
    summarize_all_threads()

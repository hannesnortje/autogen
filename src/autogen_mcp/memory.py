# Legacy/test compatibility: MemoryService wraps MemoryConfig for test imports

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from autogen_mcp.qdrant_client import QdrantWrapper
from autogen_mcp.observability import get_logger


@dataclass
class MemoryConfig:
    collection: str = "memory_default"
    summary_threshold: int = 20  # summarize every N events per thread
    correlation_id: Optional[str] = None
    # q and logger are set in __post_init__
    q: QdrantWrapper = None
    logger: Any = None

    def __post_init__(self):
        self.q = QdrantWrapper()
        self.logger = get_logger("autogen.memory", correlation_id=self.correlation_id)

    def ensure_collection(self, vector_size: int = 8) -> None:
        try:
            self.q.create_collection(self.collection, vector_size=vector_size)
            self.logger.info(
                "Created collection",
                extra={
                    "extra": {
                        "collection": self.collection,
                        "vector_size": vector_size,
                    }
                },
            )
        except Exception as e:
            self.logger.debug(
                "Collection exists or error",
                extra={"extra": {"collection": self.collection, "error": str(e)}},
            )

    def write_event(
        self,
        scope: str,
        thread_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        payload = {
            "scope": scope,
            "thread_id": thread_id,
            "text": text,
            "metadata": metadata or {},
            "ts": time.time(),
        }
        pid = str(uuid.uuid4())
        vec = [0.0] * 8
        self.q.upsert_point(self.collection, pid, vec, payload)
        self.logger.info(
            "Memory event written",
            extra={
                "extra": {
                    "collection": self.collection,
                    "pid": pid,
                    "scope": scope,
                    "thread_id": thread_id,
                }
            },
        )
        return pid

    def list_thread_events(
        self, thread_id: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        resp = self.q.scroll(
            self.collection,
            must=[{"key": "thread_id", "match": {"value": thread_id}}],
            limit=limit,
            with_payload=True,
        )
        points = resp.get("result", {}).get("points", [])
        points.sort(key=lambda p: p.get("payload", {}).get("ts", 0))
        return points

    def summarize_thread(self, thread_id: str) -> Optional[str]:
        events = self.list_thread_events(thread_id, limit=1000)
        if not events:
            return None
        if len(events) < self.summary_threshold:
            return None
        last_texts = [p["payload"].get("text", "") for p in events[-5:]]
        summary = " \n".join(last_texts)
        sid = self.write_event(
            scope="thread_summary",
            thread_id=thread_id,
            text=summary,
            metadata={"source_count": len(events), "type": "summary"},
        )
        return sid


# Legacy/test compatibility: MemoryService wraps MemoryConfig for test imports
class MemoryService(MemoryConfig):
    pass

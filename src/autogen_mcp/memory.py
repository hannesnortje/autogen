from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from autogen_mcp.qdrant_client import QdrantWrapper


@dataclass
class MemoryConfig:
    collection: str = "memory_default"
    summary_threshold: int = 20  # summarize every N events per thread


class MemoryService:
    def __init__(self, config: MemoryConfig | None = None) -> None:
        self.config = config or MemoryConfig()
        self.q = QdrantWrapper()

    def ensure_collection(self, vector_size: int = 8) -> None:
        # vector_size is minimal for now; summaries may store tiny vectors
        try:
            self.q.create_collection(self.config.collection, vector_size=vector_size)
        except Exception:
            # Assume already exists
            pass

    def write_event(
        self,
        scope: str,
        thread_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Write a memory event (no vector yet)."""
        payload = {
            "scope": scope,
            "thread_id": thread_id,
            "text": text,
            "metadata": metadata or {},
            "ts": time.time(),
        }
        pid = str(uuid.uuid4())
        # Use a zero-vector placeholder for now
        vec = [0.0] * 8
        self.q.upsert_point(self.config.collection, pid, vec, payload)
        return pid

    def list_thread_events(
        self, thread_id: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        resp = self.q.scroll(
            self.config.collection,
            must=[{"key": "thread_id", "match": {"value": thread_id}}],
            limit=limit,
            with_payload=True,
        )
        points = resp.get("result", {}).get("points", [])
        # Sort by timestamp if present
        points.sort(key=lambda p: p.get("payload", {}).get("ts", 0))
        return points

    def summarize_thread(self, thread_id: str) -> Optional[str]:
        events = self.list_thread_events(thread_id, limit=1000)
        if not events:
            return None
        if len(events) < self.config.summary_threshold:
            return None
        # naive summary: concatenate last 5 texts
        last_texts = [p["payload"].get("text", "") for p in events[-5:]]
        summary = " \n".join(last_texts)
        sid = self.write_event(
            scope="thread_summary",
            thread_id=thread_id,
            text=summary,
            metadata={"source_count": len(events), "type": "summary"},
        )
        return sid

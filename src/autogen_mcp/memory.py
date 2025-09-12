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
        from autogen_mcp.observability import redact_secrets
        import re

        # Secret patterns to block
        secret_patterns = [
            r"(?i)api[_-]?key[\s:=]+[\w-]+",
            r"(?i)token[\s:=]+[\w-]+",
            r"(?i)password[\s:=]+[\w-]+",
            r"sk-[A-Za-z0-9]{32,}",
        ]

        sensitive_keys = {"token", "api_key", "apikey", "password", "secret"}

        def contains_secret(val):
            if isinstance(val, dict):
                # Block if any key is sensitive, or any value contains a secret
                for k, v in val.items():
                    if isinstance(k, str) and k.lower() in sensitive_keys:
                        return True
                    if contains_secret(v):
                        return True
                return False
            if isinstance(val, list):
                return any(contains_secret(v) for v in val)
            if isinstance(val, str):
                return any(re.search(pat, val) for pat in secret_patterns)
            return False

        if contains_secret(text) or contains_secret(metadata or {}):
            self.logger.warning(
                "Blocked attempt to store secret in memory",
                extra={
                    "extra": {
                        "scope": scope,
                        "thread_id": thread_id,
                        "event": "blocked_secret_storage",
                    }
                },
            )
            raise ValueError("Attempted to store secret in memory; blocked by policy.")

        payload = {
            "scope": scope,
            "thread_id": thread_id,
            "text": redact_secrets(text),
            "metadata": redact_secrets(metadata or {}),
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
    def set_project(self, project_slug: str):
        """Switch to per-project collection for memory events."""
        self.collection = f"memory_{project_slug}"
        self.ensure_collection()

    def prune_low_importance(
        self, importance_threshold: float = 0.2, limit: int = 1000
    ) -> int:
        """Prune (delete) low-importance items from the current collection."""
        # For demo: assume importance is in metadata['importance'] (0-1 float)
        resp = self.q.scroll(self.collection, must=[], limit=limit, with_payload=True)
        points = resp.get("result", {}).get("points", [])
        to_delete = [
            p["id"]
            for p in points
            if p.get("payload", {}).get("metadata", {}).get("importance", 1.0)
            < importance_threshold
        ]
        if not to_delete:
            return 0
        # Qdrant batch delete
        body = {"points": to_delete}
        url = self.q._url(f"/collections/{self.collection}/points/delete")
        resp = self.q.session.post(url, json=body, timeout=10)
        resp.raise_for_status()
        self.logger.info(
            "Pruned low-importance items",
            extra={"extra": {"collection": self.collection, "count": len(to_delete)}},
        )
        return len(to_delete)

    def write_decision(
        self, thread_id: str, text: str, metadata: Optional[dict] = None
    ) -> str:
        """Write a decision event to memory (per-turn hook)."""
        return self.write_event(
            scope="decision", thread_id=thread_id, text=text, metadata=metadata
        )

    def write_snippet(
        self, thread_id: str, text: str, metadata: Optional[dict] = None
    ) -> str:
        """Write a code snippet event to memory (per-turn hook)."""
        return self.write_event(
            scope="snippet", thread_id=thread_id, text=text, metadata=metadata
        )

    def write_artifact(
        self, thread_id: str, text: str, metadata: Optional[dict] = None
    ) -> str:
        """Write an artifact event to memory (per-turn hook)."""
        return self.write_event(
            scope="artifact", thread_id=thread_id, text=text, metadata=metadata
        )

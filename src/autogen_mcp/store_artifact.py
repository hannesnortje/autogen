import os
import time
import uuid
from typing import Dict, Any, Optional
from autogen_mcp.memory import MemoryService
from autogen_mcp.observability import get_logger


def store_artifact(
    scope: str,
    thread_id: str,
    text: str,
    metadata: Optional[Dict[str, Any]] = None,
    logger=None,
    correlation_id=None,
) -> str:
    if logger:
        logger.info(
            "Storing artifact",
            extra={
                "extra": {
                    "scope": scope,
                    "thread_id": thread_id,
                    "metadata": metadata,
                }
            },
        )
    mem = MemoryService()
    mem.ensure_collection()
    pid = mem.write_event(scope, thread_id, text, metadata)
    if logger:
        logger.info(
            "Artifact stored in memory",
            extra={"extra": {"pid": pid}},
        )
    return pid


if __name__ == "__main__":
    # Example usage: store a PR artifact
    pr_url = os.environ.get("PR_URL", "https://github.com/example/repo/pull/1")
    sha = os.environ.get("COMMIT_SHA", str(uuid.uuid4()))
    correlation_id = str(uuid.uuid4())
    logger = get_logger("autogen.store_artifact", correlation_id=correlation_id)
    store_artifact(
        scope="pr_artifact",
        thread_id="main",
        text=f"PR: {pr_url}",
        metadata={"sha": sha, "ts": time.time()},
        logger=logger,
        correlation_id=correlation_id,
    )
    print("Artifact stored in Qdrant memory.")

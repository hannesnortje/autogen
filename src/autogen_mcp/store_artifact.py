import os
import time
import uuid
from typing import Dict, Any, Optional
from autogen_mcp.memory import MemoryService


def store_artifact(
    scope: str,
    thread_id: str,
    text: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    mem = MemoryService()
    mem.ensure_collection()
    return mem.write_event(scope, thread_id, text, metadata)


if __name__ == "__main__":
    # Example usage: store a PR artifact
    pr_url = os.environ.get("PR_URL", "https://github.com/example/repo/pull/1")
    sha = os.environ.get("COMMIT_SHA", str(uuid.uuid4()))
    store_artifact(
        scope="pr_artifact",
        thread_id="main",
        text=f"PR: {pr_url}",
        metadata={"sha": sha, "ts": time.time()},
    )
    print("Artifact stored in Qdrant memory.")

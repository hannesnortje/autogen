"""
Local memory client for in-process uploads from the PySide6 UI.
Bypasses HTTP endpoints and writes directly to Qdrant via
MultiScopeMemoryService.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
import os
from typing import List, Dict

from autogen_mcp.multi_memory import MultiScopeMemoryService
from autogen_mcp.memory_collections import CollectionManager, MemoryScope


def _chunk_markdown_content(content: str, filename: str) -> List[Dict]:
    """Chunk markdown content similarly to the server-side implementation.

    Strategy:
    - Split by H2/H3-style headings
    - If a section is large, further chunk by paragraphs around ~1000 chars
    """
    import re

    # Split into sections by headings
    sections = re.split(r"(?m)^(##+\s+.*)$", content)

    # Recombine title with section content
    combined_sections: List[str] = []
    i = 0
    while i < len(sections):
        if sections[i].startswith("#"):
            title = sections[i].strip()
            body = sections[i + 1] if i + 1 < len(sections) else ""
            combined_sections.append(f"{title}\n{body}")
            i += 2
        else:
            if sections[i].strip():
                combined_sections.append(sections[i])
            i += 1

    chunks: List[Dict] = []
    for idx, section in enumerate(combined_sections):
        lines = section.splitlines()
        title = lines[0] if lines else "Untitled"

        if len(section) > 2000:
            # Further split large sections into ~1000-char chunks
            # on paragraph boundaries
            paragraphs = section.split("\n\n")
            current_chunk = ""
            chunk_index = 0

            for para in paragraphs:
                if len(current_chunk) + len(para) + 2 > 1000:
                    if current_chunk:
                        chunks.append(
                            {
                                "content": current_chunk.strip(),
                                "metadata": {
                                    "filename": filename,
                                    "section_title": title,
                                    "chunk_index": chunk_index,
                                    "total_sections": len(combined_sections),
                                    "type": "markdown_chunk",
                                    "upload_date": datetime.now(
                                        timezone.utc
                                    ).isoformat(),
                                },
                            }
                        )
                        chunk_index += 1
                        current_chunk = para + "\n\n"
                    else:
                        # Paragraph itself too large; hard split
                        chunks.append(
                            {
                                "content": para[:1000],
                                "metadata": {
                                    "filename": filename,
                                    "section_title": title,
                                    "chunk_index": chunk_index,
                                    "total_sections": len(combined_sections),
                                    "type": "markdown_chunk",
                                    "upload_date": datetime.now(
                                        timezone.utc
                                    ).isoformat(),
                                },
                            }
                        )
                        chunk_index += 1
                        current_chunk = para[1000:] + "\n\n"
                else:
                    current_chunk += para + "\n\n"

            if current_chunk:
                chunks.append(
                    {
                        "content": current_chunk.strip(),
                        "metadata": {
                            "filename": filename,
                            "section_title": title,
                            "chunk_index": chunk_index,
                            "total_sections": len(combined_sections),
                            "type": "markdown_chunk",
                            "upload_date": datetime.now(timezone.utc).isoformat(),
                        },
                    }
                )
        else:
            chunks.append(
                {
                    "content": section.strip(),
                    "metadata": {
                        "filename": filename,
                        "section_title": title,
                        "chunk_index": idx,
                        "total_sections": len(combined_sections),
                        "type": "markdown_chunk",
                        "upload_date": datetime.now(timezone.utc).isoformat(),
                    },
                }
            )

    return chunks


class LocalMemoryClient:
    """Singleton-ish local client for memory operations."""

    _instance: LocalMemoryClient | None = None

    def __init__(self) -> None:
        self._collection_manager = CollectionManager()
        self._memory_service = MultiScopeMemoryService(self._collection_manager)
        # Ensure collections are initialized similar to the server,
        # but respect seeding gate via AUTOGEN_SEED_GLOBAL
        try:
            seed_flag = os.getenv("AUTOGEN_SEED_GLOBAL", "false").lower() in (
                "1",
                "true",
                "yes",
            )
            if seed_flag:
                self._memory_service.initialize()
            else:
                # Try to initialize collections, don't fail if unavailable
                try:
                    self._collection_manager.initialize_all_collections()
                    # Mark initialized so writes/search are allowed
                    self._memory_service._initialized = True  # noqa: SLF001
                except Exception:
                    # If Qdrant unavailable, allow service to work degraded
                    # in degraded mode
                    self._memory_service._initialized = True  # noqa: SLF001
        except Exception:
            # Proceed; some operations may still work
            self._memory_service._initialized = True  # noqa: SLF001

    @classmethod
    def instance(cls) -> LocalMemoryClient:
        if cls._instance is None:
            cls._instance = LocalMemoryClient()
        return cls._instance

    def upload_markdown(self, file_path: str, project: str, scope: str) -> Dict:
        """Upload a markdown file directly to memory (no HTTP)."""
        # Read content
        with open(file_path, "r", encoding="utf-8") as f:
            content_str = f.read()

        filename = file_path.split("/")[-1]
        chunks = _chunk_markdown_content(content_str, filename)

        # Map scope
        scope_mapping = {
            "global": MemoryScope.GLOBAL,
            "project": MemoryScope.PROJECT,
            "agent": MemoryScope.AGENT,
            "thread": MemoryScope.THREAD,
            "objectives": MemoryScope.OBJECTIVES,
            "artifacts": MemoryScope.ARTIFACTS,
        }
        memory_scope = scope_mapping.get(scope.lower(), MemoryScope.PROJECT)

        # Set project context
        self._memory_service.set_project(project)

        processed = 0
        thread_id = f"upload_{project}_{uuid.uuid4().hex[:8]}"

        for chunk in chunks:
            try:
                if memory_scope == MemoryScope.GLOBAL:
                    self._memory_service.write_global(
                        thread_id=thread_id,
                        text=chunk["content"],
                        metadata=chunk["metadata"],
                    )
                elif memory_scope == MemoryScope.PROJECT:
                    self._memory_service.write_project(
                        thread_id=thread_id,
                        text=chunk["content"],
                        metadata=chunk["metadata"],
                    )
                elif memory_scope == MemoryScope.ARTIFACTS:
                    self._memory_service.write_artifacts(
                        thread_id=thread_id,
                        text=chunk["content"],
                        metadata=chunk["metadata"],
                    )
                else:
                    self._memory_service.write_project(
                        thread_id=thread_id,
                        text=chunk["content"],
                        metadata=chunk["metadata"],
                    )
                processed += 1
            except Exception:
                # Fail fast on first chunk error to surface problems clearly
                if processed == 0:
                    raise
                # Otherwise continue to next chunk
                continue

        return {
            "status": "ok",
            "filename": filename,
            "chunks_processed": processed,
            "total_size": len(content_str.encode("utf-8")),
            "message": f"Processed {processed} chunks locally",
        }

    # --- Local helpers to mirror server capabilities ---

    def search(
        self,
        query: str,
        scope: str,
        limit: int = 10,
        project: str | None = None,
    ) -> list[dict]:
        """Search locally using MultiScopeMemoryService."""
        # Ensure project context for project-scope searches
        if scope and scope.lower() == "project":
            if not project:
                # Derive default project from workspace path, like server
                workspace_path = os.getenv("MCP_WORKSPACE", os.getcwd())
                project = os.path.basename(workspace_path)
            self._memory_service.set_project(project)
        elif project:
            self._memory_service.set_project(project)
        return self._memory_service.search(
            query=query,
            scope=scope,
            limit=limit,
        )

    def list_collections(self) -> list[dict]:
        """List collections with basic info locally."""
        client = self._collection_manager.client
        names = client.list_collections() or []
        result: list[dict] = []
        for name in names:
            try:
                info = client.get_collection_info(name)
                points = 0
                if hasattr(info, "points_count"):
                    points = info.points_count
                elif isinstance(info, dict) and "points_count" in info:
                    points = info["points_count"]
                status = "Active"
                result.append(
                    {
                        "name": name,
                        "documents": points,
                        "vectors": points,
                        "status": status,
                    }
                )
            except Exception:
                result.append(
                    {
                        "name": name,
                        "documents": 0,
                        "vectors": 0,
                        "status": "Unknown",
                    }
                )
        return result

    def get_stats(self) -> dict:
        """Return summary stats locally in the same shape as server."""
        collections = self.list_collections()
        total_documents = sum(c.get("documents", 0) for c in collections)
        total_collections = len(collections)
        collections_ready = sum(1 for c in collections if c.get("documents", 0) > 0)
        return {
            "status": "ready" if total_documents > 0 else "empty",
            "total_collections": total_collections,
            "total_documents": total_documents,
            "collections_ready": collections_ready,
            "message": (
                f"Found {total_documents} documents in "
                f"{collections_ready} active collections"
            ),
        }

    # --- Delete operations (local) ---

    def delete_point(self, collection: str, point_id: str) -> dict:
        """Delete a single point from a collection locally."""
        result = self._collection_manager.qdrant.delete_point(collection, point_id)
        return {
            "success": True,
            "deleted_count": 1,
            "message": f"Deleted point {point_id} from {collection}",
            "result": result,
        }

    def delete_collection(self, collection: str) -> dict:
        """Delete an entire collection locally."""
        # Try to get points count for a nicer message
        try:
            info = self._collection_manager.qdrant.get_collection_info(collection)
            points = 0
            if hasattr(info, "points_count"):
                points = info.points_count
            elif isinstance(info, dict) and "points_count" in info:
                points = info["points_count"]
        except Exception:
            points = 0

        result = self._collection_manager.qdrant.delete_collection(collection)
        return {
            "success": True,
            "deleted_count": points,
            "message": (
                f"Collection {collection} deleted with {points} points removed"
            ),
            "result": result,
        }

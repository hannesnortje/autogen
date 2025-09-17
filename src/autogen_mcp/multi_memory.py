"""
Multi-scope memory service integrating with the new collection architecture.

This replaces the single-collection memory approach with proper multi-scope
collections for global, project, agent, thread, objectives, and artifacts.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from autogen_mcp.memory_collections import (
    CollectionManager,
    MemoryEvent,
    MemoryScope,
)
from autogen_mcp.embeddings import EmbeddingService
from autogen_mcp.hybrid_search_service import HybridSearchService
from autogen_mcp.knowledge_seeder import KnowledgeSeeder
from autogen_mcp.observability import get_logger


@dataclass
class MemoryWriteOptions:
    """Options for memory write operations."""

    scope: MemoryScope
    project_id: Optional[str] = None
    agent_type: Optional[str] = None
    session_id: Optional[str] = None
    thread_id: Optional[str] = None
    importance: float = 0.5
    auto_embed: bool = True


class MultiScopeMemoryService:
    """Memory service with proper multi-scope collection support."""

    def __init__(
        self,
        collection_manager: Optional[CollectionManager] = None,
        correlation_id: Optional[str] = None,
    ):
        self.collection_manager = collection_manager or CollectionManager()
        self.embedding_service = EmbeddingService()
        self.hybrid_search = HybridSearchService()
        self.knowledge_seeder = KnowledgeSeeder(self.collection_manager)
        self.logger = get_logger("autogen.multi_memory", correlation_id=correlation_id)
        self._initialized = False
        self._current_project = None

    def set_project(self, project_slug: str):
        """Set the current project context."""
        self._current_project = project_slug
        self.logger.debug(f"Set project context: {project_slug}")

    def initialize(self, project_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Initialize all collections and seed global knowledge."""
        if self._initialized:
            return {"status": "already_initialized"}

        self.logger.info("Initializing multi-scope memory service")

        try:
            # Initialize all collections
            collections = self.collection_manager.initialize_all_collections(
                project_ids
            )

            # Seed global knowledge
            seeding_result = self.knowledge_seeder.seed_global_knowledge()

            # Verify seeded knowledge
            verification = self.knowledge_seeder.verify_seeded_knowledge()

            self._initialized = True

            result = {
                "status": "initialized",
                "collections": collections,
                "seeding": seeding_result,
                "verification": verification,
                "success": seeding_result["success"]
                and verification.get("pdca_found", False),
            }

            self.logger.info(
                "Multi-scope memory service initialized", extra={"extra": result}
            )

            return result

        except Exception as e:
            error_msg = f"Failed to initialize memory service: {str(e)}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def write_event(
        self,
        content: str,
        options: MemoryWriteOptions,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Write an event to the appropriate collection based on scope."""
        if not self._initialized:
            raise RuntimeError(
                "Memory service not initialized. Call initialize() first."
            )

        # Ensure collection exists
        collection_name = self.collection_manager.ensure_collection(
            options.scope, options.project_id
        )

        # Prepare metadata based on scope
        event_metadata = metadata or {}
        event_metadata.update(
            {
                "importance": options.importance,
                "timestamp": time.time(),
            }
        )

        # Add scope-specific required fields
        if options.scope == MemoryScope.GLOBAL:
            event_metadata.setdefault("category", "general")

        elif options.scope == MemoryScope.PROJECT:
            if not options.project_id:
                raise ValueError("project_id required for PROJECT scope")
            event_metadata["project_id"] = options.project_id
            event_metadata.setdefault("type", "note")

        elif options.scope == MemoryScope.AGENT:
            if not options.agent_type:
                raise ValueError("agent_type required for AGENT scope")
            event_metadata["agent_type"] = options.agent_type
            event_metadata.setdefault("capability", "general")

        elif options.scope == MemoryScope.THREAD:
            if not options.thread_id:
                raise ValueError("thread_id required for THREAD scope")
            event_metadata["thread_id"] = options.thread_id
            event_metadata.setdefault("message_type", "note")
            if options.session_id:
                event_metadata["session_id"] = options.session_id

        elif options.scope == MemoryScope.OBJECTIVES:
            event_metadata.setdefault("objective_type", "general")
            event_metadata.setdefault("status", "active")
            if options.project_id:
                event_metadata["project_id"] = options.project_id

        elif options.scope == MemoryScope.ARTIFACTS:
            event_metadata.setdefault("artifact_type", "general")
            event_metadata.setdefault("reference", "none")
            if options.project_id:
                event_metadata["project_id"] = options.project_id

        # Create memory event
        event = MemoryEvent(
            content=content, scope=options.scope, metadata=event_metadata
        )

        # Generate embedding if requested
        if options.auto_embed:
            event.vector = self.embedding_service.encode_one(content)

        # Validate event
        if not self.collection_manager.validate_event(event):
            raise ValueError(f"Event validation failed for scope {options.scope}")

        # Store in Qdrant
        self.collection_manager.qdrant.upsert_point(
            collection=collection_name,
            point_id=event.event_id,
            vector=event.vector,
            payload={
                "content": event.content,
                "scope": event.scope.value,
                "timestamp": event.timestamp,
                **event.metadata,
            },
        )

        self.logger.info(
            f"Memory event written to {options.scope.value}",
            extra={
                "extra": {
                    "event_id": event.event_id,
                    "collection": collection_name,
                    "content_length": len(content),
                }
            },
        )

        return event.event_id

    # Convenience methods for specific scopes
    def write_global_knowledge(
        self, content: str, category: str, tags: List[str], importance: float = 0.8
    ) -> str:
        """Write knowledge to global collection."""
        options = MemoryWriteOptions(scope=MemoryScope.GLOBAL, importance=importance)
        metadata = {
            "category": category,
            "tags": tags,
            "domain": "general",
            "language": "general",
        }
        return self.write_event(content, options, metadata)

    def write_project_decision(
        self,
        content: str,
        project_id: str,
        decision_type: str = "architectural",
        importance: float = 0.9,
    ) -> str:
        """Write project decision or ADR."""
        options = MemoryWriteOptions(
            scope=MemoryScope.PROJECT, project_id=project_id, importance=importance
        )
        metadata = {"type": decision_type, "component": "general", "status": "active"}
        return self.write_event(content, options, metadata)

    def write_agent_preference(
        self,
        content: str,
        agent_type: str,
        capability: str,
        skill_level: str = "intermediate",
    ) -> str:
        """Write agent-specific preference or capability."""
        options = MemoryWriteOptions(scope=MemoryScope.AGENT, agent_type=agent_type)
        metadata = {
            "capability": capability,
            "skill_level": skill_level,
            "preference_type": "general",
        }
        return self.write_event(content, options, metadata)

    def write_thread_message(
        self,
        content: str,
        thread_id: str,
        session_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        message_type: str = "message",
    ) -> str:
        """Write thread conversation message."""
        options = MemoryWriteOptions(
            scope=MemoryScope.THREAD, thread_id=thread_id, session_id=session_id
        )
        metadata = {"message_type": message_type}
        if agent_id:
            metadata["agent_id"] = agent_id
        return self.write_event(content, options, metadata)

    def write_objective(
        self,
        content: str,
        objective_type: str = "sprint",
        status: str = "active",
        priority: str = "medium",
        project_id: Optional[str] = None,
    ) -> str:
        """Write objective or milestone."""
        options = MemoryWriteOptions(
            scope=MemoryScope.OBJECTIVES, project_id=project_id
        )
        metadata = {
            "objective_type": objective_type,
            "status": status,
            "priority": priority,
        }
        return self.write_event(content, options, metadata)

    def write_artifact(
        self,
        content: str,
        artifact_type: str,
        reference: str,
        project_id: Optional[str] = None,
        commit_hash: Optional[str] = None,
    ) -> str:
        """Write artifact reference (commit, PR, build, etc.)."""
        options = MemoryWriteOptions(scope=MemoryScope.ARTIFACTS, project_id=project_id)
        metadata = {
            "artifact_type": artifact_type,
            "reference": reference,
            "status": "active",
            "created_date": time.strftime("%Y-%m-%d"),
        }
        if commit_hash:
            metadata["commit_hash"] = commit_hash
        return self.write_event(content, options, metadata)

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of memory system."""
        return {
            "initialized": self._initialized,
            "collections": self.collection_manager.health_check(),
            "embedding_service": {
                "available": True,
                "model": self.embedding_service.config.model,
                "dimension": self.embedding_service.dim(),
            },
        }

    def search(
        self, query: str, scope: str = "global", limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search memory across scopes using hybrid search."""
        if not self._initialized:
            raise RuntimeError(
                "Memory service not initialized. Call initialize() first."
            )

        # Map scope string to MemoryScope enum
        scope_mapping = {
            "global": MemoryScope.GLOBAL,
            "project": MemoryScope.PROJECT,
            "agent": MemoryScope.AGENT,
            "thread": MemoryScope.THREAD,
            "objectives": MemoryScope.OBJECTIVES,
            "artifacts": MemoryScope.ARTIFACTS,
        }

        memory_scope = scope_mapping.get(scope.lower(), MemoryScope.GLOBAL)

        # Get collection name
        project_id = (
            self._current_project if memory_scope == MemoryScope.PROJECT else None
        )
        collection_name = self.collection_manager.get_collection_name(
            memory_scope, project_id
        )

        # Perform hybrid search
        results = self.hybrid_search.search(
            collection=collection_name, query=query, k=limit, scopes=[scope.lower()]
        )

        # Transform results to expected format
        formatted_results = []
        for result in results:
            formatted_results.append(
                {
                    "id": result.get("id"),
                    "content": result.get("metadata", {}).get("content", ""),
                    "score": result.get("score", 0.0),
                    "scope": result.get("scope", scope),
                    "metadata": result.get("metadata", {}),
                }
            )

        return formatted_results

    # Convenience methods for easy access
    def write_global(
        self,
        thread_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Write to global scope."""
        options = MemoryWriteOptions(scope=MemoryScope.GLOBAL, thread_id=thread_id)
        return self.write_event(text, options, metadata or {})

    def write_project(
        self,
        thread_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Write to project scope."""
        options = MemoryWriteOptions(
            scope=MemoryScope.PROJECT,
            project_id=self._current_project,
            thread_id=thread_id,
        )
        return self.write_event(text, options, metadata or {})

    def write_objectives(
        self,
        thread_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Write to objectives scope."""
        options = MemoryWriteOptions(
            scope=MemoryScope.OBJECTIVES,
            project_id=self._current_project,
            thread_id=thread_id,
        )
        return self.write_event(text, options, metadata or {})

    def write_artifacts(
        self,
        thread_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Write to artifacts scope."""
        options = MemoryWriteOptions(
            scope=MemoryScope.ARTIFACTS,
            project_id=self._current_project,
            thread_id=thread_id,
        )
        return self.write_event(text, options, metadata or {})


# Backward compatibility wrapper
class MemoryService(MultiScopeMemoryService):
    """Backward compatibility wrapper for existing code."""

    def __init__(self, collection: str = "memory_default", summary_threshold: int = 20):
        super().__init__()
        self.collection = collection  # For compatibility
        self.summary_threshold = summary_threshold
        self._current_project_id = None

    def set_project(self, project_slug: str):
        """Set current project for backward compatibility."""
        self._current_project_id = project_slug
        if not self._initialized:
            self.initialize([project_slug])

    def write_event(
        self,
        scope: str,
        thread_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Backward compatibility for old write_event interface."""
        # Map old scope strings to new MemoryScope enum
        scope_mapping = {
            "decision": MemoryScope.THREAD,
            "snippet": MemoryScope.THREAD,
            "artifact": MemoryScope.ARTIFACTS,
            "thread": MemoryScope.THREAD,
            "global": MemoryScope.GLOBAL,
            "project": MemoryScope.PROJECT,
        }

        memory_scope = scope_mapping.get(scope, MemoryScope.THREAD)

        # Create options based on scope
        if memory_scope == MemoryScope.PROJECT and self._current_project_id:
            options = MemoryWriteOptions(
                scope=memory_scope,
                project_id=self._current_project_id,
                thread_id=thread_id,
            )
        else:
            options = MemoryWriteOptions(scope=memory_scope, thread_id=thread_id)

        return super().write_event(text, options, metadata)

    def write_decision(
        self, thread_id: str, text: str, metadata: Optional[dict] = None
    ) -> str:
        """Write decision event (backward compatibility)."""
        return self.write_event("decision", thread_id, text, metadata)

    def write_snippet(
        self, thread_id: str, text: str, metadata: Optional[dict] = None
    ) -> str:
        """Write snippet event (backward compatibility)."""
        return self.write_event("snippet", thread_id, text, metadata)

    def write_artifact(
        self, thread_id: str, text: str, metadata: Optional[dict] = None
    ) -> str:
        """Write artifact event (backward compatibility)."""
        return self.write_event("artifact", thread_id, text, metadata)

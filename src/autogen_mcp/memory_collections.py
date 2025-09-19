"""
Multi-scope collection schemas and management for Qdrant-based memory system.

This module defines the structured memory architecture with dedicated collections
for different knowledge scopes as specified in AutogenSpecs_Expanded.md.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from autogen_mcp.qdrant_client import QdrantWrapper
from autogen_mcp.observability import get_logger


class MemoryScope(str, Enum):
    """Memory scope types for structured knowledge organization."""

    GLOBAL = "global"  # coding standards, security rules, reusable solutions
    PROJECT = "project"  # ADRs, APIs, dataset notes, known issues
    AGENT = "agent"  # preferences, style, skills, capabilities
    THREAD = "thread"  # conversations, micro-decisions, TODOs
    OBJECTIVES = "objectives"  # sprint goals, OKRs, milestones, status updates
    ARTIFACTS = "artifacts"  # commits, PRs, build tags, test reports


@dataclass
class CollectionSchema:
    """Schema definition for a memory collection."""

    name: str
    scope: MemoryScope
    vector_size: int = 384  # FastEmbed sentence-transformers/all-MiniLM-L6-v2 dimension
    distance: str = "Cosine"
    description: str = ""
    required_fields: List[str] = None
    indexed_fields: List[str] = None

    def __post_init__(self):
        self.required_fields = self.required_fields or []
        self.indexed_fields = self.indexed_fields or []


# Collection schema definitions based on AutogenSpecs_Expanded.md requirements
COLLECTION_SCHEMAS = {
    MemoryScope.GLOBAL: CollectionSchema(
        name="autogen_global",
        scope=MemoryScope.GLOBAL,
        description="Global knowledge: coding standards, security rules, reusable solutions",
        required_fields=["content", "category", "importance"],
        indexed_fields=["category", "tags", "language", "domain"],
    ),
    MemoryScope.PROJECT: CollectionSchema(
        name="autogen_project_{project_id}",  # Template - will be formatted
        scope=MemoryScope.PROJECT,
        description="Project-specific knowledge: ADRs, APIs, known issues, decisions",
        required_fields=["content", "project_id", "type"],
        indexed_fields=["project_id", "type", "component", "status"],
    ),
    MemoryScope.AGENT: CollectionSchema(
        name="autogen_agent",
        scope=MemoryScope.AGENT,
        description="Agent preferences, style, skills, and capabilities",
        required_fields=["content", "agent_type", "capability"],
        indexed_fields=["agent_type", "capability", "skill_level", "preference_type"],
    ),
    MemoryScope.THREAD: CollectionSchema(
        name="autogen_thread",
        scope=MemoryScope.THREAD,
        description="Conversation threads, micro-decisions, and TODOs",
        required_fields=["content", "thread_id", "message_type"],
        indexed_fields=["thread_id", "session_id", "agent_id", "message_type"],
    ),
    MemoryScope.OBJECTIVES: CollectionSchema(
        name="autogen_objectives",
        scope=MemoryScope.OBJECTIVES,
        description="Sprint goals, OKRs, milestones, and progress tracking",
        required_fields=["content", "objective_type", "status"],
        indexed_fields=[
            "project_id",
            "objective_type",
            "status",
            "priority",
            "due_date",
        ],
    ),
    MemoryScope.ARTIFACTS: CollectionSchema(
        name="autogen_artifacts",
        scope=MemoryScope.ARTIFACTS,
        description="Commits, PRs, build tags, test reports, and deployment artifacts",
        required_fields=["content", "artifact_type", "reference"],
        indexed_fields=[
            "artifact_type",
            "project_id",
            "commit_hash",
            "status",
            "created_date",
        ],
    ),
}


@dataclass
class MemoryEvent:
    """Structured memory event with proper typing and validation."""

    content: str
    scope: MemoryScope
    metadata: Dict[str, Any]
    event_id: str = None
    timestamp: float = None
    vector: List[float] = None

    def __post_init__(self):
        if self.event_id is None:
            self.event_id = str(uuid.uuid4())
        if self.timestamp is None:
            self.timestamp = time.time()

        # Validate required fields based on scope
        schema = COLLECTION_SCHEMAS[self.scope]
        for field in schema.required_fields:
            if field == "content":
                continue  # Already validated as parameter
            if field not in self.metadata:
                raise ValueError(
                    f"Missing required field '{field}' for scope {self.scope}"
                )


class CollectionManager:
    """Manages multi-scope collections with proper schema validation."""

    def __init__(self, qdrant_client: Optional[QdrantWrapper] = None):
        self.qdrant = qdrant_client or QdrantWrapper()
        self.logger = get_logger("autogen.collections")
        self._initialized_collections = set()

    @property
    def client(self) -> QdrantWrapper:
        """Provide access to the Qdrant client for compatibility."""
        return self.qdrant

    # Backward-compat alias: some code references collection_manager.q
    @property
    def q(self) -> QdrantWrapper:
        return self.qdrant

    def get_collection_name(
        self, scope: MemoryScope, project_id: Optional[str] = None
    ) -> str:
        """Get actual collection name for a scope.

        Handles project-specific naming.
        """
        schema = COLLECTION_SCHEMAS[scope]

        if scope == MemoryScope.PROJECT and project_id:
            return schema.name.format(project_id=project_id)
        elif scope == MemoryScope.PROJECT and not project_id:
            raise ValueError("Project ID required for project-scope collection")

        return schema.name

    def ensure_collection(
        self, scope: MemoryScope, project_id: Optional[str] = None
    ) -> str:
        """Ensure a collection exists for the given scope."""
        collection_name = self.get_collection_name(scope, project_id)

        self.logger.info(
            f"Ensuring collection exists: {collection_name}",
            extra={
                "extra": {
                    "scope": scope.value,
                    "project_id": project_id,
                    "collection_name": collection_name,
                }
            },
        )

        if collection_name in self._initialized_collections:
            self.logger.debug(f"Collection {collection_name} already initialized")
            return collection_name

        schema = COLLECTION_SCHEMAS[scope]

        try:
            # Check if collection already exists
            existing = self.qdrant.list_collections()
            self.logger.info(f"Existing collections: {existing}")

            if collection_name not in existing:
                self.logger.info(f"Creating new collection: {collection_name}")
                self.qdrant.create_collection(
                    name=collection_name,
                    vector_size=schema.vector_size,
                    distance=schema.distance,
                )
                self.logger.info(
                    f"Created collection: {collection_name}",
                    extra={
                        "extra": {
                            "collection": collection_name,
                            "scope": scope.value,
                            "schema": schema.description,
                        }
                    },
                )
            else:
                self.logger.info(f"Collection {collection_name} already exists")

            self._initialized_collections.add(collection_name)
            return collection_name

        except Exception as e:
            self.logger.error(
                f"Failed to ensure collection: {collection_name}",
                extra={"extra": {"error": str(e), "scope": scope.value}},
            )
            raise

    def initialize_all_collections(
        self, project_ids: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """Initialize all required collections."""
        initialized = {}

        # Initialize non-project collections
        for scope in [
            MemoryScope.GLOBAL,
            MemoryScope.AGENT,
            MemoryScope.THREAD,
            MemoryScope.OBJECTIVES,
            MemoryScope.ARTIFACTS,
        ]:
            try:
                collection_name = self.ensure_collection(scope)
                initialized[scope.value] = collection_name
            except Exception as e:
                self.logger.error(f"Failed to initialize {scope.value} collection: {e}")

        # Initialize project-specific collections
        if project_ids:
            for project_id in project_ids:
                try:
                    collection_name = self.ensure_collection(
                        MemoryScope.PROJECT, project_id
                    )
                    initialized[f"project_{project_id}"] = collection_name
                except Exception as e:
                    self.logger.error(
                        (
                            "Failed to initialize project collection for "
                            f"{project_id}: {e}"
                        )
                    )

        self.logger.info(
            f"Initialized {len(initialized)} collections",
            extra={"extra": {"collections": list(initialized.keys())}},
        )

        return initialized

    def validate_event(self, event: MemoryEvent) -> bool:
        """Validate a memory event against its scope schema."""
        try:
            schema = COLLECTION_SCHEMAS[event.scope]

            # Check required fields
            for field in schema.required_fields:
                if field == "content":
                    if not event.content or not event.content.strip():
                        return False
                elif field not in event.metadata:
                    return False

            return True

        except Exception as e:
            self.logger.warning(f"Event validation failed: {e}")
            return False

    def get_schema_info(self, scope: MemoryScope) -> Dict[str, Any]:
        """Get schema information for a scope."""
        schema = COLLECTION_SCHEMAS[scope]
        return {
            "scope": scope.value,
            "collection_template": schema.name,
            "description": schema.description,
            "required_fields": schema.required_fields,
            "indexed_fields": schema.indexed_fields,
            "vector_size": schema.vector_size,
        }

    def health_check(self) -> Dict[str, Any]:
        """Check health of all initialized collections."""
        health = {
            "qdrant_available": False,
            "collections_initialized": len(self._initialized_collections),
            "collections": {},
            "errors": [],
        }

        try:
            health["qdrant_available"] = self.qdrant.health()

            if health["qdrant_available"]:
                existing = self.qdrant.list_collections()
                for collection in self._initialized_collections:
                    health["collections"][collection] = collection in existing

        except Exception as e:
            health["errors"].append(str(e))

        return health

    def collection_exists(self, collection_name: str) -> bool:
        """Return True if the given collection exists in Qdrant."""
        try:
            existing = self.qdrant.list_collections() or []
            return collection_name in existing
        except Exception as e:
            self.logger.warning(
                "Failed to check existence for collection %s: %s",
                collection_name,
                e,
            )
            return False

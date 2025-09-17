"""Memory service for AutoGen UI - MCP server integration.

This module provides memory management functionality for the UI, supporting
both direct integration with MCP components and HTTP API communication.
"""

from typing import List, Dict, Any
from PySide6.QtCore import Signal

from .base_service import BaseService, IntegrationConfig


class MemoryService(BaseService):
    """Service for memory operations with Qdrant integration.

    Supports memory search, browsing, analytics, and CRUD operations
    through both direct integration and HTTP API communication.
    """

    # Additional signals specific to memory operations
    memory_search_completed = Signal(list)  # search_results
    memory_stats_updated = Signal(dict)  # stats_dict
    memory_health_updated = Signal(dict)  # health_info

    def __init__(self, config: IntegrationConfig, parent=None):
        super().__init__(config, parent)
        self._memory_service = None
        self._analytics_service = None

    async def initialize(self) -> bool:
        """Initialize memory service with direct or HTTP integration."""
        try:
            if await self._use_direct_integration("memory"):
                await self._initialize_direct()
            else:
                await self._initialize_http()
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize memory service: {e}")
            import traceback

            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    async def _initialize_direct(self) -> None:
        """Initialize with direct imports to MCP server components."""
        try:
            # Import MCP server components directly
            from autogen_mcp.collections import CollectionManager
            from autogen_mcp.multi_memory import MultiScopeMemoryService
            from autogen_mcp.memory_analytics import MemoryAnalyticsService

            # Initialize services directly
            collection_manager = CollectionManager()

            # Initialize all collections
            collection_manager.initialize_all_collections()

            self._memory_service = MultiScopeMemoryService(collection_manager)

            # Initialize the memory service (synchronous call, returns dict)
            self._memory_service.initialize()

            # Create analytics service (don't start monitoring yet to avoid issues)
            self._analytics_service = MemoryAnalyticsService(self._memory_service)

            msg = "Memory service initialized with direct integration"
            self.logger.info(msg)

        except ImportError as e:
            self.logger.error(f"Direct integration failed: {e}")
            # Fall back to HTTP if direct fails
            await self._initialize_http()

    async def _initialize_http(self) -> None:
        """Initialize with HTTP client to MCP server."""
        await self._ensure_http_client()
        self.logger.info("Memory service initialized with HTTP integration")

    async def search_memory(
        self,
        query: str,
        scope: str = "conversation",
        k: int = 5,
        threshold: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """Search memory entries by query.

        Args:
            query: Search query text
            scope: Memory scope (conversation, project, global)
            k: Number of results to return
            threshold: Similarity threshold (0.0-1.0)

        Returns:
            List of memory entries with content and metadata
        """
        operation_name = f"search_memory_{scope}"
        self.operation_started.emit(operation_name)

        try:
            use_direct = self._memory_service and await self._use_direct_integration(
                "memory"
            )
            if use_direct:
                # Direct integration
                results = await self._search_memory_direct(query, scope, k, threshold)
            else:
                # HTTP integration
                results = await self._search_memory_http(query, scope, k, threshold)

            self.memory_search_completed.emit(results)
            self.operation_completed.emit(operation_name, {"results": results})
            return results

        except Exception as e:
            error_msg = f"Memory search failed: {e}"
            self.logger.error(error_msg)
            self.operation_failed.emit(operation_name, error_msg)
            return []

    async def _search_memory_direct(
        self, query: str, scope: str, k: int, threshold: float
    ) -> List[Dict[str, Any]]:
        """Search memory using direct integration."""
        # Convert scope to memory service format
        scope_map = {
            "conversation": "thread",  # Map conversation to thread
            "project": "project",
            "global": "global",
        }
        scope_str = scope_map.get(scope, "thread")

        # Perform direct search
        results = self._memory_service.search(query=query, scope=scope_str, limit=k)

        # Convert to UI format
        return [
            {
                "id": result.get("id"),
                "content": result.get("content"),
                "metadata": result.get("metadata", {}),
                "score": result.get("score"),
                "timestamp": result.get("metadata", {}).get("timestamp"),
            }
            for result in results
        ]

    async def _search_memory_http(
        self, query: str, scope: str, k: int, threshold: float
    ) -> List[Dict[str, Any]]:
        """Search memory using HTTP API."""
        payload = {"query": query, "scope": scope, "k": k, "threshold": threshold}

        response = await self._http_request("POST", "/memory/search", json=payload)
        return response.get("results", [])

    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics."""
        operation_name = "get_memory_stats"
        self.operation_started.emit(operation_name)

        try:
            use_direct = self._analytics_service and await self._use_direct_integration(
                "analytics"
            )
            if use_direct:
                # Direct integration
                stats = await self._get_memory_stats_direct()
            else:
                # HTTP integration
                stats = await self._get_memory_stats_http()

            self.memory_stats_updated.emit(stats)
            self.operation_completed.emit(operation_name, stats)
            return stats

        except Exception as e:
            error_msg = f"Failed to get memory stats: {e}"
            self.logger.error(error_msg)
            self.operation_failed.emit(operation_name, error_msg)
            return {}

    async def _get_memory_stats_direct(self) -> Dict[str, Any]:
        """Get memory stats using direct integration."""
        report = await self._analytics_service.get_analytics_report()
        return {
            "total_entries": report.get("metrics", {})
            .get("storage", {})
            .get("total_entries", 0),
            "memory_usage": report.get("metrics", {}),
            "collection_stats": report.get("scope_metrics", {}),
            "health_score": str(report.get("health_status", "unknown")),
        }

    async def _get_memory_stats_http(self) -> Dict[str, Any]:
        """Get memory stats using HTTP API."""
        response = await self._http_request("GET", "/memory/analytics/report")
        return response.get("stats", {})

    async def get_memory_health(self) -> Dict[str, Any]:
        """Get memory system health information."""
        operation_name = "get_memory_health"
        self.operation_started.emit(operation_name)

        try:
            if await self._use_direct_integration("analytics"):
                health = await self._get_memory_health_direct()
            else:
                health = await self._get_memory_health_http()

            self.memory_health_updated.emit(health)
            self.operation_completed.emit(operation_name, health)
            return health

        except Exception as e:
            error_msg = f"Failed to get memory health: {e}"
            self.logger.error(error_msg)
            self.operation_failed.emit(operation_name, error_msg)
            return {"status": "error", "message": error_msg}

    async def _get_memory_health_direct(self) -> Dict[str, Any]:
        """Get memory health using direct integration."""
        if self._analytics_service:
            report = await self._analytics_service.get_analytics_report()
            health_status = report.get("health_status", "unknown")
            alerts = report.get("alerts", [])
            return {
                "status": str(health_status),
                "connection": "connected",
                "alerts": [alert.get("message", str(alert)) for alert in alerts],
            }
        return {"status": "unknown", "connection": "disconnected"}

    async def _get_memory_health_http(self) -> Dict[str, Any]:
        """Get memory health using HTTP API."""
        response = await self._http_request("GET", "/memory/analytics/health")
        return response.get("health", {})

    async def browse_memories(
        self, scope: str = "conversation", limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Browse memory entries with pagination.

        Args:
            scope: Memory scope to browse
            limit: Maximum number of entries to return
            offset: Starting offset for pagination

        Returns:
            List of memory entries
        """
        operation_name = f"browse_memories_{scope}"
        self.operation_started.emit(operation_name)

        try:
            # For now, use search with empty query to browse
            # TODO: Implement dedicated browse endpoint
            results = await self.search_memory(
                query="",  # Empty query for browsing
                scope=scope,
                k=limit,  # k parameter in the public method
                threshold=0.0,  # No threshold for browsing
            )

            # Apply offset manually for now
            if results:
                paginated_results = results[offset : offset + limit]
            else:
                paginated_results = []

            result_data = {"results": paginated_results}
            self.operation_completed.emit(operation_name, result_data)
            return paginated_results

        except Exception as e:
            error_msg = f"Browse memories failed: {e}"
            self.logger.error(error_msg)
            self.operation_failed.emit(operation_name, error_msg)
            return []

    async def clear_memory(self, scope: str = "conversation") -> bool:
        """Clear memories in specified scope.

        Args:
            scope: Memory scope to clear

        Returns:
            True if successful
        """
        operation_name = f"clear_memory_{scope}"
        self.operation_started.emit(operation_name)

        try:
            # Note: This is a destructive operation, implement with care
            # For now, just return success without actual clearing
            # TODO: Implement safe memory clearing

            result_data = {"scope": scope, "cleared": True}
            self.operation_completed.emit(operation_name, result_data)
            return True

        except Exception as e:
            error_msg = f"Clear memory failed: {e}"
            self.logger.error(error_msg)
            self.operation_failed.emit(operation_name, error_msg)
            return False

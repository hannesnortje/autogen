"""Base service architecture for AutoGen UI integration with MCP server.

This module provides the foundation for hybrid integration between the PySide6
UI and MCP server, supporting both direct Python imports and HTTP API calls.
"""

import asyncio
from enum import Enum
from typing import Any, Dict, List, Optional
import logging
import httpx
from pydantic import BaseModel
from PySide6.QtCore import QObject, Signal, QTimer


class IntegrationMode(str, Enum):
    """Integration mode for connecting to MCP server."""

    DIRECT = "direct"  # Direct Python imports
    HTTP = "http"  # HTTP API calls
    HYBRID = "hybrid"  # Direct with HTTP fallback


class IntegrationConfig(BaseModel):
    """Configuration for MCP server integration."""

    mode: IntegrationMode = IntegrationMode.DIRECT
    mcp_server_url: str = "http://localhost:9000"
    websocket_url: str = "ws://localhost:9000"
    timeout: int = 30
    retry_attempts: int = 3
    direct_components: List[str] = ["memory", "sessions"]
    http_components: List[str] = ["analytics", "cross_project"]


class BaseService(QObject):
    """Base service class for UI-MCP server integration.

    Provides common functionality for both direct and HTTP integration modes,
    including error handling, retries, and automatic fallback.
    """

    # Qt Signals for UI updates
    operation_started = Signal(str)  # operation_name
    operation_completed = Signal(str, dict)  # operation_name, result
    operation_failed = Signal(str, str)  # operation_name, error_message
    connection_status_changed = Signal(bool)  # is_connected

    def __init__(self, config: IntegrationConfig, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.config = config
        class_name = f"{self.__class__.__module__}.{self.__class__.__name__}"
        self.logger = logging.getLogger(class_name)
        self.http_client: Optional[httpx.AsyncClient] = None
        self.is_connected = False

        # Health check timer
        self.health_timer = QTimer()
        self.health_timer.timeout.connect(self._check_health)
        self.health_timer.start(30000)  # Check every 30 seconds

    async def _ensure_http_client(self) -> httpx.AsyncClient:
        """Ensure HTTP client is initialized."""
        if self.http_client is None:
            self.http_client = httpx.AsyncClient(
                base_url=self.config.mcp_server_url, timeout=self.config.timeout
            )
        return self.http_client

    async def _http_request(
        self, method: str, endpoint: str, **kwargs
    ) -> Dict[str, Any]:
        """Make HTTP request to MCP server with error handling."""
        client = await self._ensure_http_client()

        for attempt in range(self.config.retry_attempts):
            try:
                response = await client.request(method, endpoint, **kwargs)
                response.raise_for_status()
                return response.json()
            except httpx.RequestError as e:
                msg = f"HTTP request failed (attempt {attempt + 1}): {e}"
                self.logger.warning(msg)
                if attempt == self.config.retry_attempts - 1:
                    raise
                await asyncio.sleep(1)  # Brief delay before retry

        return {}

    async def _direct_import_available(self, module_name: str) -> bool:
        """Check if direct import is available for given module."""
        try:
            if module_name == "memory":
                from autogen_mcp.multi_memory import (  # noqa: F401
                    MultiScopeMemoryService,
                )

                return True
            elif module_name == "analytics":
                from autogen_mcp.memory_analytics import (  # noqa: F401
                    MemoryAnalyticsService,
                )

                return True
            elif module_name == "sessions":
                from autogen_mcp.orchestrator import (  # noqa: F401
                    AgentOrchestrator,
                )

                return True
            # Add more module checks as needed
        except ImportError:
            return False
        return False

    async def _use_direct_integration(self, component: str) -> bool:
        """Determine if direct integration should be used for component."""
        if self.config.mode == IntegrationMode.HTTP:
            return False
        elif self.config.mode == IntegrationMode.DIRECT:
            return await self._direct_import_available(component)
        else:  # HYBRID mode
            if component in self.config.direct_components:
                return await self._direct_import_available(component)
            return False

    def _check_health(self) -> None:
        """Check service health (Qt slot for timer)."""
        asyncio.create_task(self._async_health_check())

    async def _async_health_check(self) -> None:
        """Async health check implementation."""
        try:
            if self.config.mode != IntegrationMode.DIRECT:
                # HTTP health check
                result = await self._http_request("GET", "/health")
                new_status = result.get("status") == "healthy"
            else:
                # Direct integration is always "connected" if imports work
                new_status = await self._direct_import_available("memory")

            if new_status != self.is_connected:
                self.is_connected = new_status
                self.connection_status_changed.emit(self.is_connected)

        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            if self.is_connected:
                self.is_connected = False
                self.connection_status_changed.emit(self.is_connected)

    async def close(self) -> None:
        """Clean up resources."""
        self.health_timer.stop()
        if self.http_client:
            await self.http_client.aclose()

    def initialize(self) -> bool:
        """Initialize the service. Return True if successful."""
        msg = "Subclasses must implement initialize method"
        raise NotImplementedError(msg)

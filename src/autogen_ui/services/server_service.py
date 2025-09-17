"""Server service for AutoGen UI server management and monitoring.

This module provides server health monitoring, endpoint testing, and connection
management functionality for the MCP server integration.
"""

import asyncio
import logging
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

import httpx
from PySide6.QtCore import QObject, Signal, QTimer

from .base_service import BaseService, IntegrationConfig


class ServerStatus(str, Enum):
    """Server connection status."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    ERROR = "error"


@dataclass
class EndpointInfo:
    """Information about an MCP server endpoint."""

    path: str
    method: str
    description: str
    status: ServerStatus = ServerStatus.DISCONNECTED
    response_time: Optional[float] = None
    last_checked: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class ServerHealth:
    """Server health information."""

    status: ServerStatus
    uptime: Optional[float] = None
    version: Optional[str] = None
    endpoints_healthy: int = 0
    endpoints_total: int = 0
    last_check: Optional[datetime] = None
    error_message: Optional[str] = None


class ServerService(BaseService):
    """Service for MCP server management and monitoring."""

    # Qt Signals
    server_status_changed = Signal(ServerStatus)
    health_updated = Signal(ServerHealth)
    endpoint_tested = Signal(str, EndpointInfo)  # endpoint_path, info

    def __init__(self, config: IntegrationConfig, parent: Optional[QObject] = None):
        super().__init__(config, parent)
        self.logger = logging.getLogger(f"{__name__}.ServerService")

        # Server state
        self._current_status = ServerStatus.DISCONNECTED
        self._server_health: Optional[ServerHealth] = None

        # MCP Server endpoints (from mcp_server.py analysis)
        self._endpoints = self._initialize_endpoints()

        # Health check timer (override parent timer for more frequent checks)
        self.health_timer.stop()  # Stop parent timer
        self.health_timer = QTimer()
        self.health_timer.timeout.connect(self._check_server_health)
        # Check every 10 seconds for server management
        self.health_timer.start(10000)

        # HTTP client for endpoint testing
        self._test_client: Optional[httpx.AsyncClient] = None

    def _initialize_endpoints(self) -> List[EndpointInfo]:
        """Initialize known MCP server endpoints."""
        return [
            # Core System Endpoints
            EndpointInfo("GET", "/health", "Server health monitoring"),
            EndpointInfo("GET", "/workspace", "Workspace information"),
            EndpointInfo("POST", "/workspace/write", "File operations"),
            EndpointInfo("GET", "/workspace/files", "File listing"),
            # Agent Orchestration Endpoints
            EndpointInfo("POST", "/orchestrate/start", "Start sessions"),
            EndpointInfo("POST", "/orchestrate/stop", "Stop sessions"),
            EndpointInfo("GET", "/orchestrate/sessions", "List sessions"),
            # Memory Management Endpoints
            EndpointInfo("POST", "/memory/search", "Memory search"),
            EndpointInfo("POST", "/objective/add", "Add objectives"),
            # Analytics Endpoints
            EndpointInfo("GET", "/memory/analytics/report", "Analytics dashboard"),
            EndpointInfo("GET", "/memory/analytics/health", "Health monitoring"),
            EndpointInfo("POST", "/memory/analytics/optimize", "Memory optimization"),
            EndpointInfo("GET", "/memory/analytics/metrics", "Real-time metrics"),
            # Cross-Project Learning Endpoints
            EndpointInfo("POST", "/cross-project/register", "Cross-project learning"),
            EndpointInfo(
                "POST",
                "/cross-project/recommendations",
                "Smart recommendations",
            ),
            EndpointInfo("GET", "/cross-project/analysis", "Pattern analysis"),
            # WebSocket endpoint (special handling)
            EndpointInfo("WS", "/ws/session/{session_id}", "Real-time updates"),
        ]

    async def _ensure_test_client(self) -> httpx.AsyncClient:
        """Ensure test HTTP client is initialized."""
        if self._test_client is None:
            self._test_client = httpx.AsyncClient(
                base_url=self.config.mcp_server_url,
                timeout=5.0,  # Shorter timeout for testing
            )
        return self._test_client

    def initialize(self) -> bool:
        """Initialize the server service."""
        self.logger.info("Initializing ServerService")

        # Start with initial health check
        self._check_server_health()

        return True

    def _check_server_health(self) -> None:
        """Check server health (Qt slot for timer)."""
        try:
            # Run health check in separate thread
            import threading

            thread = threading.Thread(target=self._sync_health_check)
            thread.daemon = True
            thread.start()
        except Exception as e:
            self.logger.error(f"Health check thread failed: {e}")

    def _sync_health_check(self) -> None:
        """Synchronous health check wrapper."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._async_health_check())
            loop.close()
        except Exception as e:
            self.logger.error(f"Server health check failed: {e}")
            self._update_server_status(ServerStatus.ERROR, str(e))

    async def _async_health_check(self) -> None:
        """Async health check implementation."""
        try:
            client = await self._ensure_test_client()

            response = await client.get("/health")

            if response.status_code == 200:
                health_data = response.json()

                # Create server health object
                health = ServerHealth(
                    status=ServerStatus.CONNECTED,
                    uptime=health_data.get("uptime"),
                    version=health_data.get("version", "unknown"),
                    last_check=datetime.now(),
                    # Exclude WebSocket from total
                    endpoints_total=len(self._endpoints) - 1,
                    endpoints_healthy=0,  # Will be updated by endpoint testing
                )

                self._server_health = health
                self._update_server_status(ServerStatus.CONNECTED)
                self.health_updated.emit(health)

            else:
                self._update_server_status(
                    ServerStatus.ERROR,
                    f"Health check failed: HTTP {response.status_code}",
                )

        except httpx.RequestError as e:
            self.logger.warning(f"Server health check failed: {e}")
            self._update_server_status(ServerStatus.DISCONNECTED, str(e))
        except Exception as e:
            self.logger.error(f"Unexpected health check error: {e}")
            self._update_server_status(ServerStatus.ERROR, str(e))

    def _update_server_status(
        self, status: ServerStatus, error_msg: Optional[str] = None
    ) -> None:
        """Update server status and emit signals."""
        if status != self._current_status:
            self._current_status = status
            self.server_status_changed.emit(status)

            if status == ServerStatus.DISCONNECTED and self._server_health:
                self._server_health.status = status
                self._server_health.error_message = error_msg
                self.health_updated.emit(self._server_health)

    async def test_endpoint(self, endpoint_path: str) -> EndpointInfo:
        """Test a specific endpoint and return results."""
        endpoint = next(
            (ep for ep in self._endpoints if ep.path == endpoint_path), None
        )
        if not endpoint:
            raise ValueError(f"Unknown endpoint: {endpoint_path}")

        self.operation_started.emit(f"test_endpoint_{endpoint_path}")

        try:
            if endpoint.method == "WS":
                # Special handling for WebSocket endpoint
                return await self._test_websocket_endpoint(endpoint)
            else:
                return await self._test_http_endpoint(endpoint)

        except Exception as e:
            self.logger.error(f"Endpoint test failed for {endpoint_path}: {e}")
            endpoint.status = ServerStatus.ERROR
            endpoint.error_message = str(e)
            endpoint.last_checked = datetime.now()

            self.endpoint_tested.emit(endpoint_path, endpoint)
            self.operation_failed.emit(f"test_endpoint_{endpoint_path}", str(e))
            return endpoint

    async def _test_http_endpoint(self, endpoint: EndpointInfo) -> EndpointInfo:
        """Test HTTP endpoint."""
        client = await self._ensure_test_client()

        start_time = asyncio.get_event_loop().time()

        try:
            # Prepare test data based on endpoint
            test_data = self._get_test_data_for_endpoint(endpoint.path)

            if endpoint.method == "GET":
                response = await client.get(endpoint.path)
            elif endpoint.method == "POST":
                response = await client.post(endpoint.path, json=test_data)
            else:
                raise ValueError(f"Unsupported method: {endpoint.method}")

            response_time = asyncio.get_event_loop().time() - start_time

            # Update endpoint info
            endpoint.status = (
                ServerStatus.CONNECTED
                if response.status_code < 400
                else ServerStatus.ERROR
            )
            endpoint.response_time = response_time
            endpoint.last_checked = datetime.now()
            endpoint.error_message = (
                None if response.status_code < 400 else f"HTTP {response.status_code}"
            )

        except httpx.RequestError as e:
            endpoint.status = ServerStatus.DISCONNECTED
            endpoint.error_message = str(e)
            endpoint.last_checked = datetime.now()

        self.endpoint_tested.emit(endpoint.path, endpoint)
        self.operation_completed.emit(
            f"test_endpoint_{endpoint.path}",
            {
                "status": endpoint.status,
                "response_time": endpoint.response_time,
            },
        )

        return endpoint

    async def _test_websocket_endpoint(self, endpoint: EndpointInfo) -> EndpointInfo:
        """Test WebSocket endpoint."""
        try:
            import websockets

            # Test WebSocket connection
            ws_url = self.config.websocket_url + "/ws/session/test"

            start_time = asyncio.get_event_loop().time()
            async with websockets.connect(ws_url, timeout=5):
                response_time = asyncio.get_event_loop().time() - start_time

                endpoint.status = ServerStatus.CONNECTED
                endpoint.response_time = response_time
                endpoint.last_checked = datetime.now()
                endpoint.error_message = None

        except Exception as e:
            endpoint.status = ServerStatus.ERROR
            endpoint.error_message = str(e)
            endpoint.last_checked = datetime.now()

        self.endpoint_tested.emit(endpoint.path, endpoint)
        return endpoint

    def _get_test_data_for_endpoint(self, path: str) -> Dict:
        """Get appropriate test data for endpoint."""
        test_data = {
            "/memory/search": {"query": "test", "scope": "global", "k": 1},
            "/objective/add": {"project": "test", "objective": "test objective"},
            "/orchestrate/start": {
                "project": "test",
                "agents": ["test_agent"],
                "objective": "test session",
            },
            "/workspace/write": {"filename": "test.txt", "content": "test content"},
            "/cross-project/register": {"project": "test", "context": "test context"},
            "/cross-project/recommendations": {
                "project": "test",
                "context": "test query",
            },
            "/memory/analytics/optimize": {"strategy": "cleanup"},
        }
        return test_data.get(path, {})

    async def test_all_endpoints(self) -> Dict[str, EndpointInfo]:
        """Test all endpoints and return results."""
        self.operation_started.emit("test_all_endpoints")

        results = {}
        healthy_count = 0

        # Test HTTP endpoints
        http_endpoints = [ep for ep in self._endpoints if ep.method != "WS"]

        for endpoint in http_endpoints:
            try:
                result = await self.test_endpoint(endpoint.path)
                results[endpoint.path] = result

                if result.status == ServerStatus.CONNECTED:
                    healthy_count += 1

            except Exception as e:
                self.logger.error(f"Failed to test endpoint {endpoint.path}: {e}")

        # Update server health with endpoint results
        if self._server_health:
            self._server_health.endpoints_healthy = healthy_count
            self.health_updated.emit(self._server_health)

        self.operation_completed.emit(
            "test_all_endpoints",
            {
                "tested": len(results),
                "healthy": healthy_count,
                "total": len(http_endpoints),
            },
        )

        return results

    def get_server_health(self) -> Optional[ServerHealth]:
        """Get current server health information."""
        return self._server_health

    def get_endpoints(self) -> List[EndpointInfo]:
        """Get all endpoint information."""
        return self._endpoints.copy()

    def get_server_status(self) -> ServerStatus:
        """Get current server status."""
        return self._current_status

    async def close(self) -> None:
        """Clean up resources."""
        await super().close()
        if self._test_client:
            await self._test_client.aclose()

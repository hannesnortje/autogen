"""
Real-time Service for AutoGen UI

Provides WebSocket connectivity to MCP server for real-time updates,
notifications, and live session monitoring.
"""

import asyncio
import json
import logging
import websockets
from collections import defaultdict
from typing import Dict, Optional, Callable, Any, List
from PySide6.QtCore import QObject, Signal, QThread, QTimer

logger = logging.getLogger(__name__)


class WebSocketWorker(QThread):
    """Worker thread for WebSocket operations"""

    connected = Signal()
    disconnected = Signal()
    message_received = Signal(dict)
    error_occurred = Signal(str)
    connection_failed = Signal(str)

    def __init__(self, server_url: str, session_id: Optional[str] = None):
        super().__init__()
        self.server_url = server_url
        self.session_id = session_id
        self.websocket = None
        self.should_stop = False
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 5
        self._reconnect_delay = 2  # seconds

    def run(self):
        """Main WebSocket connection loop"""
        asyncio.run(self._websocket_loop())

    async def _websocket_loop(self):
        """Async WebSocket connection handling"""
        while not self.should_stop:
            try:
                await self._connect_and_listen()
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                self.error_occurred.emit(str(e))

                if self._reconnect_attempts < self._max_reconnect_attempts:
                    self._reconnect_attempts += 1
                    attempts_msg = (
                        f"Attempting reconnect "
                        f"{self._reconnect_attempts}/"
                        f"{self._max_reconnect_attempts}"
                    )
                    logger.info(attempts_msg)
                    await asyncio.sleep(self._reconnect_delay)
                    self._reconnect_delay *= 2  # Exponential backoff
                else:
                    failed_msg = "Max reconnect attempts exceeded"
                    self.connection_failed.emit(failed_msg)
                    break

    async def _connect_and_listen(self):
        """Connect to WebSocket and listen for messages"""
        if self.session_id:
            ws_url = f"{self.server_url}/ws/session/{self.session_id}"
        else:
            ws_url = f"{self.server_url}/ws/general"

        logger.info(f"Connecting to WebSocket: {ws_url}")

        async with websockets.connect(ws_url) as websocket:
            self.websocket = websocket
            self._reconnect_attempts = 0
            self._reconnect_delay = 2
            self.connected.emit()

            try:
                async for message in websocket:
                    if self.should_stop:
                        break

                    try:
                        data = json.loads(message)
                        self.message_received.emit(data)
                    except json.JSONDecodeError as e:
                        decode_error = f"Failed to decode WebSocket message: {e}"
                        logger.error(decode_error)

            except websockets.exceptions.ConnectionClosed:
                logger.info("WebSocket connection closed")
                self.disconnected.emit()

    def stop(self):
        """Stop the WebSocket connection"""
        self.should_stop = True
        self.quit()
        self.wait(5000)  # Wait up to 5 seconds

    async def send_message(self, message: Dict[str, Any]):
        """Send message through WebSocket"""
        if self.websocket and not self.websocket.closed:
            try:
                await self.websocket.send(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send WebSocket message: {e}")
                self.error_occurred.emit(str(e))


class RealtimeService(QObject):
    """
    Real-time communication service for AutoGen UI

    Handles WebSocket connections, real-time updates,
    and coordinates between UI components.
    """

    # Signals for various real-time events
    session_updated = Signal(str, dict)  # session_id, update_data
    memory_updated = Signal(str, dict)  # scope, memory_data
    agent_status_changed = Signal(str, dict)  # agent_id, status_data
    server_status_changed = Signal(dict)  # server_status
    notification_received = Signal(str, str, str)  # level, title, message

    def __init__(self, server_url: str = "ws://localhost:9000"):
        super().__init__()
        self.server_url = server_url
        self.websocket_workers: Dict[str, WebSocketWorker] = {}
        self._event_handlers: Dict[str, Callable] = {}

        # Event batching and throttling
        self._event_batch: Dict[str, List[tuple]] = defaultdict(list)
        self._batch_timer = QTimer()
        self._batch_timer.timeout.connect(self._process_event_batch)
        self._batch_timer.setSingleShot(True)
        self._batch_interval = 100  # 100ms batching interval

        # Set up default event handlers
        self._setup_default_handlers()

        logger.info(f"RealtimeService initialized with server: {server_url}")

    def _setup_default_handlers(self):
        """Set up default event handlers"""
        self._event_handlers.update(
            {
                "session_update": self._handle_session_update,
                "memory_update": self._handle_memory_update,
                "agent_status": self._handle_agent_status,
                "server_status": self._handle_server_status,
                "notification": self._handle_notification,
                "error": self._handle_error,
            }
        )

    def connect_to_session(self, session_id: str):
        """Connect to a specific session for real-time updates"""
        if session_id in self.websocket_workers:
            logger.warning(f"Already connected to session {session_id}")
            return

        worker = WebSocketWorker(self.server_url, session_id)

        # Connect signals
        worker.connected.connect(lambda: self._on_worker_connected(session_id))
        worker.disconnected.connect(lambda: self._on_worker_disconnected(session_id))
        worker.message_received.connect(
            lambda msg: self._on_message_received(session_id, msg)
        )
        worker.error_occurred.connect(
            lambda err: self._on_worker_error(session_id, err)
        )
        worker.connection_failed.connect(
            lambda err: self._on_connection_failed(session_id, err)
        )

        self.websocket_workers[session_id] = worker
        worker.start()

        logger.info(f"Connecting to session {session_id}")

    def disconnect_from_session(self, session_id: str):
        """Disconnect from a session"""
        if session_id not in self.websocket_workers:
            logger.warning(f"Not connected to session {session_id}")
            return

        worker = self.websocket_workers[session_id]
        worker.stop()
        del self.websocket_workers[session_id]

        logger.info(f"Disconnected from session {session_id}")

    def disconnect_all(self):
        """Disconnect from all sessions"""
        for session_id in list(self.websocket_workers.keys()):
            self.disconnect_from_session(session_id)

    def register_event_handler(self, event_type: str, handler: Callable):
        """Register custom event handler"""
        self._event_handlers[event_type] = handler
        logger.info(f"Registered handler for event type: {event_type}")

    def _on_worker_connected(self, session_id: str):
        """Handle worker connection"""
        logger.info(f"Connected to session {session_id}")

    def _on_worker_disconnected(self, session_id: str):
        """Handle worker disconnection"""
        logger.info(f"Disconnected from session {session_id}")

    def _on_worker_error(self, session_id: str, error: str):
        """Handle worker error"""
        logger.error(f"WebSocket error for session {session_id}: {error}")

    def _on_connection_failed(self, session_id: str, error: str):
        """Handle connection failure"""
        logger.error(f"Failed to connect to session {session_id}: {error}")
        # Clean up failed worker
        if session_id in self.websocket_workers:
            del self.websocket_workers[session_id]

    def _on_message_received(self, session_id: str, message: dict):
        """Handle received WebSocket message"""
        try:
            event_type = message.get("type", "unknown")

            # Use batching for high-frequency events
            if event_type in ["memory_update", "session_update"]:
                self._queue_event_for_batch(event_type, session_id, message)
            elif event_type in self._event_handlers:
                # Process immediately for low-frequency events
                self._event_handlers[event_type](session_id, message)
            else:
                logger.warning(f"Unknown event type: {event_type}")

        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def _handle_session_update(self, session_id: str, message: dict):
        """Handle session update events"""
        update_data = message.get("data", {})
        self.session_updated.emit(session_id, update_data)

        # Check if this is a significant update worth notifying
        status = update_data.get("status")
        if status in ["completed", "failed", "started"]:
            title = f"Session {session_id}"
            msg = f"Session status changed to: {status}"
            self.notification_received.emit("info", title, msg)

    def _handle_memory_update(self, session_id: str, message: dict):
        """Handle memory update events"""
        update_data = message.get("data", {})
        scope = update_data.get("scope", "unknown")
        self.memory_updated.emit(scope, update_data)

    def _handle_agent_status(self, session_id: str, message: dict):
        """Handle agent status change events"""
        update_data = message.get("data", {})
        agent_id = update_data.get("agent_id", session_id)
        self.agent_status_changed.emit(agent_id, update_data)

    def _handle_server_status(self, session_id: str, message: dict):
        """Handle server status change events"""
        status_data = message.get("data", {})
        self.server_status_changed.emit(status_data)

    def _handle_notification(self, session_id: str, message: dict):
        """Handle notification events"""
        data = message.get("data", {})
        level = data.get("level", "info")
        title = data.get("title", "Notification")
        msg = data.get("message", "")
        self.notification_received.emit(level, title, msg)

    def _handle_error(self, session_id: str, message: dict):
        """Handle error events"""
        data = message.get("data", {})
        error_msg = data.get("message", "Unknown error occurred")
        logger.error(f"Server error: {error_msg}")
        self.notification_received.emit("error", "Server Error", error_msg)

    def _process_event_batch(self):
        """Process batched events to prevent UI flooding"""
        if not self._event_batch:
            return

        # Process each event type's batch
        for event_type, events in self._event_batch.items():
            if not events:
                continue

            # For memory updates, only process the most recent per scope
            if event_type == "memory_update":
                scope_latest = {}
                for session_id, message in events:
                    scope = message.get("data", {}).get("scope", "unknown")
                    scope_latest[scope] = (session_id, message)

                for session_id, message in scope_latest.values():
                    self._handle_memory_update(session_id, message)

            # For session updates, only process the most recent per session
            elif event_type == "session_update":
                session_latest = {}
                for session_id, message in events:
                    session_latest[session_id] = (session_id, message)

                for session_id, message in session_latest.values():
                    self._handle_session_update(session_id, message)

            # For other events, process all (they're typically less frequent)
            else:
                for session_id, message in events:
                    if event_type in self._event_handlers:
                        self._event_handlers[event_type](session_id, message)

        # Clear the batch
        self._event_batch.clear()
        logger.debug("Processed event batch")

    def _queue_event_for_batch(self, event_type: str, session_id: str, message: dict):
        """Queue an event for batch processing"""
        self._event_batch[event_type].append((session_id, message))

        # Start or restart the batch timer
        if not self._batch_timer.isActive():
            self._batch_timer.start(self._batch_interval)

    def is_connected(self, session_id: Optional[str] = None) -> bool:
        """Check if connected to session(s)"""
        if session_id:
            worker = self.websocket_workers.get(session_id)
            return worker is not None and worker.isRunning()
        else:
            return len(self.websocket_workers) > 0

    def get_connected_sessions(self) -> List[str]:
        """Get list of connected session IDs"""
        return list(self.websocket_workers.keys())

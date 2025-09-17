"""Server management panel for AutoGen UI.

This module provides a comprehensive server management interface including
real-time status monitoring, endpoint testing, and connection management.
"""

import logging
from typing import Optional
from datetime import datetime

from PySide6.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QTextEdit,
    QFrame,
    QTabWidget,
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QFont

from ...services import ServerService, ServerStatus, ServerHealth, EndpointInfo


class ServerStatusWidget(QFrame):
    """Widget displaying server connection status."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.Box)
        self.setFixedHeight(80)
        self._setup_ui()
        self._current_status = ServerStatus.DISCONNECTED

    def _setup_ui(self):
        """Set up the status widget UI."""
        layout = QHBoxLayout(self)

        # Status indicator
        self.status_label = QLabel("●")
        self.status_label.setFixedSize(20, 20)
        font = QFont()
        font.setPointSize(16)
        self.status_label.setFont(font)
        self.status_label.setAlignment(Qt.AlignCenter)

        # Status text
        self.status_text = QLabel("Disconnected")
        font = QFont()
        font.setBold(True)
        self.status_text.setFont(font)

        # Server info
        self.server_info = QLabel("MCP Server: localhost:9000")
        self.server_info.setStyleSheet("color: gray;")

        layout.addWidget(self.status_label)
        layout.addWidget(self.status_text)
        layout.addStretch()
        layout.addWidget(self.server_info)

        self.update_status(ServerStatus.DISCONNECTED)

    def update_status(
        self, status: ServerStatus, health: Optional[ServerHealth] = None
    ):
        """Update the status display."""
        self._current_status = status

        status_colors = {
            ServerStatus.CONNECTED: "#4CAF50",  # Green
            ServerStatus.CONNECTING: "#FF9800",  # Orange
            ServerStatus.DISCONNECTED: "#757575",  # Gray
            ServerStatus.ERROR: "#F44336",  # Red
        }

        status_texts = {
            ServerStatus.CONNECTED: "Connected",
            ServerStatus.CONNECTING: "Connecting...",
            ServerStatus.DISCONNECTED: "Disconnected",
            ServerStatus.ERROR: "Error",
        }

        color = status_colors.get(status, "#757575")
        text = status_texts.get(status, "Unknown")

        self.status_label.setStyleSheet(f"color: {color};")
        self.status_text.setText(text)

        # Update server info with health data
        if health and status == ServerStatus.CONNECTED:
            info_text = "MCP Server: localhost:9000 | "
            info_text += f"Version: {health.version} | "
            if health.uptime:
                info_text += f"Uptime: {health.uptime:.1f}s"
            self.server_info.setText(info_text)
        else:
            self.server_info.setText("MCP Server: localhost:9000")


class EndpointTestWidget(QWidget):
    """Widget for testing server endpoints."""

    def __init__(self, server_service: ServerService, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.server_service = server_service
        self.logger = logging.getLogger(f"{__name__}.EndpointTestWidget")
        self._setup_ui()
        self._connect_signals()
        self._load_endpoints()

    def _setup_ui(self):
        """Set up the endpoint testing UI."""
        layout = QVBoxLayout(self)

        # Control buttons
        controls_layout = QHBoxLayout()

        self.test_all_button = QPushButton("Test All Endpoints")
        self.test_all_button.clicked.connect(self._test_all_endpoints)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self._load_endpoints)

        controls_layout.addWidget(self.test_all_button)
        controls_layout.addWidget(self.refresh_button)
        controls_layout.addStretch()

        # Endpoint table
        self.endpoint_table = QTableWidget()
        self.endpoint_table.setColumnCount(6)
        self.endpoint_table.setHorizontalHeaderLabels(
            ["Method", "Endpoint", "Status", "Response Time", "Last Checked", "Error"]
        )

        # Auto-resize columns
        header = self.endpoint_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Endpoint column
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Status
        # Response Time
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        # Last Checked
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.Stretch)  # Error

        layout.addLayout(controls_layout)
        layout.addWidget(self.endpoint_table)

    def _connect_signals(self):
        """Connect server service signals."""
        self.server_service.endpoint_tested.connect(self._on_endpoint_tested)
        self.server_service.operation_started.connect(self._on_operation_started)
        self.server_service.operation_completed.connect(self._on_operation_completed)

    def _load_endpoints(self):
        """Load endpoints into the table."""
        endpoints = self.server_service.get_endpoints()
        self.endpoint_table.setRowCount(len(endpoints))

        for row, endpoint in enumerate(endpoints):
            self._update_endpoint_row(row, endpoint)

    def _update_endpoint_row(self, row: int, endpoint: EndpointInfo):
        """Update a single endpoint row."""
        # Method
        method_item = QTableWidgetItem(endpoint.method)
        method_item.setFlags(method_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.endpoint_table.setItem(row, 0, method_item)

        # Endpoint path
        path_item = QTableWidgetItem(endpoint.path)
        path_item.setFlags(path_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.endpoint_table.setItem(row, 1, path_item)

        # Status
        status_item = QTableWidgetItem(endpoint.status.value)
        status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        # Color code status
        status_colors = {
            ServerStatus.CONNECTED: "#4CAF50",
            ServerStatus.DISCONNECTED: "#757575",
            ServerStatus.ERROR: "#F44336",
        }
        if endpoint.status in status_colors:
            status_item.setData(
                Qt.ItemDataRole.BackgroundRole, status_colors[endpoint.status]
            )

        self.endpoint_table.setItem(row, 2, status_item)

        # Response time
        response_time = ""
        if endpoint.response_time is not None:
            response_time = f"{endpoint.response_time:.3f}s"
        response_item = QTableWidgetItem(response_time)
        flags = response_item.flags() & ~Qt.ItemFlag.ItemIsEditable
        response_item.setFlags(flags)
        self.endpoint_table.setItem(row, 3, response_item)

        # Last checked
        last_checked = ""
        if endpoint.last_checked:
            last_checked = endpoint.last_checked.strftime("%H:%M:%S")
        checked_item = QTableWidgetItem(last_checked)
        checked_flags = checked_item.flags() & ~Qt.ItemFlag.ItemIsEditable
        checked_item.setFlags(checked_flags)
        self.endpoint_table.setItem(row, 4, checked_item)

        # Error message
        error_msg = endpoint.error_message or ""
        error_item = QTableWidgetItem(error_msg)
        error_flags = error_item.flags() & ~Qt.ItemFlag.ItemIsEditable
        error_item.setFlags(error_flags)
        if error_msg:
            error_item.setToolTip(error_msg)
        self.endpoint_table.setItem(row, 5, error_item)

    @Slot(str, EndpointInfo)
    def _on_endpoint_tested(self, endpoint_path: str, endpoint_info: EndpointInfo):
        """Handle endpoint test results."""
        endpoints = self.server_service.get_endpoints()
        for row, endpoint in enumerate(endpoints):
            if endpoint.path == endpoint_path:
                self._update_endpoint_row(row, endpoint_info)
                break

    @Slot(str)
    def _on_operation_started(self, operation: str):
        """Handle operation started."""
        if operation == "test_all_endpoints":
            self.test_all_button.setEnabled(False)
            self.test_all_button.setText("Testing...")

    @Slot(str, dict)
    def _on_operation_completed(self, operation: str, result: dict):
        """Handle operation completed."""
        if operation == "test_all_endpoints":
            self.test_all_button.setEnabled(True)
            self.test_all_button.setText("Test All Endpoints")
            self._load_endpoints()  # Refresh the table

    def _test_all_endpoints(self):
        """Test all endpoints."""
        import asyncio
        import threading

        def run_test():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.server_service.test_all_endpoints())
            loop.close()

        thread = threading.Thread(target=run_test)
        thread.daemon = True
        thread.start()


class ServerLogWidget(QWidget):
    """Widget for displaying server logs and activity."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Set up the log widget UI."""
        layout = QVBoxLayout(self)

        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        # Limit log size using document method
        self.log_display.document().setMaximumBlockCount(1000)

        # Control buttons
        controls_layout = QHBoxLayout()

        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.log_display.clear)

        controls_layout.addStretch()
        controls_layout.addWidget(clear_button)

        layout.addWidget(self.log_display)
        layout.addLayout(controls_layout)

        # Add some initial content
        self._add_log_entry("Server monitoring started", "INFO")

    def _add_log_entry(self, message: str, level: str = "INFO"):
        """Add a log entry."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] {level}: {message}"

        # Color code based on level
        color = {
            "INFO": "black",
            "WARNING": "orange",
            "ERROR": "red",
            "SUCCESS": "green",
        }.get(level, "black")

        formatted_line = f'<span style="color: {color};">{log_line}</span>'
        self.log_display.append(formatted_line)

    def log_server_event(self, event: str, level: str = "INFO"):
        """Log a server event."""
        self._add_log_entry(event, level)


class ServerPanel(QDockWidget):
    """Main server management panel."""

    def __init__(self, server_service: ServerService, parent: Optional[QWidget] = None):
        super().__init__("Server Management", parent)
        self.server_service = server_service
        self.logger = logging.getLogger(f"{__name__}.ServerPanel")

        allowed_areas = (
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.setAllowedAreas(allowed_areas)
        self.setMinimumWidth(400)

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Set up the server panel UI."""
        # Main widget
        main_widget = QWidget()
        self.setWidget(main_widget)

        layout = QVBoxLayout(main_widget)

        # Status widget at the top
        self.status_widget = ServerStatusWidget()
        layout.addWidget(self.status_widget)

        # Tabbed interface for different server management aspects
        self.tab_widget = QTabWidget()

        # Endpoint testing tab
        self.endpoint_widget = EndpointTestWidget(self.server_service)
        self.tab_widget.addTab(self.endpoint_widget, "Endpoints")

        # Server logs tab
        self.log_widget = ServerLogWidget()
        self.tab_widget.addTab(self.log_widget, "Logs")

        layout.addWidget(self.tab_widget)

        # Initialize display
        self._update_status_display()

    def _connect_signals(self):
        """Connect server service signals."""
        self.server_service.server_status_changed.connect(self._on_status_changed)
        self.server_service.health_updated.connect(self._on_health_updated)
        self.server_service.operation_started.connect(self._on_operation_started)
        self.server_service.operation_completed.connect(self._on_operation_completed)
        self.server_service.operation_failed.connect(self._on_operation_failed)

    @Slot(ServerStatus)
    def _on_status_changed(self, status: ServerStatus):
        """Handle server status changes."""
        self._update_status_display()

        status_messages = {
            ServerStatus.CONNECTED: ("Connected to MCP server", "SUCCESS"),
            ServerStatus.CONNECTING: ("Connecting to MCP server...", "INFO"),
            ServerStatus.DISCONNECTED: ("Disconnected from MCP server", "WARNING"),
            ServerStatus.ERROR: ("MCP server connection error", "ERROR"),
        }

        if status in status_messages:
            message, level = status_messages[status]
            self.log_widget.log_server_event(message, level)

    @Slot(ServerHealth)
    def _on_health_updated(self, health: ServerHealth):
        """Handle server health updates."""
        self._update_status_display()

        if health.status == ServerStatus.CONNECTED:
            healthy = health.endpoints_healthy
            total = health.endpoints_total
            msg = f"Health check successful - {healthy}/{total} endpoints"
            self.log_widget.log_server_event(f"{msg} healthy", "SUCCESS")

    @Slot(str)
    def _on_operation_started(self, operation: str):
        """Handle operation started."""
        if operation.startswith("test_endpoint_"):
            endpoint = operation.replace("test_endpoint_", "")
            msg = f"Testing endpoint: {endpoint}"
            self.log_widget.log_server_event(msg, "INFO")

    @Slot(str, dict)
    def _on_operation_completed(self, operation: str, result: dict):
        """Handle operation completed."""
        if operation.startswith("test_endpoint_"):
            endpoint = operation.replace("test_endpoint_", "")
            status = result.get("status", "unknown")
            response_time = result.get("response_time", 0)
            msg = f"Endpoint {endpoint} test completed: {status}"
            timing = f" ({response_time:.3f}s)"
            level = "SUCCESS" if status == "connected" else "WARNING"
            self.log_widget.log_server_event(msg + timing, level)

    @Slot(str, str)
    def _on_operation_failed(self, operation: str, error: str):
        """Handle operation failed."""
        if operation.startswith("test_endpoint_"):
            endpoint = operation.replace("test_endpoint_", "")
            msg = f"Endpoint {endpoint} test failed: {error}"
            self.log_widget.log_server_event(msg, "ERROR")

    def _update_status_display(self):
        """Update the status display."""
        status = self.server_service.get_server_status()
        health = self.server_service.get_server_health()
        self.status_widget.update_status(status, health)

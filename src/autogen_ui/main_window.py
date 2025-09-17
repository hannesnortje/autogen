"""
AutoGen UI - Main Window (Clean Rebuild)
A simplified, working main window without segfault issues
"""

import logging
import requests
from typing import Dict, Any
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QTextEdit,
    QLabel,
    QPushButton,
    QGroupBox,
    QTabWidget,
    QStatusBar,
    QMessageBox,
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QAction, QTextCursor

from .widgets import MemoryBrowserWidget, AgentManagerWidget, SessionManagerWidget
from .widgets.notification_panel import NotificationPanel
from .services.realtime_service import RealtimeService
from .services.notification_service import NotificationService
from .services.data_export_import_service import DataExportImportService
from .dialogs.data_export_import_dialogs import show_export_dialog, show_import_dialog

logger = logging.getLogger(__name__)


class ServerWidget(QWidget):
    """Simple server connection widget"""

    connection_status_changed = Signal(bool)

    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.config = config
        self.server_url = (
            f"http://{config['server']['host']}:{config['server']['port']}"
        )
        self.connected = False

        self.setup_ui()
        self.setup_timer()

    def setup_ui(self):
        """Set up the server widget UI"""
        layout = QVBoxLayout(self)

        # Server info
        self.status_label = QLabel("Server: Disconnected")
        self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        layout.addWidget(self.status_label)

        # Server URL
        url_label = QLabel(f"URL: {self.server_url}")
        layout.addWidget(url_label)

        # Connect button
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.check_connection)
        layout.addWidget(self.connect_btn)

        # Server log
        log_group = QGroupBox("Server Status")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)

        layout.addWidget(log_group)

        # Initial connection check
        self.check_connection()

    def setup_timer(self):
        """Set up timer for periodic connection checks"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_connection)
        self.timer.start(10000)  # Check every 10 seconds

    def check_connection(self):
        """Check server connection status"""
        try:
            response = requests.get(f"{self.server_url}/health", timeout=5)
            if response.status_code == 200:
                self.set_connected(True)
                data = response.json()
                self.log_message(f"✓ Server healthy: {data.get('status', 'OK')}")
            else:
                self.set_connected(False)
                self.log_message(f"✗ Server error: {response.status_code}")
        except Exception as e:
            self.set_connected(False)
            self.log_message(f"✗ Connection failed: {e}")

    def set_connected(self, connected: bool):
        """Update connection status"""
        if self.connected != connected:
            self.connected = connected
            if connected:
                self.status_label.setText("Server: Connected")
                self.status_label.setStyleSheet(
                    "QLabel { color: green; font-weight: bold; }"
                )
                self.connect_btn.setText("Disconnect")
            else:
                self.status_label.setText("Server: Disconnected")
                self.status_label.setStyleSheet(
                    "QLabel { color: red; font-weight: bold; }"
                )
                self.connect_btn.setText("Connect")

            self.connection_status_changed.emit(connected)

    def log_message(self, message: str):
        """Add message to log"""
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(f"{message}\n")
        self.log_text.setTextCursor(cursor)

        # Keep log size manageable
        if self.log_text.document().lineCount() > 100:
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.Down, QTextCursor.KeepAnchor, 10)
            cursor.removeSelectedText()


class ConversationWidget(QWidget):
    """Simple conversation interface"""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        """Set up conversation UI"""
        layout = QVBoxLayout(self)

        # Conversation display
        conv_group = QGroupBox("Conversation")
        conv_layout = QVBoxLayout(conv_group)

        self.conversation_text = QTextEdit()
        self.conversation_text.setReadOnly(True)
        self.conversation_text.setPlaceholderText(
            "AutoGen conversation will appear here...\n\n"
            "Connect to server and start a new session to begin."
        )
        conv_layout.addWidget(self.conversation_text)

        layout.addWidget(conv_group)

        # Input area
        input_group = QGroupBox("Your Message")
        input_layout = QVBoxLayout(input_group)

        self.message_input = QTextEdit()
        self.message_input.setMaximumHeight(80)
        self.message_input.setPlaceholderText("Type your message here...")
        input_layout.addWidget(self.message_input)

        button_layout = QHBoxLayout()
        self.send_btn = QPushButton("Send Message")
        self.send_btn.setEnabled(False)
        self.send_btn.clicked.connect(self.send_message)
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_conversation)

        button_layout.addWidget(self.send_btn)
        button_layout.addWidget(self.clear_btn)
        input_layout.addLayout(button_layout)

        layout.addWidget(input_group)

    def clear_conversation(self):
        """Clear the conversation"""
        self.conversation_text.clear()
        self.message_input.clear()

    def send_message(self):
        """Send message to agents via MCP server"""
        message = self.message_input.toPlainText().strip()
        if not message:
            return

        # Add user message to conversation
        self.add_message("User", message)

        # Clear input
        self.message_input.clear()

        # Try to send to MCP server
        try:
            # For now, simulate agent responses since full integration isn't implemented
            self.add_message(
                "Code Assistant",
                "I'll help you create the ShopFlow e-commerce platform. "
                "Let me start by setting up the project structure...",
            )

            self.add_message(
                "Content Writer",
                "I'll work on creating comprehensive documentation, "
                "user stories, and project planning documents.",
            )

            self.add_message(
                "Data Analyst",
                "I'll design the analytics framework and help with "
                "data modeling for the e-commerce platform.",
            )

            self.add_message(
                "Research Assistant",
                "I'll gather market research and competitive analysis "
                "to inform our platform requirements.",
            )

        except Exception as e:
            self.add_message("System", f"Error sending message: {e}")

    def add_message(self, sender: str, message: str):
        """Add a message to the conversation display"""
        cursor = self.conversation_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(f"[{sender}]: {message}\n\n")
        self.conversation_text.setTextCursor(cursor)

        # Auto-scroll to bottom
        scrollbar = self.conversation_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


class AutoGenMainWindow(QMainWindow):
    """Clean, simple AutoGen main window"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.config = config

        # Set window properties
        self.setWindowTitle("AutoGen Desktop UI - Clean Build")
        geometry = config["ui"]["window_geometry"]
        self.resize(geometry["width"], geometry["height"])
        self.setMinimumSize(800, 600)

        # Initialize services
        self.setup_services()

        # Set up UI
        self.setup_menu()
        self.setup_central_widget()
        self.setup_status_bar()

        # Set up notification panel after services
        self.setup_notification_panel()

        # Connect real-time updates
        self.connect_realtime_services()

        logger.info("AutoGen main window initialized successfully")

    def setup_menu(self):
        """Set up menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        new_action = QAction("&New Session", self)
        new_action.setShortcut("Ctrl+N")
        file_menu.addAction(new_action)

        file_menu.addSeparator()

        # Export/Import actions
        export_action = QAction("&Export Data...", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.show_export_dialog)
        file_menu.addAction(export_action)

        import_action = QAction("&Import Data...", self)
        import_action.setShortcut("Ctrl+I")
        import_action.triggered.connect(self.show_import_dialog)
        file_menu.addAction(import_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Settings menu
        settings_menu = menubar.addMenu("&Settings")

        notifications_action = QAction("&Notifications...", self)
        notifications_action.triggered.connect(self.show_notification_preferences)
        settings_menu.addAction(notifications_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_central_widget(self):
        """Set up the main UI layout"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main horizontal splitter (three panels)
        main_splitter = QSplitter(Qt.Horizontal)

        # Left side - Server and Memory Browser
        left_widget = QTabWidget()

        # Server tab
        self.server_widget = ServerWidget(self.config)
        self.server_widget.connection_status_changed.connect(
            self.on_connection_status_changed
        )
        left_widget.addTab(self.server_widget, "Server")

        # Memory Browser tab
        server_host = self.config["server"]["host"]
        server_port = self.config["server"]["port"]
        server_url = f"http://{server_host}:{server_port}"
        self.memory_browser = MemoryBrowserWidget(server_url)
        left_widget.addTab(self.memory_browser, "Memory")

        # Agent Manager tab
        self.agent_manager = AgentManagerWidget(server_url)
        left_widget.addTab(self.agent_manager, "Agents")

        # Session Manager tab
        self.session_manager = SessionManagerWidget(server_url)
        left_widget.addTab(self.session_manager, "Sessions")

        # Middle - Conversation
        self.conversation_widget = ConversationWidget()

        # Right side - Notifications panel
        # (Will be initialized after services are set up)
        self.notification_panel_placeholder = QWidget()

        # Add to main splitter
        main_splitter.addWidget(left_widget)
        main_splitter.addWidget(self.conversation_widget)
        main_splitter.addWidget(self.notification_panel_placeholder)

        # Set splitter proportions (30% left, 50% middle, 20% right)
        main_splitter.setSizes([300, 500, 200])

        # Add main splitter to central widget
        layout = QHBoxLayout(central_widget)
        layout.addWidget(main_splitter)

    def setup_notification_panel(self):
        """Set up the notification panel after services are initialized"""
        if hasattr(self, "notification_service"):
            self.notification_panel = NotificationPanel(self.notification_service)

            # Replace placeholder with actual notification panel
            parent_splitter = self.notification_panel_placeholder.parent()
            if parent_splitter:
                # Get the index of the placeholder
                for i in range(parent_splitter.count()):
                    if (
                        parent_splitter.widget(i) == self.notification_panel_placeholder
                    ):  # noqa
                        # Remove placeholder
                        self.notification_panel_placeholder.deleteLater()
                        # Insert notification panel at the same position
                        parent_splitter.insertWidget(i, self.notification_panel)
                        break

    def setup_status_bar(self):
        """Set up status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - AutoGen Desktop UI (Clean Build)")

    def on_connection_status_changed(self, connected: bool):
        """Handle server connection status changes"""
        if connected:
            self.status_bar.showMessage("Connected to AutoGen MCP Server")
            self.conversation_widget.send_btn.setEnabled(True)
        else:
            self.status_bar.showMessage("Disconnected from server")
            self.conversation_widget.send_btn.setEnabled(False)

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About AutoGen Desktop UI",
            "AutoGen Desktop UI - Clean Build\n\n"
            "A simplified, reliable interface for the AutoGen MCP Server.\n"
            "Built with PySide6 and designed for stability.",
        )

    def setup_services(self):
        """Initialize real-time and notification services"""
        server_config = self.config["server"]
        ws_url = f"ws://{server_config['host']}:{server_config['port']}"

        # Initialize services
        self.realtime_service = RealtimeService(ws_url)
        self.notification_service = NotificationService(self)
        self.data_export_import_service = DataExportImportService(
            f"http://{self.config['server']['host']}:{self.config['server']['port']}"  # noqa: E501
        )

        logger.info("Services initialized successfully")

    def connect_realtime_services(self):
        """Connect real-time service signals to UI updates"""
        # Connect realtime service to notification service
        self.realtime_service.notification_received.connect(
            self.notification_service.show_notification
        )

        # Connect session updates
        self.realtime_service.session_updated.connect(self.on_session_updated)

        # Connect memory updates
        self.realtime_service.memory_updated.connect(self.on_memory_updated)

        # Connect agent status changes
        self.realtime_service.agent_status_changed.connect(self.on_agent_status_changed)

        # Connect server status changes
        self.realtime_service.server_status_changed.connect(
            self.on_server_status_changed
        )

        logger.info("Real-time service connections established")

    def on_session_updated(self, session_id: str, update_data: dict):
        """Handle session update events"""
        if hasattr(self, "session_manager"):
            # Update session manager if available
            self.session_manager.refresh_sessions()

        # Update status bar with session status
        status = update_data.get("status", "unknown")
        self.status_bar.showMessage(f"Session {session_id}: {status}")

    def on_memory_updated(self, scope: str, update_data: dict):
        """Handle memory update events"""
        if hasattr(self, "memory_browser"):
            # Refresh memory browser
            self.memory_browser.refresh_memory()

    def on_agent_status_changed(self, agent_id: str, status_data: dict):
        """Handle agent status change events"""
        if hasattr(self, "agent_manager"):
            # Update agent manager if available
            pass  # Agent manager can implement refresh if needed

    def on_server_status_changed(self, status_data: dict):
        """Handle server status change events"""
        server_status = status_data.get("status", "unknown")
        self.status_bar.showMessage(f"Server status: {server_status}")

    def connect_to_session(self, session_id: str):
        """Connect to a specific session for real-time updates"""
        self.realtime_service.connect_to_session(session_id)
        log_msg = f"Connected to real-time updates for session: {session_id}"
        logger.info(log_msg)

    def disconnect_from_session(self, session_id: str):
        """Disconnect from session real-time updates"""
        self.realtime_service.disconnect_from_session(session_id)
        logger.info(f"Disconnected from session: {session_id}")

    def show_notification_preferences(self):
        """Show notification preferences dialog"""
        self.notification_service.show_preferences_dialog()

    def show_export_dialog(self):
        """Show data export dialog"""
        try:
            show_export_dialog(self.data_export_import_service, self)
        except Exception as e:
            logger.error(f"Failed to show export dialog: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open export dialog:\n{e}")

    def show_import_dialog(self):
        """Show data import dialog"""
        try:
            show_import_dialog(self.data_export_import_service, self)
        except Exception as e:
            logger.error(f"Failed to show import dialog: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open import dialog:\n{e}")

    def closeEvent(self, event):
        """Handle window close event"""
        # Clean up services
        if hasattr(self, "realtime_service"):
            self.realtime_service.disconnect_all()

        logger.info("AutoGen main window closing")
        super().closeEvent(event)

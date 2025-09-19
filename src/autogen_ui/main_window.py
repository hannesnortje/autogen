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
from .widgets.enhanced_conversation_widget import EnhancedConversationWidget
from .widgets.notification_panel import NotificationPanel
from .services.realtime_service import RealtimeService
from .services.notification_service import NotificationService
from .services.data_export_import_service import DataExportImportService
from .services.conversation_service import ConversationService
from .services.session_service import SessionService
from .dialogs.data_export_import_dialogs import show_export_dialog, show_import_dialog

logger = logging.getLogger(__name__)


class ServerWidget(QWidget):
    """Enhanced server connection widget with reconnection logic"""

    connection_status_changed = Signal(bool)

    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.config = config
        self.server_url = (
            f"http://{config['server']['host']}:{config['server']['port']}"
        )
        self.connected = False
        self.reconnecting = False

        # Reconnection settings
        self.retry_attempts = 0
        self.max_retry_attempts = 5
        self.base_retry_delay = 2  # seconds
        self.current_retry_delay = self.base_retry_delay
        self.consecutive_failures = 0
        self.last_successful_connection = None

        # Setup timers first, then UI (since UI setup calls check_connection)
        self.setup_timer()
        self.setup_ui()

    def setup_ui(self):
        """Set up the server widget UI"""
        layout = QVBoxLayout(self)

        # Connection status with info
        status_layout = QHBoxLayout()

        self.status_label = QLabel("Server: Checking...")
        self.status_label.setStyleSheet("QLabel { font-weight: bold; }")
        status_layout.addWidget(self.status_label)

        # Connect button
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setMaximumWidth(100)
        self.connect_btn.clicked.connect(self.manual_reconnect)
        status_layout.addWidget(self.connect_btn)

        layout.addLayout(status_layout)

        # Server URL
        url_label = QLabel(f"URL: {self.server_url}")
        layout.addWidget(url_label)

        # Connection info
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("QLabel { color: gray; font-size: 10px; }")
        layout.addWidget(self.info_label)

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
        self.timer.start(5000)  # Check every 5 seconds (more responsive)

        # Separate timer for reconnection attempts
        self.reconnect_timer = QTimer()
        self.reconnect_timer.setSingleShot(True)
        self.reconnect_timer.timeout.connect(self.attempt_reconnection)

    def check_connection(self):
        """Check server connection status"""
        try:
            response = requests.get(f"{self.server_url}/health", timeout=3)
            if response.status_code == 200:
                # Connection successful
                if not self.connected or self.reconnecting:
                    # We've recovered from a disconnection
                    self.reset_retry_state()
                    self.log_message("✅ Connection restored!")

                self.set_connected(True)
                data = response.json()
                status = data.get("status", "OK")
                self.log_message(f"✓ Server healthy: {status}")

                # Update last successful connection time
                import datetime

                self.last_successful_connection = datetime.datetime.now()
            else:
                error_msg = f"Server error: {response.status_code}"
                self.handle_connection_failure(error_msg)
        except Exception as e:
            self.handle_connection_failure(f"Connection failed: {str(e)}")

    def handle_connection_failure(self, error_message: str):
        """Handle connection failure with smart reconnection logic"""
        self.consecutive_failures += 1

        if self.connected:
            # First failure - log and mark as disconnected
            self.set_connected(False)
            self.log_message(f"✗ {error_message}")

        if not self.reconnecting and self.retry_attempts < self.max_retry_attempts:
            # Start reconnection process
            self.start_reconnection_process()

        # Only log every few attempts to avoid spam
        if self.consecutive_failures == 1 or self.consecutive_failures % 3 == 0:
            self.log_message(f"✗ {error_message}")

    def start_reconnection_process(self):
        """Start the reconnection process"""
        if self.retry_attempts >= self.max_retry_attempts:
            msg = "❌ Max reconnection attempts exceeded. Manual reconnection required."
            self.log_message(msg)
            self.set_reconnecting(False)
            return

        self.set_reconnecting(True)
        self.retry_attempts += 1

        # Calculate exponential backoff delay (max 30 seconds)
        delay = self.base_retry_delay * (2 ** (self.retry_attempts - 1))
        self.current_retry_delay = min(delay, 30)

        msg = (
            f"🔄 Attempting reconnection {self.retry_attempts}/"
            f"{self.max_retry_attempts} in {self.current_retry_delay}s..."
        )
        self.log_message(msg)

        # Start reconnection timer
        self.reconnect_timer.start(int(self.current_retry_delay * 1000))

    def attempt_reconnection(self):
        """Attempt to reconnect (called by timer)"""
        self.log_message(f"🔄 Reconnection attempt {self.retry_attempts}...")
        self.check_connection()

        if not self.connected:
            # This attempt failed, try again
            QTimer.singleShot(1000, self.start_reconnection_process)

    def manual_reconnect(self):
        """Manual reconnection triggered by user"""
        self.reset_retry_state()
        self.log_message("🔄 Manual reconnection requested...")
        self.check_connection()

    def reset_retry_state(self):
        """Reset the retry state after successful connection"""
        self.retry_attempts = 0
        self.current_retry_delay = self.base_retry_delay
        self.consecutive_failures = 0
        self.set_reconnecting(False)
        if self.reconnect_timer.isActive():
            self.reconnect_timer.stop()

    def set_reconnecting(self, reconnecting: bool):
        """Update reconnecting status"""
        self.reconnecting = reconnecting
        self.update_ui_state()

    def update_ui_state(self):
        """Update UI based on current connection state"""
        import datetime

        current_time = datetime.datetime.now().strftime("%H:%M:%S")

        if self.connected:
            self.status_label.setText("Server: Connected")
            self.status_label.setStyleSheet(
                "QLabel { color: green; font-weight: bold; }"
            )
            self.connect_btn.setText("Reconnect")
            self.info_label.setText(f"Last check: {current_time}")
        elif self.reconnecting:
            self.status_label.setText("Server: Reconnecting...")
            self.status_label.setStyleSheet(
                "QLabel { color: orange; font-weight: bold; }"
            )
            self.connect_btn.setText("Retry Now")
            if self.retry_attempts > 0:
                retry_info = (
                    f"Retry {self.retry_attempts}/"
                    f"{self.max_retry_attempts} - "
                    f"Next in {self.current_retry_delay}s"
                )
                self.info_label.setText(retry_info)
        else:
            self.status_label.setText("Server: Disconnected")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
            self.connect_btn.setText("Connect")
            if self.retry_attempts >= self.max_retry_attempts:
                msg = "Max retries exceeded - click Connect to retry"
                self.info_label.setText(msg)
            else:
                self.info_label.setText(f"Connection lost at {current_time}")

    def set_connected(self, connected: bool):
        """Update connection status"""
        if self.connected != connected:
            self.connected = connected
            self.update_ui_state()
            self.connection_status_changed.emit(connected)

    def log_message(self, message: str):
        """Add message to log with timestamp"""
        import datetime

        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(f"[{timestamp}] {message}\n")
        self.log_text.setTextCursor(cursor)

        # Keep log size manageable
        if self.log_text.document().lineCount() > 100:
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.Down, QTextCursor.KeepAnchor, 10)
            cursor.removeSelectedText()


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

        # Middle - Conversation (using enhanced conversation widget with services)
        self.conversation_widget = EnhancedConversationWidget(
            self.conversation_service, use_mcp=True
        )

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
        server_url = f"http://{server_config['host']}:{server_config['port']}"
        ws_url = f"ws://{server_config['host']}:{server_config['port']}"

        # Initialize services
        self.session_service = SessionService(server_url)
        self.conversation_service = ConversationService(self.session_service)
        self.realtime_service = RealtimeService(ws_url)
        self.notification_service = NotificationService(self)
        self.data_export_import_service = DataExportImportService(server_url)

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

        # Connect session manager signals to conversation widget
        if hasattr(self, "session_manager"):
            logger.info("Connecting session manager signals to conversation widget")
            self.session_manager.session_started.connect(
                lambda config: self._on_session_started_for_conversation(config)
            )
            self.session_manager.session_ended.connect(
                lambda session_id: self._on_session_ended_for_conversation(session_id)
            )
        else:
            logger.warning(
                "No session_manager found - conversation widget won't receive session updates!"
            )

        logger.info("Real-time service connections established")

    def _on_session_started_for_conversation(self, config: dict):
        """Handle session started signal for conversation widget"""
        session_id = config.get("session_id") or config.get("name")
        logger.info(f"Main Window: Session started callback - session_id: {session_id}")
        logger.info(f"Main Window: Full config: {config}")
        if session_id:
            logger.info(
                f"Main Window: Setting conversation widget session_id to: {session_id}"
            )
            self.conversation_widget.set_session_id(session_id)

            # CRITICAL FIX: Start the conversation in the service
            logger.info(
                f"Main Window: Starting conversation service for session: {session_id}"
            )
            self.conversation_service.start_conversation(session_id, config)
        else:
            logger.warning("Session started but no session_id or name in config!")
            logger.warning(f"Config keys: {list(config.keys())}")

    def _on_session_ended_for_conversation(self, session_id: str):
        """Handle session ended signal for conversation widget"""
        logger.info(f"Main Window: Session ended callback - session_id: {session_id}")
        self.conversation_widget.set_session_id(None)

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

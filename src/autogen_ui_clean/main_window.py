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

        # Set up UI
        self.setup_menu()
        self.setup_central_widget()
        self.setup_status_bar()

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

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_central_widget(self):
        """Set up the main UI layout"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main horizontal splitter
        splitter = QSplitter(Qt.Horizontal)

        # Left side - Server and Memory Browser
        left_widget = QTabWidget()

        # Server tab
        self.server_widget = ServerWidget(self.config)
        self.server_widget.connection_status_changed.connect(
            self.on_connection_status_changed
        )
        left_widget.addTab(self.server_widget, "Server")

        # Memory Browser tab
        server_url = (
            f"http://{self.config['server']['host']}:{self.config['server']['port']}"
        )
        self.memory_browser = MemoryBrowserWidget(server_url)
        left_widget.addTab(self.memory_browser, "Memory")

        # Agent Manager tab
        self.agent_manager = AgentManagerWidget(server_url)
        left_widget.addTab(self.agent_manager, "Agents")

        # Session Manager tab
        self.session_manager = SessionManagerWidget(server_url)
        left_widget.addTab(self.session_manager, "Sessions")

        # Right side - Conversation
        self.conversation_widget = ConversationWidget()

        # Add to splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(self.conversation_widget)

        # Set splitter proportions (40% left, 60% right)
        splitter.setSizes([400, 600])

        # Add splitter to central widget
        layout = QHBoxLayout(central_widget)
        layout.addWidget(splitter)

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

    def closeEvent(self, event):
        """Handle window close event"""
        logger.info("AutoGen main window closing")
        super().closeEvent(event)

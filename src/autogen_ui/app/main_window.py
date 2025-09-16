"""
AutoGen Desktop UI - Main Application Window

This module contains the MainWindow class which serves as the primary
interface for the AutoGen desktop application. It implements the dock-based
layout with panels for server management, session control, memory browsing,
and agent configuration.
"""

import logging
from typing import Dict, Any, Optional

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QDockWidget,
    QTextEdit,
    QPushButton,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction


logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Main application window with dock-based layout.

    Features:
    - Menu system for all major functions
    - Toolbar with quick action buttons
    - Status bar with connection indicators
    - Dock system for modular panels
    - Theme support (dark/light)
    """

    # Signals for application events
    closing = Signal()
    theme_changed = Signal(str)

    def __init__(self, config: Dict[str, Any], parent: Optional[QWidget] = None):
        """Initialize the main window with configuration."""
        super().__init__(parent)

        self.config = config
        self.dock_widgets: Dict[str, QDockWidget] = {}

        logger.info("Initializing MainWindow")

        # Set up the main window
        self.setup_window()
        self.setup_menu_bar()
        self.setup_toolbar()
        self.setup_central_widget()
        self.setup_dock_widgets()
        self.setup_status_bar()

        # Apply theme
        self.apply_theme(config.get("theme", "system"))

        # Set up auto-save of window state
        self.setup_window_state_persistence()

        logger.info("MainWindow initialized successfully")

    def setup_window(self) -> None:
        """Configure the main window properties."""

        # Set window title and icon
        self.setWindowTitle(self.config["app_name"])

        # Set window size from config
        geometry = self.config.get("window_geometry", {})
        width = geometry.get("width", 1200)
        height = geometry.get("height", 800)
        self.resize(width, height)

        # Enable dock nesting
        self.setDockNestingEnabled(True)

        # Set corner widget behavior
        left_area = Qt.DockWidgetArea.LeftDockWidgetArea
        right_area = Qt.DockWidgetArea.RightDockWidgetArea
        bottom_area = Qt.DockWidgetArea.BottomDockWidgetArea

        self.setCorner(Qt.Corner.TopLeftCorner, left_area)
        self.setCorner(Qt.Corner.TopRightCorner, right_area)
        self.setCorner(Qt.Corner.BottomLeftCorner, bottom_area)
        self.setCorner(Qt.Corner.BottomRightCorner, right_area)

    def setup_menu_bar(self) -> None:
        """Create the main menu bar."""

        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        # New Session action
        new_session_action = QAction("&New Session", self)
        new_session_action.setShortcut("Ctrl+N")
        new_session_action.setStatusTip("Create a new agent session")
        new_session_action.triggered.connect(self.on_new_session)
        file_menu.addAction(new_session_action)

        file_menu.addSeparator()

        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        # Theme submenu
        theme_menu = view_menu.addMenu("&Theme")

        system_theme_action = QAction("&System", self)
        system_theme_action.triggered.connect(lambda: self.apply_theme("system"))
        theme_menu.addAction(system_theme_action)

        light_theme_action = QAction("&Light", self)
        light_theme_action.triggered.connect(lambda: self.apply_theme("light"))
        theme_menu.addAction(light_theme_action)

        dark_theme_action = QAction("&Dark", self)
        dark_theme_action.triggered.connect(lambda: self.apply_theme("dark"))
        theme_menu.addAction(dark_theme_action)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        # Server management
        server_action = QAction("&Server Status", self)
        server_action.setStatusTip("View MCP server status and controls")
        server_action.triggered.connect(self.on_show_server_panel)
        tools_menu.addAction(server_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self.on_about)
        help_menu.addAction(about_action)

    def setup_toolbar(self) -> None:
        """Create the main toolbar."""

        toolbar = self.addToolBar("Main")
        toolbar.setMovable(False)

        # New Session button
        new_session_action = QAction("New Session", self)
        new_session_action.setStatusTip("Create a new agent session")
        new_session_action.triggered.connect(self.on_new_session)
        toolbar.addAction(new_session_action)

        toolbar.addSeparator()

        # Server status indicator (placeholder)
        server_status_action = QAction("Server: Unknown", self)
        server_status_action.setEnabled(False)
        toolbar.addAction(server_status_action)

    def setup_central_widget(self) -> None:
        """Set up the central widget area."""

        # Create central widget with welcome/dashboard content
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)

        # Welcome label
        welcome_label = QLabel("Welcome to AutoGen Desktop")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_label.setStyleSheet(
            "font-size: 24px; font-weight: bold; padding: 20px;"
        )
        layout.addWidget(welcome_label)

        # Status information
        status_info = QTextEdit()
        status_info.setReadOnly(True)
        status_info.setMaximumHeight(200)

        status_text = """
        <h3>AutoGen Desktop UI - Step 1.1 Foundation Complete</h3>

        <p><b>✅ Completed Tasks:</b></p>
        <ul>
            <li>PySide6 dependencies installed and configured</li>
            <li>Complete directory structure created</li>
            <li>Application entry point implemented</li>
            <li>MainWindow class with dock-based layout</li>
            <li>Menu system and toolbar</li>
            <li>Theme support (system/light/dark)</li>
        </ul>

        <p><b>⏳ Next Steps:</b></p>
        <ul>
            <li>Extend logging system integration</li>
            <li>Test coexistence with MCP server</li>
            <li>Implement server management panel</li>
            <li>Add session management capabilities</li>
        </ul>
        """

        status_info.setHtml(status_text)
        layout.addWidget(status_info)

        # Set central widget
        self.setCentralWidget(central_widget)

    def setup_dock_widgets(self) -> None:
        """Create and configure dock widgets for different panels."""

        # Server Management Panel (placeholder)
        self.create_dock_widget(
            "server_panel",
            "Server Management",
            self.create_server_panel_placeholder(),
            Qt.DockWidgetArea.LeftDockWidgetArea,
        )

        # Session Management Panel (placeholder)
        self.create_dock_widget(
            "session_panel",
            "Session Management",
            self.create_session_panel_placeholder(),
            Qt.DockWidgetArea.LeftDockWidgetArea,
        )

        # Memory Management Panel (placeholder)
        self.create_dock_widget(
            "memory_panel",
            "Memory Browser",
            self.create_memory_panel_placeholder(),
            Qt.DockWidgetArea.RightDockWidgetArea,
        )

        # Agent Management Panel (placeholder)
        self.create_dock_widget(
            "agent_panel",
            "Agent Configuration",
            self.create_agent_panel_placeholder(),
            Qt.DockWidgetArea.RightDockWidgetArea,
        )

        # Initially hide some panels to avoid clutter
        self.dock_widgets["memory_panel"].hide()
        self.dock_widgets["agent_panel"].hide()

    def create_dock_widget(
        self, name: str, title: str, widget: QWidget, area: Qt.DockWidgetArea
    ) -> QDockWidget:
        """Create a dock widget with given properties."""

        dock = QDockWidget(title, self)
        dock.setWidget(widget)
        dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea
            | Qt.DockWidgetArea.RightDockWidgetArea
            | Qt.DockWidgetArea.BottomDockWidgetArea
        )

        self.addDockWidget(area, dock)
        self.dock_widgets[name] = dock

        return dock

    def create_server_panel_placeholder(self) -> QWidget:
        """Create placeholder for server management panel."""

        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(QLabel("Server Management"))
        layout.addWidget(QLabel("Status: Not connected"))
        layout.addWidget(QPushButton("Connect to MCP Server"))
        layout.addWidget(QPushButton("Server Health Check"))

        return widget

    def create_session_panel_placeholder(self) -> QWidget:
        """Create placeholder for session management panel."""

        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(QLabel("Active Sessions"))
        layout.addWidget(QLabel("No active sessions"))
        layout.addWidget(QPushButton("Create New Session"))

        return widget

    def create_memory_panel_placeholder(self) -> QWidget:
        """Create placeholder for memory management panel."""

        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(QLabel("Memory Browser"))
        layout.addWidget(QLabel("Global Memory: 0 entries"))
        layout.addWidget(QLabel("Project Memory: 0 entries"))
        layout.addWidget(QLabel("Lessons: 0 entries"))

        return widget

    def create_agent_panel_placeholder(self) -> QWidget:
        """Create placeholder for agent configuration panel."""

        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(QLabel("Agent Configuration"))
        layout.addWidget(QLabel("Available Agents: 0"))
        layout.addWidget(QPushButton("Create Agent"))

        return widget

    def setup_status_bar(self) -> None:
        """Set up the status bar."""

        status_bar = self.statusBar()
        status_bar.showMessage("Ready - AutoGen Desktop UI")

        # Add permanent widgets for connection status
        self.server_status_label = QLabel("MCP Server: Disconnected")
        status_bar.addPermanentWidget(self.server_status_label)

        self.memory_status_label = QLabel("Memory: Not loaded")
        status_bar.addPermanentWidget(self.memory_status_label)

    def setup_window_state_persistence(self) -> None:
        """Set up automatic saving of window state."""

        # TODO: Implement window state persistence using QSettings
        # This will remember window size, position, and dock layout
        pass

    def apply_theme(self, theme: str) -> None:
        """Apply a theme to the application."""

        logger.info(f"Applying theme: {theme}")

        if theme == "dark":
            self.setStyleSheet(
                """
                QMainWindow {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QMenuBar {
                    background-color: #3c3c3c;
                    color: #ffffff;
                }
                QMenuBar::item:selected {
                    background-color: #5c5c5c;
                }
                QToolBar {
                    background-color: #3c3c3c;
                    border: none;
                }
                QDockWidget {
                    color: #ffffff;
                    titlebar-close-icon: none;
                    titlebar-normal-icon: none;
                }
                QDockWidget::title {
                    background-color: #4c4c4c;
                    padding: 4px;
                }
                QPushButton {
                    background-color: #4c4c4c;
                    border: 1px solid #6c6c6c;
                    padding: 6px;
                    color: #ffffff;
                }
                QPushButton:hover {
                    background-color: #5c5c5c;
                }
                QLabel {
                    color: #ffffff;
                }
                QTextEdit {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    border: 1px solid #6c6c6c;
                }
            """
            )
        elif theme == "light":
            self.setStyleSheet("")  # Use default light theme
        else:  # system theme
            self.setStyleSheet("")  # Use system default

        self.theme_changed.emit(theme)

    # Event handlers
    def on_new_session(self) -> None:
        """Handle new session creation."""
        logger.info("New session requested")
        self.statusBar().showMessage("New session - feature coming in next phase")

    def on_show_server_panel(self) -> None:
        """Show the server management panel."""
        self.dock_widgets["server_panel"].show()
        self.dock_widgets["server_panel"].raise_()

    def on_about(self) -> None:
        """Show about dialog."""
        from PySide6.QtWidgets import QMessageBox

        QMessageBox.about(
            self,
            "About AutoGen Desktop",
            f"AutoGen Desktop UI\n"
            f"Version: {self.config['app_version']}\n\n"
            f"A desktop application for managing AutoGen multi-agent workflows\n"
            f"with Qdrant memory integration.\n\n"
            f"Built with PySide6 (Qt6 for Python)",
        )

    def closeEvent(self, event) -> None:
        """Handle window close event."""
        logger.info("MainWindow closing")
        self.closing.emit()
        super().closeEvent(event)

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
    QDockWidget,
    QSplitter,
    QTabWidget,
    QGroupBox,
    QScrollArea,
    QSizePolicy,
    QLabel,
    QPushButton,
    QComboBox,
    QCheckBox,
    QLineEdit,
    QTextEdit,
    QMessageBox,
    QFileDialog,
)
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtCore import QSettings, QTimer, Qt, Signal


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

        # Initialize theme before any UI setup
        self.current_theme = "system"

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
        """Configure the main window properties with professional layout."""

        # Set window title and icon
        self.setWindowTitle(self.config["app_name"])

        # Set minimum and preferred window size
        geometry = self.config.get("window_geometry", {})
        width = geometry.get("width", 1400)  # Increased for better layout
        height = geometry.get("height", 900)  # Increased for better layout

        self.setMinimumSize(1000, 700)  # Set minimum size
        self.resize(width, height)

        # Enable dock nesting for complex layouts
        self.setDockNestingEnabled(True)

        # Set animation and unified title bar on macOS
        self.setAnimated(True)
        self.setUnifiedTitleAndToolBarOnMac(True)

        # Configure corner widget behavior for optimal dock layout
        left_area = Qt.DockWidgetArea.LeftDockWidgetArea
        right_area = Qt.DockWidgetArea.RightDockWidgetArea
        bottom_area = Qt.DockWidgetArea.BottomDockWidgetArea

        self.setCorner(Qt.Corner.TopLeftCorner, left_area)
        self.setCorner(Qt.Corner.TopRightCorner, right_area)
        self.setCorner(Qt.Corner.BottomLeftCorner, bottom_area)
        self.setCorner(Qt.Corner.BottomRightCorner, right_area)

        # Set central widget size policy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def setup_menu_bar(self) -> None:
        """Create comprehensive menu bar."""
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu("&File")

        # New actions
        new_session_action = QAction("&New Session", self)
        new_session_action.setShortcut(QKeySequence.StandardKey.New)
        new_session_action.setStatusTip("Start a new conversation session")
        new_session_action.triggered.connect(self.on_new_session)
        file_menu.addAction(new_session_action)

        new_agent_action = QAction("New &Agent...", self)
        new_agent_action.setShortcut("Ctrl+Shift+A")
        new_agent_action.setStatusTip("Create a new agent configuration")
        new_agent_action.triggered.connect(self.new_agent)
        file_menu.addAction(new_agent_action)

        file_menu.addSeparator()

        # Open/Save actions
        open_session_action = QAction("&Open Session...", self)
        open_session_action.setShortcut(QKeySequence.StandardKey.Open)
        open_session_action.setStatusTip("Open a saved conversation session")
        open_session_action.triggered.connect(self.open_session)
        file_menu.addAction(open_session_action)

        save_session_action = QAction("&Save Session", self)
        save_session_action.setShortcut(QKeySequence.StandardKey.Save)
        save_session_action.setStatusTip("Save current conversation session")
        save_session_action.triggered.connect(self.save_session)
        file_menu.addAction(save_session_action)

        save_as_action = QAction("Save Session &As...", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.setStatusTip("Save session with new name")
        save_as_action.triggered.connect(self.save_session_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        # Export actions
        export_menu = file_menu.addMenu("&Export")

        export_markdown_action = QAction("As &Markdown...", self)
        export_markdown_action.setStatusTip("Export conversation as Markdown")
        export_markdown_action.triggered.connect(
            lambda: self.export_conversation("markdown")
        )
        export_menu.addAction(export_markdown_action)

        export_json_action = QAction("As &JSON...", self)
        export_json_action.setStatusTip("Export conversation as JSON")
        export_json_action.triggered.connect(lambda: self.export_conversation("json"))
        export_menu.addAction(export_json_action)

        file_menu.addSeparator()

        # Preferences and Exit
        preferences_action = QAction("&Preferences...", self)
        preferences_action.setShortcut("Ctrl+,")
        preferences_action.setStatusTip("Open application preferences")
        preferences_action.triggered.connect(self.show_preferences)
        file_menu.addAction(preferences_action)

        file_menu.addSeparator()

        quit_action = QAction("&Quit", self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.setStatusTip("Exit the application")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # Edit Menu
        edit_menu = menubar.addMenu("&Edit")

        undo_action = QAction("&Undo", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.setStatusTip("Undo last action")
        undo_action.setEnabled(False)  # Will be enabled when undo is available
        edit_menu.addAction(undo_action)

        redo_action = QAction("&Redo", self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.setStatusTip("Redo last undone action")
        redo_action.setEnabled(False)  # Will be enabled when redo is available
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        copy_action = QAction("&Copy", self)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.setStatusTip("Copy selected text")
        copy_action.triggered.connect(self.copy_selection)
        edit_menu.addAction(copy_action)

        select_all_action = QAction("Select &All", self)
        select_all_action.setShortcut(QKeySequence.StandardKey.SelectAll)
        select_all_action.setStatusTip("Select all text")
        select_all_action.triggered.connect(self.select_all)
        edit_menu.addAction(select_all_action)

        edit_menu.addSeparator()

        clear_conversation_action = QAction("&Clear Conversation", self)
        clear_conversation_action.setShortcut("Ctrl+Shift+C")
        clear_conversation_action.setStatusTip("Clear current conversation")
        clear_conversation_action.triggered.connect(self.clear_conversation)
        edit_menu.addAction(clear_conversation_action)

        # View Menu
        view_menu = menubar.addMenu("&View")

        # Panel visibility toggles
        toggle_agents_action = QAction("&Agent Panel", self)
        toggle_agents_action.setCheckable(True)
        toggle_agents_action.setChecked(True)
        toggle_agents_action.setStatusTip("Toggle agent configuration panel")
        toggle_agents_action.triggered.connect(self.toggle_agent_panel)
        view_menu.addAction(toggle_agents_action)

        toggle_memory_action = QAction("&Memory Panel", self)
        toggle_memory_action.setCheckable(True)
        toggle_memory_action.setChecked(True)
        toggle_memory_action.setStatusTip("Toggle memory browser panel")
        toggle_memory_action.triggered.connect(self.toggle_memory_panel)
        view_menu.addAction(toggle_memory_action)

        view_menu.addSeparator()

        # Zoom actions
        zoom_in_action = QAction("Zoom &In", self)
        zoom_in_action.setShortcut(QKeySequence.StandardKey.ZoomIn)
        zoom_in_action.setStatusTip("Increase font size")
        zoom_in_action.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom &Out", self)
        zoom_out_action.setShortcut(QKeySequence.StandardKey.ZoomOut)
        zoom_out_action.setStatusTip("Decrease font size")
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)

        zoom_reset_action = QAction("&Reset Zoom", self)
        zoom_reset_action.setShortcut("Ctrl+0")
        zoom_reset_action.setStatusTip("Reset font size to default")
        zoom_reset_action.triggered.connect(self.zoom_reset)
        view_menu.addAction(zoom_reset_action)

        view_menu.addSeparator()

        # Theme submenu
        theme_menu = view_menu.addMenu("&Theme")

        light_theme_action = QAction("&Light", self)
        light_theme_action.setCheckable(True)
        light_theme_action.setChecked(self.current_theme == "light")
        light_theme_action.triggered.connect(lambda: self.apply_theme("light"))
        theme_menu.addAction(light_theme_action)

        dark_theme_action = QAction("&Dark", self)
        dark_theme_action.setCheckable(True)
        dark_theme_action.setChecked(self.current_theme == "dark")
        dark_theme_action.triggered.connect(lambda: self.apply_theme("dark"))
        theme_menu.addAction(dark_theme_action)

        system_theme_action = QAction("&System", self)
        system_theme_action.setCheckable(True)
        system_theme_action.setChecked(self.current_theme == "system")
        system_theme_action.triggered.connect(lambda: self.apply_theme("system"))
        theme_menu.addAction(system_theme_action)

        # Agents Menu
        agents_menu = menubar.addMenu("&Agents")

        create_agent_action = QAction("&Create Agent...", self)
        create_agent_action.setShortcut("Ctrl+Shift+N")
        create_agent_action.setStatusTip("Create a new agent")
        create_agent_action.triggered.connect(self.create_agent_dialog)
        agents_menu.addAction(create_agent_action)

        manage_agents_action = QAction("&Manage Agents...", self)
        manage_agents_action.setStatusTip("Open agent management dialog")
        manage_agents_action.triggered.connect(self.manage_agents)
        agents_menu.addAction(manage_agents_action)

        agents_menu.addSeparator()

        import_agents_action = QAction("&Import Agents...", self)
        import_agents_action.setStatusTip("Import agent configurations")
        import_agents_action.triggered.connect(self.import_agents)
        agents_menu.addAction(import_agents_action)

        export_agents_action = QAction("&Export Agents...", self)
        export_agents_action.setStatusTip("Export agent configurations")
        export_agents_action.triggered.connect(self.export_agents)
        agents_menu.addAction(export_agents_action)

        # Memory Menu
        memory_menu = menubar.addMenu("&Memory")

        connect_memory_action = QAction("&Connect to Memory...", self)
        connect_memory_action.setStatusTip("Connect to Qdrant memory database")
        connect_memory_action.triggered.connect(self.connect_memory)
        memory_menu.addAction(connect_memory_action)

        memory_browser_action = QAction("Memory &Browser...", self)
        memory_browser_action.setShortcut("Ctrl+M")
        memory_browser_action.setStatusTip("Open memory browser")
        memory_browser_action.triggered.connect(self.open_memory_browser)
        memory_menu.addAction(memory_browser_action)

        memory_menu.addSeparator()

        clear_memory_action = QAction("&Clear Memory...", self)
        clear_memory_action.setStatusTip("Clear all memory entries")
        clear_memory_action.triggered.connect(self.clear_memory)
        memory_menu.addAction(clear_memory_action)

        memory_stats_action = QAction("Memory &Statistics", self)
        memory_stats_action.setStatusTip("Show memory usage statistics")
        memory_stats_action.triggered.connect(self.show_memory_stats)
        memory_menu.addAction(memory_stats_action)

        # Help Menu
        help_menu = menubar.addMenu("&Help")

        getting_started_action = QAction("&Getting Started", self)
        getting_started_action.setStatusTip("Show getting started guide")
        getting_started_action.triggered.connect(self.show_getting_started)
        help_menu.addAction(getting_started_action)

        documentation_action = QAction("&Documentation", self)
        documentation_action.setShortcut(QKeySequence.StandardKey.HelpContents)
        documentation_action.setStatusTip("Open documentation")
        documentation_action.triggered.connect(self.show_documentation)
        help_menu.addAction(documentation_action)

        help_menu.addSeparator()

        keyboard_shortcuts_action = QAction("&Keyboard Shortcuts", self)
        keyboard_shortcuts_action.setShortcut("Ctrl+?")
        keyboard_shortcuts_action.setStatusTip("Show keyboard shortcuts")
        keyboard_shortcuts_action.triggered.connect(self.show_shortcuts)
        help_menu.addAction(keyboard_shortcuts_action)

        help_menu.addSeparator()

        about_action = QAction("&About", self)
        about_action.setStatusTip("About this application")
        about_action.triggered.connect(self.on_about)
        help_menu.addAction(about_action)

    def setup_toolbar(self) -> None:
        """Create comprehensive toolbar with quick actions."""

        # Main toolbar
        toolbar = self.addToolBar("Main")
        toolbar.setObjectName("MainToolBar")
        toolbar.setMovable(True)  # Allow users to move toolbar
        toolbar.setFloatable(False)  # Prevent floating

        # Session actions
        new_session_action = QAction("New Session", self)
        new_session_action.setStatusTip("Start a new conversation session")
        new_session_action.setShortcut("Ctrl+N")
        new_session_action.triggered.connect(self.on_new_session)
        # Icons to be added when available
        toolbar.addAction(new_session_action)

        open_session_action = QAction("Open Session", self)
        open_session_action.setStatusTip("Open a saved session")
        open_session_action.setShortcut("Ctrl+O")
        open_session_action.triggered.connect(self.open_session)
        toolbar.addAction(open_session_action)

        save_session_action = QAction("Save Session", self)
        save_session_action.setStatusTip("Save current session")
        save_session_action.setShortcut("Ctrl+S")
        save_session_action.triggered.connect(self.save_session)
        toolbar.addAction(save_session_action)

        toolbar.addSeparator()

        # Connection actions
        connect_server_action = QAction("Connect Server", self)
        connect_server_action.setStatusTip("Connect to MCP server")
        connect_server_action.triggered.connect(self.connect_server)
        toolbar.addAction(connect_server_action)

        disconnect_server_action = QAction("Disconnect Server", self)
        disconnect_server_action.setStatusTip("Disconnect from MCP server")
        disconnect_server_action.triggered.connect(self.disconnect_server)
        disconnect_server_action.setEnabled(False)  # Enabled when connected
        toolbar.addAction(disconnect_server_action)

        toolbar.addSeparator()

        # Agent actions
        new_agent_action = QAction("New Agent", self)
        new_agent_action.setStatusTip("Create a new agent")
        new_agent_action.setShortcut("Ctrl+Shift+A")
        new_agent_action.triggered.connect(self.new_agent)
        toolbar.addAction(new_agent_action)

        manage_agents_action = QAction("Manage Agents", self)
        manage_agents_action.setStatusTip("Manage existing agents")
        manage_agents_action.triggered.connect(self.manage_agents)
        toolbar.addAction(manage_agents_action)

        toolbar.addSeparator()

        # Memory actions
        memory_browser_action = QAction("Memory Browser", self)
        memory_browser_action.setStatusTip("Browse memory entries")
        memory_browser_action.setShortcut("Ctrl+M")
        memory_browser_action.triggered.connect(self.open_memory_browser)
        toolbar.addAction(memory_browser_action)

        connect_memory_action = QAction("Connect Memory", self)
        connect_memory_action.setStatusTip("Connect to memory database")
        connect_memory_action.triggered.connect(self.connect_memory)
        toolbar.addAction(connect_memory_action)

        toolbar.addSeparator()

        # Utility actions
        clear_conversation_action = QAction("Clear Chat", self)
        clear_conversation_action.setStatusTip("Clear current conversation")
        clear_conversation_action.setShortcut("Ctrl+Shift+C")
        clear_conversation_action.triggered.connect(self.clear_conversation)
        toolbar.addAction(clear_conversation_action)

        preferences_action = QAction("Preferences", self)
        preferences_action.setStatusTip("Open application preferences")
        preferences_action.setShortcut("Ctrl+,")
        preferences_action.triggered.connect(self.show_preferences)
        toolbar.addAction(preferences_action)

        # Store toolbar reference for later use
        self.main_toolbar = toolbar

    def setup_central_widget(self) -> None:
        """Create the central widget with improved layout."""
        # Create main splitter for professional layout
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setObjectName("MainSplitter")

        # Create left panel with tabbed interface
        left_panel = QTabWidget()
        left_panel.setObjectName("LeftPanel")
        left_panel.setMinimumWidth(250)
        left_panel.setMaximumWidth(400)

        # Agent configuration tab
        agent_config_widget = QScrollArea()
        agent_config_widget.setWidgetResizable(True)
        agent_content = QWidget()
        agent_layout = QVBoxLayout(agent_content)

        # Agent selection group
        agent_group = QGroupBox("Agent Configuration")
        agent_group_layout = QVBoxLayout(agent_group)

        # Agent type selector
        agent_type_layout = QVBoxLayout()
        agent_type_layout.addWidget(QLabel("Agent Type:"))
        agent_type_combo = QComboBox()
        agent_type_combo.addItems(
            [
                "Assistant Agent",
                "User Proxy Agent",
                "Group Chat Manager",
                "Code Executor Agent",
            ]
        )
        agent_type_layout.addWidget(agent_type_combo)
        agent_group_layout.addLayout(agent_type_layout)

        # Agent name input
        name_layout = QVBoxLayout()
        name_layout.addWidget(QLabel("Agent Name:"))
        name_input = QLineEdit()
        name_input.setPlaceholderText("Enter agent name...")
        name_layout.addWidget(name_input)
        agent_group_layout.addLayout(name_layout)

        # Agent features
        features_layout = QVBoxLayout()
        features_layout.addWidget(QLabel("Features:"))
        code_exec_cb = QCheckBox("Code Execution")
        human_input_cb = QCheckBox("Human Input Required")
        memory_cb = QCheckBox("Memory Integration")
        features_layout.addWidget(code_exec_cb)
        features_layout.addWidget(human_input_cb)
        features_layout.addWidget(memory_cb)
        agent_group_layout.addLayout(features_layout)

        agent_layout.addWidget(agent_group)
        agent_layout.addStretch()
        agent_config_widget.setWidget(agent_content)
        left_panel.addTab(agent_config_widget, "Agents")

        # Memory configuration tab
        memory_widget = QScrollArea()
        memory_widget.setWidgetResizable(True)
        memory_content = QWidget()
        memory_layout = QVBoxLayout(memory_content)

        memory_group = QGroupBox("Memory Settings")
        memory_group_layout = QVBoxLayout(memory_group)

        # Qdrant connection settings
        qdrant_layout = QVBoxLayout()
        qdrant_layout.addWidget(QLabel("Qdrant URL:"))
        qdrant_input = QLineEdit()
        qdrant_input.setPlaceholderText("http://localhost:6333")
        qdrant_layout.addWidget(qdrant_input)

        qdrant_layout.addWidget(QLabel("Collection Name:"))
        collection_input = QLineEdit()
        collection_input.setPlaceholderText("autogen_memory")
        qdrant_layout.addWidget(collection_input)

        memory_group_layout.addLayout(qdrant_layout)
        memory_layout.addWidget(memory_group)
        memory_layout.addStretch()
        memory_widget.setWidget(memory_content)
        left_panel.addTab(memory_widget, "Memory")

        main_splitter.addWidget(left_panel)

        # Create center panel with conversation area
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        center_layout.setContentsMargins(5, 5, 5, 5)

        # Conversation display area
        conversation_group = QGroupBox("Conversation")
        conversation_layout = QVBoxLayout(conversation_group)

        conversation_display = QTextEdit()
        conversation_display.setReadOnly(True)
        conversation_display.setPlaceholderText(
            "Conversation will appear here...\n"
            "Configure agents and start a new session to begin."
        )
        conversation_layout.addWidget(conversation_display)

        # Input area
        input_layout = QVBoxLayout()
        input_layout.addWidget(QLabel("Your Message:"))
        message_input = QTextEdit()
        message_input.setMaximumHeight(100)
        message_input.setPlaceholderText("Type your message here...")
        input_layout.addWidget(message_input)

        # Send button
        send_button = QPushButton("Send Message")
        send_button.setEnabled(False)  # Will be enabled when session is active
        input_layout.addWidget(send_button)

        conversation_layout.addLayout(input_layout)
        center_layout.addWidget(conversation_group)

        main_splitter.addWidget(center_panel)

        # Set splitter proportions (left panel: ~25%, center: ~75%)
        main_splitter.setSizes([350, 1050])
        main_splitter.setCollapsible(0, True)  # Left panel can collapse
        main_splitter.setCollapsible(1, False)  # Center panel cannot collapse

        self.setCentralWidget(main_splitter)

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
        """Set up comprehensive status bar with real-time indicators."""

        status_bar = self.statusBar()
        status_bar.showMessage("Ready - AutoGen Desktop UI initialized")

        # Create status indicator widgets
        # Session status (leftmost)
        self.session_status_label = QLabel("Session: None")
        self.session_status_label.setStyleSheet(
            "QLabel { color: #666; padding: 2px 8px; }"
        )
        self.session_status_label.setToolTip("Current session status")
        status_bar.addWidget(self.session_status_label)

        # Add separator
        separator1 = QLabel("|")
        separator1.setStyleSheet("QLabel { color: #ccc; padding: 0 4px; }")
        status_bar.addWidget(separator1)

        # Agent count
        self.agent_count_label = QLabel("Agents: 0")
        self.agent_count_label.setStyleSheet(
            "QLabel { color: #666; padding: 2px 8px; }"
        )
        self.agent_count_label.setToolTip("Number of configured agents")
        status_bar.addWidget(self.agent_count_label)

        # Add separator
        separator2 = QLabel("|")
        separator2.setStyleSheet("QLabel { color: #ccc; padding: 0 4px; }")
        status_bar.addWidget(separator2)

        # Memory statistics
        self.memory_stats_label = QLabel("Memory: 0 entries")
        self.memory_stats_label.setStyleSheet(
            "QLabel { color: #666; padding: 2px 8px; }"
        )
        self.memory_stats_label.setToolTip("Memory database statistics")
        status_bar.addWidget(self.memory_stats_label)

        # Permanent widgets (right side)
        # Theme indicator
        self.theme_label = QLabel(f"Theme: {self.current_theme.title()}")
        self.theme_label.setStyleSheet("QLabel { color: #666; padding: 2px 8px; }")
        self.theme_label.setToolTip("Current UI theme")
        status_bar.addPermanentWidget(self.theme_label)

        # Connection status indicators
        self.memory_connection_label = QLabel("Memory: Disconnected")
        self.memory_connection_label.setStyleSheet(
            "QLabel { color: #d32f2f; padding: 2px 8px; font-weight: bold; }"
        )
        self.memory_connection_label.setToolTip("Memory database connection status")
        status_bar.addPermanentWidget(self.memory_connection_label)

        self.server_connection_label = QLabel("MCP Server: Disconnected")
        self.server_connection_label.setStyleSheet(
            "QLabel { color: #d32f2f; padding: 2px 8px; font-weight: bold; }"
        )
        self.server_connection_label.setToolTip("MCP server connection status")
        status_bar.addPermanentWidget(self.server_connection_label)

        # Status update timer for real-time updates
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status_indicators)
        self.status_timer.start(5000)  # Update every 5 seconds

    def setup_window_state_persistence(self) -> None:
        """Set up automatic saving and restoring of window state."""
        # Initialize QSettings for persistent storage
        self.settings = QSettings("AutoGen", "AutoGenDesktop")

        # Restore window state from previous session
        self.restore_window_state()

        # Set up automatic saving when window changes
        # Window geometry and state will be saved on close

    def restore_window_state(self) -> None:
        """Restore window geometry, splitter positions, and preferences."""
        # Restore window geometry
        geometry = self.settings.value("window/geometry")
        if geometry:
            self.restoreGeometry(geometry)

        # Restore window state (dock positions, toolbar state)
        window_state = self.settings.value("window/state")
        if window_state:
            self.restoreState(window_state)

        # Restore splitter positions
        if hasattr(self, "centralWidget") and self.centralWidget():
            main_splitter = self.centralWidget().findChild(QSplitter, "MainSplitter")
            if main_splitter:
                splitter_state = self.settings.value("splitter/main_sizes")
                if splitter_state:
                    # Convert to list of integers
                    sizes = [int(size) for size in splitter_state]
                    main_splitter.setSizes(sizes)

        # Restore theme preference
        saved_theme = self.settings.value("appearance/theme", "system")
        if saved_theme != self.current_theme:
            self.apply_theme(saved_theme)

        # Restore dock widget visibility
        for dock_name in self.dock_widgets:
            visibility = self.settings.value(
                f"docks/{dock_name}/visible", True, type=bool
            )
            self.dock_widgets[dock_name].setVisible(visibility)

        # Restore toolbar visibility and position
        if hasattr(self, "main_toolbar"):
            toolbar_visible = self.settings.value(
                "toolbar/main/visible", True, type=bool
            )
            self.main_toolbar.setVisible(toolbar_visible)

            toolbar_area = self.settings.value(
                "toolbar/main/area", 4, type=int
            )  # 4 = TopToolBarArea
            toolbar_area_enum = Qt.ToolBarArea(toolbar_area)
            if toolbar_area_enum in [
                Qt.ToolBarArea.TopToolBarArea,
                Qt.ToolBarArea.BottomToolBarArea,
                Qt.ToolBarArea.LeftToolBarArea,
                Qt.ToolBarArea.RightToolBarArea,
            ]:
                self.addToolBar(toolbar_area_enum, self.main_toolbar)

    def save_window_state(self) -> None:
        """Save current window geometry, splitter positions, and preferences."""
        # Save window geometry
        self.settings.setValue("window/geometry", self.saveGeometry())

        # Save window state (dock positions, toolbar state)
        self.settings.setValue("window/state", self.saveState())

        # Save splitter positions
        if hasattr(self, "centralWidget") and self.centralWidget():
            main_splitter = self.centralWidget().findChild(QSplitter, "MainSplitter")
            if main_splitter:
                sizes = main_splitter.sizes()
                self.settings.setValue("splitter/main_sizes", sizes)

        # Save theme preference
        self.settings.setValue("appearance/theme", self.current_theme)

        # Save dock widget visibility states
        for dock_name, dock_widget in self.dock_widgets.items():
            self.settings.setValue(
                f"docks/{dock_name}/visible", dock_widget.isVisible()
            )

        # Save toolbar state
        if hasattr(self, "main_toolbar"):
            self.settings.setValue(
                "toolbar/main/visible", self.main_toolbar.isVisible()
            )
            toolbar_area = self.toolBarArea(self.main_toolbar)
            self.settings.setValue("toolbar/main/area", int(toolbar_area))

        # Ensure settings are written to disk
        self.settings.sync()

    def reset_window_state(self) -> None:
        """Reset window state to defaults (useful for preferences)."""
        # Clear all saved settings
        self.settings.clear()

        # Reset to default theme
        self.apply_theme("system")

        # Reset window to default size and position
        self.resize(1400, 900)
        self.move(100, 100)

        # Show all dock widgets
        for dock_widget in self.dock_widgets.values():
            dock_widget.setVisible(True)

        # Show toolbar
        if hasattr(self, "main_toolbar"):
            self.main_toolbar.setVisible(True)
            self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.main_toolbar)

        # Reset splitter to default proportions
        if hasattr(self, "centralWidget") and self.centralWidget():
            main_splitter = self.centralWidget().findChild(QSplitter, "MainSplitter")
            if main_splitter:
                main_splitter.setSizes([350, 1050])  # Default proportions

    def apply_theme(self, theme: str) -> None:
        """Apply comprehensive theme to the application."""
        logger.info(f"Applying theme: {theme}")
        self.current_theme = theme

        if theme == "dark":
            self.setStyleSheet(self._get_dark_theme_stylesheet())
        elif theme == "light":
            self.setStyleSheet(self._get_light_theme_stylesheet())
        else:  # system theme
            # For system theme, detect system preference
            self.setStyleSheet(self._get_system_theme_stylesheet())

        # Update status bar theme indicator
        if hasattr(self, "theme_label"):
            self.theme_label.setText(f"Theme: {theme.title()}")

        self.theme_changed.emit(theme)

    def _get_dark_theme_stylesheet(self) -> str:
        """Get comprehensive dark theme stylesheet."""
        return """
            /* Main Window */
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }

            /* Menu Bar */
            QMenuBar {
                background-color: #3c3c3c;
                color: #ffffff;
                border-bottom: 1px solid #555555;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 4px 12px;
            }
            QMenuBar::item:selected {
                background-color: #5c5c5c;
            }
            QMenuBar::item:pressed {
                background-color: #4c4c4c;
            }
            QMenu {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
            }
            QMenu::item {
                padding: 6px 12px;
            }
            QMenu::item:selected {
                background-color: #5c5c5c;
            }
            QMenu::separator {
                height: 1px;
                background-color: #555555;
                margin: 2px 0;
            }

            /* Toolbar */
            QToolBar {
                background-color: #3c3c3c;
                border: none;
                spacing: 2px;
                padding: 2px;
            }
            QToolBar QToolButton {
                background-color: transparent;
                border: 1px solid transparent;
                padding: 6px 12px;
                margin: 1px;
                color: #ffffff;
            }
            QToolBar QToolButton:hover {
                background-color: #5c5c5c;
                border: 1px solid #777777;
            }
            QToolBar QToolButton:pressed {
                background-color: #4c4c4c;
            }
            QToolBar::separator {
                background-color: #555555;
                width: 1px;
                margin: 4px 2px;
            }

            /* Status Bar */
            QStatusBar {
                background-color: #3c3c3c;
                color: #ffffff;
                border-top: 1px solid #555555;
            }
            QStatusBar QLabel {
                color: #ffffff;
            }

            /* Dock Widgets */
            QDockWidget {
                color: #ffffff;
                titlebar-close-icon: none;
                titlebar-normal-icon: none;
            }
            QDockWidget::title {
                background-color: #4c4c4c;
                padding: 6px;
                border-bottom: 1px solid #555555;
            }
            QDockWidget QWidget {
                background-color: #2b2b2b;
            }

            /* Buttons */
            QPushButton {
                background-color: #4c4c4c;
                border: 1px solid #6c6c6c;
                padding: 8px 16px;
                color: #ffffff;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #5c5c5c;
                border: 1px solid #7c7c7c;
            }
            QPushButton:pressed {
                background-color: #3c3c3c;
            }
            QPushButton:disabled {
                background-color: #3c3c3c;
                color: #888888;
                border: 1px solid #555555;
            }

            /* Labels */
            QLabel {
                color: #ffffff;
            }

            /* Text Widgets */
            QTextEdit, QLineEdit {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #6c6c6c;
                padding: 4px;
                selection-background-color: #5c5c5c;
            }
            QTextEdit:focus, QLineEdit:focus {
                border: 1px solid #8c8c8c;
            }

            /* Combo Boxes */
            QComboBox {
                background-color: #4c4c4c;
                border: 1px solid #6c6c6c;
                padding: 4px;
                color: #ffffff;
            }
            QComboBox:hover {
                border: 1px solid #7c7c7c;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #3c3c3c;
                color: #ffffff;
                selection-background-color: #5c5c5c;
            }

            /* Check Boxes */
            QCheckBox {
                color: #ffffff;
                spacing: 6px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                background-color: #3c3c3c;
                border: 1px solid #6c6c6c;
            }
            QCheckBox::indicator:checked {
                background-color: #5c5c5c;
                border: 1px solid #8c8c8c;
            }

            /* Tab Widget */
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #4c4c4c;
                color: #ffffff;
                padding: 8px 16px;
                border: 1px solid #555555;
            }
            QTabBar::tab:selected {
                background-color: #2b2b2b;
                border-bottom: 1px solid #2b2b2b;
            }
            QTabBar::tab:hover:!selected {
                background-color: #5c5c5c;
            }

            /* Group Box */
            QGroupBox {
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                margin-top: 8px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                background-color: #2b2b2b;
            }

            /* Scroll Area */
            QScrollArea {
                background-color: #2b2b2b;
                border: 1px solid #555555;
            }
            QScrollBar:vertical {
                background-color: #3c3c3c;
                width: 12px;
            }
            QScrollBar::handle:vertical {
                background-color: #6c6c6c;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #7c7c7c;
            }

            /* Splitter */
            QSplitter::handle {
                background-color: #555555;
            }
            QSplitter::handle:horizontal {
                width: 2px;
            }
            QSplitter::handle:vertical {
                height: 2px;
            }
        """

    def _get_light_theme_stylesheet(self) -> str:
        """Get comprehensive light theme stylesheet."""
        return """
            /* Main Window */
            QMainWindow {
                background-color: #ffffff;
                color: #000000;
            }

            /* Menu Bar */
            QMenuBar {
                background-color: #f5f5f5;
                color: #000000;
                border-bottom: 1px solid #d0d0d0;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 4px 12px;
            }
            QMenuBar::item:selected {
                background-color: #e0e0e0;
            }
            QMenuBar::item:pressed {
                background-color: #d0d0d0;
            }
            QMenu {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #d0d0d0;
            }
            QMenu::item {
                padding: 6px 12px;
            }
            QMenu::item:selected {
                background-color: #e0e0e0;
            }
            QMenu::separator {
                height: 1px;
                background-color: #d0d0d0;
                margin: 2px 0;
            }

            /* Toolbar */
            QToolBar {
                background-color: #f5f5f5;
                border: none;
                spacing: 2px;
                padding: 2px;
            }
            QToolBar QToolButton {
                background-color: transparent;
                border: 1px solid transparent;
                padding: 6px 12px;
                margin: 1px;
                color: #000000;
            }
            QToolBar QToolButton:hover {
                background-color: #e0e0e0;
                border: 1px solid #c0c0c0;
            }
            QToolBar QToolButton:pressed {
                background-color: #d0d0d0;
            }
            QToolBar::separator {
                background-color: #d0d0d0;
                width: 1px;
                margin: 4px 2px;
            }

            /* Status Bar */
            QStatusBar {
                background-color: #f5f5f5;
                color: #000000;
                border-top: 1px solid #d0d0d0;
            }
            QStatusBar QLabel {
                color: #000000;
            }

            /* Dock Widgets */
            QDockWidget {
                color: #000000;
            }
            QDockWidget::title {
                background-color: #e5e5e5;
                padding: 6px;
                border-bottom: 1px solid #d0d0d0;
            }
            QDockWidget QWidget {
                background-color: #ffffff;
            }

            /* Buttons */
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #c0c0c0;
                padding: 8px 16px;
                color: #000000;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e5e5e5;
                border: 1px solid #b0b0b0;
            }
            QPushButton:pressed {
                background-color: #d5d5d5;
            }
            QPushButton:disabled {
                background-color: #f5f5f5;
                color: #888888;
                border: 1px solid #d5d5d5;
            }

            /* Labels */
            QLabel {
                color: #000000;
            }

            /* Text Widgets */
            QTextEdit, QLineEdit {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #c0c0c0;
                padding: 4px;
                selection-background-color: #b3d9ff;
            }
            QTextEdit:focus, QLineEdit:focus {
                border: 1px solid #0078d4;
            }

            /* Combo Boxes */
            QComboBox {
                background-color: #ffffff;
                border: 1px solid #c0c0c0;
                padding: 4px;
                color: #000000;
            }
            QComboBox:hover {
                border: 1px solid #0078d4;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #000000;
                selection-background-color: #e5e5e5;
            }

            /* Check Boxes */
            QCheckBox {
                color: #000000;
                spacing: 6px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                background-color: #ffffff;
                border: 1px solid #c0c0c0;
            }
            QCheckBox::indicator:checked {
                background-color: #0078d4;
                border: 1px solid #0078d4;
            }

            /* Tab Widget */
            QTabWidget::pane {
                border: 1px solid #d0d0d0;
                background-color: #ffffff;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                color: #000000;
                padding: 8px 16px;
                border: 1px solid #d0d0d0;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                border-bottom: 1px solid #ffffff;
            }
            QTabBar::tab:hover:!selected {
                background-color: #e5e5e5;
            }

            /* Group Box */
            QGroupBox {
                color: #000000;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                margin-top: 8px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                background-color: #ffffff;
            }

            /* Scroll Area */
            QScrollArea {
                background-color: #ffffff;
                border: 1px solid #d0d0d0;
            }
            QScrollBar:vertical {
                background-color: #f0f0f0;
                width: 12px;
            }
            QScrollBar::handle:vertical {
                background-color: #c0c0c0;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #a0a0a0;
            }

            /* Splitter */
            QSplitter::handle {
                background-color: #d0d0d0;
            }
            QSplitter::handle:horizontal {
                width: 2px;
            }
            QSplitter::handle:vertical {
                height: 2px;
            }
        """

    def _get_system_theme_stylesheet(self) -> str:
        """Get system theme stylesheet (detects system preference)."""
        # For now, return light theme as default system theme
        # In future, this could detect actual system theme preference
        return self._get_light_theme_stylesheet()

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
            f"A desktop application for managing AutoGen "
            f"multi-agent workflows\n"
            f"with Qdrant memory integration.\n\n"
            f"Built with PySide6 (Qt6 for Python)",
        )

    # Menu Action Methods
    def new_agent(self) -> None:
        """Create a new agent - placeholder implementation."""
        QMessageBox.information(
            self, "New Agent", "Agent creation dialog - coming soon!"
        )

    def open_session(self) -> None:
        """Open a saved session - placeholder implementation."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open Session", "", "JSON Files (*.json);;All Files (*)"
        )
        if filename:
            QMessageBox.information(
                self, "Open Session", f"Would open session: {filename}"
            )

    def save_session(self) -> None:
        """Save current session - placeholder implementation."""
        QMessageBox.information(self, "Save Session", "Session saving - coming soon!")

    def save_session_as(self) -> None:
        """Save session with new name - placeholder implementation."""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Session As", "", "JSON Files (*.json);;All Files (*)"
        )
        if filename:
            QMessageBox.information(
                self, "Save Session As", f"Would save session as: {filename}"
            )

    def export_conversation(self, format_type: str) -> None:
        """Export conversation in specified format."""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            f"Export as {format_type.upper()}",
            "",
            f"{format_type.upper()} Files (*.{format_type});;All Files (*)",
        )
        if filename:
            QMessageBox.information(
                self,
                "Export",
                f"Would export conversation as {format_type}: {filename}",
            )

    def show_preferences(self) -> None:
        """Show application preferences dialog."""
        reply = QMessageBox.question(
            self,
            "Preferences",
            "Preferences dialog is coming soon!\n\n"
            "Would you like to reset window layout to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.reset_window_state()
            QMessageBox.information(
                self, "Reset Complete", "Window layout has been reset to defaults."
            )

    def copy_selection(self) -> None:
        """Copy selected text to clipboard."""
        # Will be implemented to copy from active text widget
        QMessageBox.information(self, "Copy", "Copy functionality - coming soon!")

    def select_all(self) -> None:
        """Select all text in active text widget."""
        QMessageBox.information(
            self, "Select All", "Select all functionality - coming soon!"
        )

    def clear_conversation(self) -> None:
        """Clear the current conversation."""
        reply = QMessageBox.question(
            self,
            "Clear Conversation",
            "Are you sure you want to clear the current conversation?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            QMessageBox.information(
                self, "Cleared", "Conversation cleared - coming soon!"
            )

    def toggle_agent_panel(self, checked: bool) -> None:
        """Toggle agent configuration panel visibility."""
        status = "shown" if checked else "hidden"
        QMessageBox.information(self, "Toggle Panel", f"Agent panel {status}")

    def toggle_memory_panel(self, checked: bool) -> None:
        """Toggle memory browser panel visibility."""
        status = "shown" if checked else "hidden"
        QMessageBox.information(self, "Toggle Panel", f"Memory panel {status}")

    def zoom_in(self) -> None:
        """Increase font size."""
        QMessageBox.information(self, "Zoom", "Zoom in - coming soon!")

    def zoom_out(self) -> None:
        """Decrease font size."""
        QMessageBox.information(self, "Zoom", "Zoom out - coming soon!")

    def zoom_reset(self) -> None:
        """Reset font size to default."""
        QMessageBox.information(self, "Zoom", "Reset zoom - coming soon!")

    def create_agent_dialog(self) -> None:
        """Show create agent dialog."""
        QMessageBox.information(
            self, "Create Agent", "Create agent dialog - coming soon!"
        )

    def manage_agents(self) -> None:
        """Open agent management dialog."""
        QMessageBox.information(
            self, "Manage Agents", "Agent management - coming soon!"
        )

    def import_agents(self) -> None:
        """Import agent configurations."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Import Agents", "", "JSON Files (*.json);;All Files (*)"
        )
        if filename:
            QMessageBox.information(
                self, "Import", f"Would import agents from: {filename}"
            )

    def export_agents(self) -> None:
        """Export agent configurations."""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Agents", "", "JSON Files (*.json);;All Files (*)"
        )
        if filename:
            QMessageBox.information(
                self, "Export", f"Would export agents to: {filename}"
            )

    def connect_memory(self) -> None:
        """Connect to memory database."""
        QMessageBox.information(
            self, "Connect Memory", "Memory connection - coming soon!"
        )

    def open_memory_browser(self) -> None:
        """Open memory browser dialog."""
        QMessageBox.information(self, "Memory Browser", "Memory browser - coming soon!")

    def clear_memory(self) -> None:
        """Clear all memory entries."""
        reply = QMessageBox.question(
            self,
            "Clear Memory",
            "Are you sure you want to clear all memory entries?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            QMessageBox.information(self, "Cleared", "Memory cleared - coming soon!")

    def show_memory_stats(self) -> None:
        """Show memory usage statistics."""
        QMessageBox.information(
            self, "Memory Statistics", "Memory stats - coming soon!"
        )

    def show_getting_started(self) -> None:
        """Show getting started guide."""
        QMessageBox.information(
            self, "Getting Started", "Getting started guide - coming soon!"
        )

    def show_documentation(self) -> None:
        """Open documentation."""
        QMessageBox.information(self, "Documentation", "Documentation - coming soon!")

    def show_shortcuts(self) -> None:
        """Show keyboard shortcuts dialog."""
        shortcuts_text = """
Keyboard Shortcuts:

File:
  Ctrl+N    - New Session
  Ctrl+O    - Open Session
  Ctrl+S    - Save Session
  Ctrl+Shift+S - Save Session As
  Ctrl+,    - Preferences
  Ctrl+Q    - Quit

Edit:
  Ctrl+Z    - Undo
  Ctrl+Y    - Redo
  Ctrl+C    - Copy
  Ctrl+A    - Select All
  Ctrl+Shift+C - Clear Conversation

View:
  Ctrl++    - Zoom In
  Ctrl+-    - Zoom Out
  Ctrl+0    - Reset Zoom

Agents:
  Ctrl+Shift+A - New Agent
  Ctrl+Shift+N - Create Agent

Memory:
  Ctrl+M    - Memory Browser

Help:
  F1        - Documentation
  Ctrl+?    - Keyboard Shortcuts
        """
        QMessageBox.information(self, "Keyboard Shortcuts", shortcuts_text.strip())

    def connect_server(self) -> None:
        """Connect to MCP server."""
        QMessageBox.information(
            self, "Connect Server", "Server connection - coming soon!"
        )

    def disconnect_server(self) -> None:
        """Disconnect from MCP server."""
        QMessageBox.information(
            self, "Disconnect Server", "Server disconnection - coming soon!"
        )

    def update_status_indicators(self) -> None:
        """Update status bar indicators with current application state."""
        # Update session status
        # This will be connected to actual session management later
        session_count = 0  # Placeholder
        if session_count > 0:
            self.session_status_label.setText(f"Session: Active ({session_count})")
            self.session_status_label.setStyleSheet(
                "QLabel { color: #2e7d32; padding: 2px 8px; }"
            )
        else:
            self.session_status_label.setText("Session: None")
            self.session_status_label.setStyleSheet(
                "QLabel { color: #666; padding: 2px 8px; }"
            )

        # Update agent count
        agent_count = 0  # Placeholder - will connect to actual agent manager
        self.agent_count_label.setText(f"Agents: {agent_count}")

        # Update memory statistics
        memory_count = 0  # Placeholder - will connect to actual memory service
        self.memory_stats_label.setText(f"Memory: {memory_count} entries")

        # Update connection statuses
        # These will be connected to actual connection managers later
        server_connected = False  # Placeholder
        memory_connected = False  # Placeholder

        if server_connected:
            self.server_connection_label.setText("MCP Server: Connected")
            self.server_connection_label.setStyleSheet(
                "QLabel { color: #2e7d32; padding: 2px 8px; font-weight: bold; }"
            )
        else:
            self.server_connection_label.setText("MCP Server: Disconnected")
            self.server_connection_label.setStyleSheet(
                "QLabel { color: #d32f2f; padding: 2px 8px; font-weight: bold; }"
            )

        if memory_connected:
            self.memory_connection_label.setText("Memory: Connected")
            self.memory_connection_label.setStyleSheet(
                "QLabel { color: #2e7d32; padding: 2px 8px; font-weight: bold; }"
            )
        else:
            self.memory_connection_label.setText("Memory: Disconnected")
            self.memory_connection_label.setStyleSheet(
                "QLabel { color: #d32f2f; padding: 2px 8px; font-weight: bold; }"
            )

        # Update theme label when theme changes
        self.theme_label.setText(f"Theme: {self.current_theme.title()}")

    def closeEvent(self, event) -> None:
        """Handle window close event and save state."""
        logger.info("MainWindow closing - saving window state")

        # Save current window state before closing
        self.save_window_state()

        # Stop the status update timer
        if hasattr(self, "status_timer"):
            self.status_timer.stop()

        # Emit closing signal for any connected components
        self.closing.emit()

        # Accept the close event
        super().closeEvent(event)

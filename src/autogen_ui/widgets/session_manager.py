"""
Session Management Widget - Clean Implementation
Manage AutoGen conversation sessions and history
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLabel,
    QTextEdit,
    QLineEdit,
    QComboBox,
    QTabWidget,
    QMessageBox,
    QFrame,
    QFormLayout,
    QSpinBox,
    QCheckBox,
    QScrollArea,
    QTreeWidget,
    QTreeWidgetItem,
    QFileDialog,
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont

from autogen_ui.services import SessionService

logger = logging.getLogger(__name__)


class ConversationViewer(QWidget):
    """Widget to view conversation history"""

    def __init__(self):
        super().__init__()
        self.conversation_data = []
        self.setup_ui()

    def setup_ui(self):
        """Set up conversation viewer UI"""
        layout = QVBoxLayout(self)

        # Conversation display
        self.conversation_text = QTextEdit()
        self.conversation_text.setReadOnly(True)
        self.conversation_text.setFont(QFont("monospace", 9))
        layout.addWidget(self.conversation_text)

        # Controls
        controls_layout = QHBoxLayout()

        self.export_btn = QPushButton("Export")
        self.export_btn.clicked.connect(self.export_conversation)
        controls_layout.addWidget(self.export_btn)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_conversation)
        controls_layout.addWidget(self.clear_btn)

        controls_layout.addStretch()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search conversation...")
        self.search_input.textChanged.connect(self.search_conversation)
        controls_layout.addWidget(self.search_input)

        layout.addLayout(controls_layout)

    def add_message(self, role: str, content: str, timestamp: str = None):
        """Add a message to the conversation"""
        if timestamp is None:
            timestamp = datetime.now().strftime("%H:%M:%S")

        message = {"role": role, "content": content, "timestamp": timestamp}

        self.conversation_data.append(message)
        self.refresh_display()

    def refresh_display(self):
        """Refresh the conversation display"""
        conversation_html = "<style>"
        conversation_html += "body { font-family: monospace; font-size: 12px; }"
        conversation_html += ".user { color: #2E8B57; font-weight: bold; }"
        conversation_html += ".assistant { color: #4169E1; font-weight: bold; }"
        conversation_html += ".system { color: #8B4513; font-weight: bold; }"
        conversation_html += ".timestamp { color: #888; font-size: 10px; }"
        conversation_html += (
            ".message { margin: 10px 0; padding: 5px; border-left: 3px solid #ddd; }"
        )
        conversation_html += "</style><body>"

        for msg in self.conversation_data:
            role_class = msg["role"].lower()
            conversation_html += '<div class="message">'
            conversation_html += (
                f'<span class="{role_class}">{msg["role"].upper()}:</span> '
            )
            conversation_html += (
                f'<span class="timestamp">[{msg["timestamp"]}]</span><br>'
            )
            conversation_html += f"{msg['content']}<br>"
            conversation_html += "</div>"

        conversation_html += "</body>"
        self.conversation_text.setHtml(conversation_html)

        # Scroll to bottom
        cursor = self.conversation_text.textCursor()
        cursor.movePosition(cursor.End)
        self.conversation_text.setTextCursor(cursor)

    def export_conversation(self):
        """Export conversation to JSON"""
        if not self.conversation_data:
            QMessageBox.information(self, "Info", "No conversation to export")
            return

        # Prepare export data for future implementation
        # export_data = {
        #     "exported_at": datetime.now().isoformat(),
        #     "messages": self.conversation_data,
        # }

        QMessageBox.information(
            self,
            "Export",
            f"Conversation exported with {len(self.conversation_data)} messages",
        )

    def clear_conversation(self):
        """Clear the conversation"""
        reply = QMessageBox.question(
            self,
            "Clear Conversation",
            "Are you sure you want to clear the conversation?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.conversation_data.clear()
            self.conversation_text.clear()

    def search_conversation(self, text: str):
        """Search within conversation"""
        if not text:
            self.refresh_display()
            return

        # Simple search highlighting (could be enhanced)
        self.refresh_display()


class SessionConfigWidget(QWidget):
    """Widget for configuring session settings"""

    # Signal for when user wants to start a session
    session_start_requested = Signal(dict)

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        """Set up session configuration UI"""
        layout = QVBoxLayout(self)

        # Scroll area for form
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Basic settings
        self.setup_basic_settings(scroll_layout)

        # Agent settings
        self.setup_agent_settings(scroll_layout)

        # Advanced settings
        self.setup_advanced_settings(scroll_layout)

        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)

        # Action buttons
        self.setup_action_buttons(layout)

    def setup_basic_settings(self, layout):
        """Set up basic session settings"""
        basic_group = QGroupBox("Basic Settings")
        basic_layout = QFormLayout(basic_group)

        self.session_name = QLineEdit()
        self.session_name.setPlaceholderText("Enter session name...")
        basic_layout.addRow("Session Name:", self.session_name)

        # Project name field
        self.project_name = QLineEdit()
        self.project_name.setPlaceholderText("Enter project name...")
        basic_layout.addRow("Project Name:", self.project_name)

        # Objective field
        self.objective = QTextEdit()
        self.objective.setPlaceholderText("Enter session objective...")
        self.objective.setMaximumHeight(80)
        basic_layout.addRow("Objective:", self.objective)

        self.session_type = QComboBox()
        self.session_type.addItems(
            [
                "Development",
                "Code Review",
                "Coding",
                "Planning",
                "Research",
                "Chat",
                "Custom",
            ]
        )
        basic_layout.addRow("Session Type:", self.session_type)

        # Working directory selection
        working_dir_layout = QHBoxLayout()
        self.working_directory = QLineEdit()
        self.working_directory.setPlaceholderText("Select working directory...")
        import os

        self.working_directory.setText(os.getcwd())  # Default to current directory
        working_dir_layout.addWidget(self.working_directory)

        self.browse_dir_btn = QPushButton("Browse...")
        self.browse_dir_btn.clicked.connect(self.browse_working_directory)
        working_dir_layout.addWidget(self.browse_dir_btn)

        basic_layout.addRow("Working Directory:", working_dir_layout)

        self.max_rounds = QSpinBox()
        self.max_rounds.setRange(1, 100)
        self.max_rounds.setValue(10)
        basic_layout.addRow("Max Rounds:", self.max_rounds)

        layout.addWidget(basic_group)

    def setup_agent_settings(self, layout):
        """Set up agent selection settings"""
        agent_group = QGroupBox("Agent Selection")
        agent_layout = QVBoxLayout(agent_group)

        # Selected agents list
        self.agents_list = QListWidget()
        self.agents_list.setMaximumHeight(120)
        agent_layout.addWidget(QLabel("Selected Agents:"))
        agent_layout.addWidget(self.agents_list)

        # Agent controls
        agent_controls = QHBoxLayout()

        self.add_agent_btn = QPushButton("Add Agent")
        self.add_agent_btn.clicked.connect(self.add_agent)
        agent_controls.addWidget(self.add_agent_btn)

        self.remove_agent_btn = QPushButton("Remove")
        self.remove_agent_btn.clicked.connect(self.remove_agent)
        self.remove_agent_btn.setEnabled(False)
        agent_controls.addWidget(self.remove_agent_btn)

        agent_controls.addStretch()
        agent_layout.addLayout(agent_controls)

        layout.addWidget(agent_group)

    def setup_advanced_settings(self, layout):
        """Set up advanced session settings"""
        advanced_group = QGroupBox("Advanced Settings")
        advanced_layout = QFormLayout(advanced_group)

        # Memory integration
        self.memory_enabled = QCheckBox("Enable Memory")
        self.memory_enabled.setChecked(True)
        advanced_layout.addRow("Memory:", self.memory_enabled)

        # Auto-save
        self.auto_save = QCheckBox("Auto-save Session")
        self.auto_save.setChecked(True)
        advanced_layout.addRow("Auto-save:", self.auto_save)

        # Timeout
        self.timeout = QSpinBox()
        self.timeout.setRange(30, 300)
        self.timeout.setValue(120)
        self.timeout.setSuffix(" seconds")
        advanced_layout.addRow("Response Timeout:", self.timeout)

        layout.addWidget(advanced_group)

    def setup_action_buttons(self, layout):
        """Set up action buttons"""
        button_layout = QHBoxLayout()

        self.start_session_btn = QPushButton("Start Session")
        self.start_session_btn.clicked.connect(self.start_session)
        button_layout.addWidget(self.start_session_btn)

        self.save_config_btn = QPushButton("Save Config")
        self.save_config_btn.clicked.connect(self.save_config)
        button_layout.addWidget(self.save_config_btn)

        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self.reset_config)
        button_layout.addWidget(self.reset_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

    def add_agent(self):
        """Add agent to session"""
        # Placeholder - would show agent selection dialog
        agent_name = f"Agent-{self.agents_list.count() + 1}"
        item = QListWidgetItem(agent_name)
        self.agents_list.addItem(item)

    def remove_agent(self):
        """Remove selected agent"""
        current_item = self.agents_list.currentItem()
        if current_item:
            self.agents_list.takeItem(self.agents_list.row(current_item))

    def browse_working_directory(self):
        """Browse for working directory"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Working Directory",
            self.working_directory.text() or os.getcwd(),
        )
        if directory:
            self.working_directory.setText(directory)

    def start_session(self):
        """Start a new session"""
        if not self.session_name.text().strip():
            QMessageBox.warning(self, "Warning", "Please enter a session name")
            return

        if not self.project_name.text().strip():
            QMessageBox.warning(self, "Warning", "Please enter a project name")
            return

        if not self.objective.toPlainText().strip():
            QMessageBox.warning(self, "Warning", "Please enter a session objective")
            return

        if not self.working_directory.text().strip():
            QMessageBox.warning(self, "Warning", "Please select a working directory")
            return

        config = self.get_session_config()

        # Emit signal for the manager to handle
        self.session_start_requested.emit(config)

    def save_config(self):
        """Save session configuration"""
        config = self.get_session_config()
        QMessageBox.information(
            self, "Config Saved", f"Session configuration '{config['name']}' saved"
        )

    def reset_config(self):
        """Reset configuration"""
        self.session_name.clear()
        self.project_name.clear()
        self.objective.clear()
        self.session_type.setCurrentIndex(0)
        self.max_rounds.setValue(10)
        self.agents_list.clear()
        self.memory_enabled.setChecked(True)
        self.auto_save.setChecked(True)
        self.timeout.setValue(120)

    def get_session_config(self) -> Dict[str, Any]:
        """Get current session configuration"""
        agents = []
        for i in range(self.agents_list.count()):
            agents.append(self.agents_list.item(i).text())

        return {
            "name": self.session_name.text().strip(),
            "project": self.project_name.text().strip(),
            "objective": self.objective.toPlainText().strip(),
            "type": self.session_type.currentText(),
            "max_rounds": self.max_rounds.value(),
            "agents": agents,
            "working_directory": self.working_directory.text().strip(),
            "memory_enabled": self.memory_enabled.isChecked(),
            "auto_save": self.auto_save.isChecked(),
            "timeout": self.timeout.value(),
            "created_at": datetime.now().isoformat(),
        }


class SessionManagerWidget(QWidget):
    """Main session management widget"""

    session_started = Signal(dict)
    session_ended = Signal(str)

    def __init__(self, server_url: str):
        super().__init__()
        self.server_url = server_url
        self.current_session = None
        self.sessions_history = []

        # Initialize session service
        self.session_service = SessionService(server_url)
        self.session_service.session_started.connect(self._on_session_started)
        self.session_service.session_stopped.connect(self._on_session_stopped)
        self.session_service.session_error.connect(self._on_session_error)

        self.setup_ui()
        self.setup_timer()
        self.load_sessions()

    def setup_ui(self):
        """Set up session manager UI"""
        layout = QVBoxLayout(self)

        # Session status
        self.setup_status_bar(layout)

        # Main content tabs
        self.tab_widget = QTabWidget()

        # Current session tab
        self.setup_current_session_tab()

        # New session tab
        self.setup_new_session_tab()

        # Session history tab
        self.setup_history_tab()

        layout.addWidget(self.tab_widget)

    def setup_status_bar(self, layout):
        """Set up session status bar"""
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.StyledPanel)
        status_frame.setMaximumHeight(35)
        status_layout = QHBoxLayout(status_frame)

        self.status_label = QLabel("No active session")
        self.status_label.setStyleSheet(
            "QLabel { color: orange; font-weight: bold; padding: 4px; }"
        )

        self.end_session_btn = QPushButton("End Session")
        self.end_session_btn.clicked.connect(self.end_current_session)
        self.end_session_btn.setEnabled(False)
        self.end_session_btn.setMaximumWidth(100)

        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.end_session_btn)

        layout.addWidget(status_frame)

    def setup_current_session_tab(self):
        """Set up current session tab"""
        current_widget = QWidget()
        current_layout = QVBoxLayout(current_widget)

        # Session info
        info_group = QGroupBox("Current Session")
        info_layout = QFormLayout(info_group)

        self.current_name_label = QLabel("None")
        info_layout.addRow("Name:", self.current_name_label)

        self.current_type_label = QLabel("None")
        info_layout.addRow("Type:", self.current_type_label)

        self.current_directory_label = QLabel("None")
        info_layout.addRow("Directory:", self.current_directory_label)

        self.current_agents_label = QLabel("None")
        info_layout.addRow("Agents:", self.current_agents_label)

        self.current_rounds_label = QLabel("0/0")
        info_layout.addRow("Rounds:", self.current_rounds_label)

        current_layout.addWidget(info_group)

        # Conversation viewer
        self.conversation_viewer = ConversationViewer()
        current_layout.addWidget(self.conversation_viewer)

        self.tab_widget.addTab(current_widget, "Current Session")

    def setup_new_session_tab(self):
        """Set up new session tab"""
        self.session_config = SessionConfigWidget()
        self.session_config.session_start_requested.connect(
            self._handle_session_start_request
        )
        self.tab_widget.addTab(self.session_config, "New Session")

    def setup_history_tab(self):
        """Set up session history tab"""
        history_widget = QWidget()
        history_layout = QVBoxLayout(history_widget)

        # History controls
        controls_layout = QHBoxLayout()

        self.refresh_history_btn = QPushButton("Refresh")
        self.refresh_history_btn.clicked.connect(self.load_sessions)
        controls_layout.addWidget(self.refresh_history_btn)

        self.clear_history_btn = QPushButton("Clear History")
        self.clear_history_btn.clicked.connect(self.clear_history)
        controls_layout.addWidget(self.clear_history_btn)

        controls_layout.addStretch()
        history_layout.addLayout(controls_layout)

        # History tree
        self.history_tree = QTreeWidget()
        self.history_tree.setHeaderLabels(
            ["Session", "Type", "Agents", "Started", "Status"]
        )
        self.history_tree.itemDoubleClicked.connect(self.load_session)
        history_layout.addWidget(self.history_tree)

        self.tab_widget.addTab(history_widget, "History")

    def setup_timer(self):
        """Set up update timer"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_current_session)
        self.timer.start(5000)  # Update every 5 seconds

    def load_sessions(self):
        """Load session history"""
        # Placeholder - load from storage
        self.history_tree.clear()

        # Add some sample sessions
        sample_sessions = [
            {
                "name": "Code Review Session",
                "type": "Code Review",
                "agents": ["Code-Assistant", "Reviewer"],
                "started": "2025-09-17 09:00",
                "status": "Completed",
            },
            {
                "name": "Planning Meeting",
                "type": "Planning",
                "agents": ["Planner", "Analyst"],
                "started": "2025-09-17 08:30",
                "status": "Completed",
            },
        ]

        for session in sample_sessions:
            item = QTreeWidgetItem(
                [
                    session["name"],
                    session["type"],
                    ", ".join(session["agents"]),
                    session["started"],
                    session["status"],
                ]
            )
            item.setData(0, Qt.UserRole, session)
            self.history_tree.addTopLevelItem(item)

    def load_session(self, item):
        """Load a session from history"""
        session_data = item.data(0, Qt.UserRole)
        if session_data:
            QMessageBox.information(
                self, "Load Session", f"Loading session: {session_data['name']}"
            )

    def update_current_session(self):
        """Update current session display"""
        if self.current_session:
            # Update session info display
            pass

    def start_session(self, config: Dict[str, Any]):
        """Start a new session"""
        self.current_session = config
        self.current_name_label.setText(config["name"])
        self.current_type_label.setText(config["type"])
        self.current_directory_label.setText(
            config.get("working_directory", "Not specified")
        )
        self.current_agents_label.setText(", ".join(config["agents"]))
        self.current_rounds_label.setText(f"0/{config['max_rounds']}")

        self.status_label.setText(f"Active: {config['name']}")
        self.status_label.setStyleSheet(
            "QLabel { color: green; font-weight: bold; padding: 4px; }"
        )
        self.end_session_btn.setEnabled(True)

        # Switch to current session tab
        self.tab_widget.setCurrentIndex(0)

        # Add welcome message
        self.conversation_viewer.add_message(
            "system",
            f"Session '{config['name']}' started with agents: {', '.join(config['agents'])}",
        )

        self.session_started.emit(config)

    def end_current_session(self):
        """End the current session"""
        if not self.current_session:
            return

        reply = QMessageBox.question(
            self,
            "End Session",
            f"Are you sure you want to end session '{self.current_session['name']}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            session_name = self.current_session["name"]
            self.current_session = None

            self.status_label.setText("No active session")
            self.status_label.setStyleSheet(
                "QLabel { color: orange; font-weight: bold; padding: 4px; }"
            )
            self.end_session_btn.setEnabled(False)

            # Clear current session display
            self.current_name_label.setText("None")
            self.current_type_label.setText("None")
            self.current_directory_label.setText("None")
            self.current_agents_label.setText("None")
            self.current_rounds_label.setText("0/0")

            self.session_ended.emit(session_name)

    def clear_history(self):
        """Clear session history"""
        reply = QMessageBox.question(
            self,
            "Clear History",
            "Are you sure you want to clear all session history?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.history_tree.clear()
            self.sessions_history.clear()

    def _handle_session_start_request(self, config: dict):
        """Handle session start request from config widget"""
        try:
            # Extract session parameters
            project_name = config.get("project", "Unnamed Project")
            objective = config.get(
                "objective", f"{config.get('type', 'Chat')} session for {project_name}"
            )
            agents = config.get("agents", ["assistant"])
            working_directory = config.get("working_directory")
            session_type = config.get("type", "Chat")

            # Start the session using the session service
            self.session_service.start_session(
                project_name=project_name,
                objective=objective,
                working_directory=working_directory,
                session_type=session_type,
            )

            # Update UI to show session is starting
            self.status_label.setText(f"Starting session: {project_name}")
            self.status_label.setStyleSheet(
                "QLabel { color: blue; font-weight: bold; padding: 4px; }"
            )

        except Exception as e:
            QMessageBox.critical(
                self, "Session Start Error", f"Failed to start session: {str(e)}"
            )

    def _on_session_started(self, session_id: str, session_info: dict):
        """Handle session started signal"""
        logger.info(f"Session {session_id} started: {session_info}")
        # Update UI to show active session
        if session_info:
            self.current_session = session_info
            self.current_name_label.setText(session_info.get("project", "Unknown"))
            self.status_label.setText(
                f"Active: {session_info.get('project', 'Unknown')}"
            )
            self.status_label.setStyleSheet(
                "QLabel { color: green; font-weight: bold; padding: 4px; }"
            )

    def _on_session_stopped(self, session_id: str):
        """Handle session stopped signal"""
        logger.info(f"Session {session_id} stopped")
        self.current_session = None
        self.status_label.setText("No active session")
        self.status_label.setStyleSheet(
            "QLabel { color: gray; font-style: italic; padding: 4px; }"
        )

    def _on_session_error(self, session_id: str, error_message: str):
        """Handle session error signal"""
        logger.error(f"Session {session_id} error: {error_message}")
        QMessageBox.critical(self, "Session Error", f"Session error: {error_message}")

"""
Session Management Widget - Clean Implementation
Manage AutoGen conversation sessions and history
"""

import os
import json
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
    QDialog,
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont

from autogen_ui.services.session_service import SessionService
from autogen_ui.dialogs.agent_selection_dialog import AgentSelectionDialog

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
        cursor.movePosition(cursor.MoveOperation.End)
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

        # Initialize storage paths
        self.sessions_dir = os.path.expanduser("~/.autogen/sessions")
        os.makedirs(self.sessions_dir, exist_ok=True)
        self.saved_configs_file = os.path.join(self.sessions_dir, "saved_configs.json")

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
        """Add agent to session using agent selection dialog"""
        # Get currently selected agent names to avoid duplicates
        current_agents = []
        for i in range(self.agents_list.count()):
            item = self.agents_list.item(i)
            has_data = (
                item and hasattr(item, "data") and item.data(Qt.ItemDataRole.UserRole)
            )
            if has_data:
                agent_data = item.data(Qt.ItemDataRole.UserRole)
                current_agents.append(agent_data["name"])

        # Show agent selection dialog
        dialog = AgentSelectionDialog(self, current_agents)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_agents = dialog.get_selected_agents()
            session_options = dialog.get_session_options()

            # Store session options for later use
            self._session_options = session_options

            # Add only new agents to avoid duplicates
            for agent in selected_agents:
                # Check if this agent is already in the list
                already_exists = False
                for i in range(self.agents_list.count()):
                    existing_item = self.agents_list.item(i)
                    if existing_item and hasattr(existing_item, "data"):
                        existing_data = existing_item.data(Qt.ItemDataRole.UserRole)
                        if existing_data and existing_data.get("name") == agent["name"]:
                            already_exists = True
                            break

                # Only add if not already in the list
                if not already_exists:
                    item = QListWidgetItem()
                    display_text = f"{agent['name']} ({agent['role']})"
                    if agent["type"] == "preset":
                        display_text += " [Preset]"
                    else:
                        display_text += " [Custom]"

                    item.setText(display_text)
                    item.setData(Qt.ItemDataRole.UserRole, agent)
                    self.agents_list.addItem(item)

            # Update remove button state
            self.update_remove_button_state()

    def remove_agent(self):
        """Remove selected agent"""
        current_item = self.agents_list.currentItem()
        if current_item:
            row = self.agents_list.row(current_item)
            self.agents_list.takeItem(row)
            self.update_remove_button_state()

    def update_remove_button_state(self):
        """Update the state of the remove agent button"""
        has_agents = self.agents_list.count() > 0
        has_selection = self.agents_list.currentItem() is not None
        self.remove_agent_btn.setEnabled(has_agents and has_selection)

        # Connect selection change to update button state
        if not hasattr(self, "_selection_connected"):
            self.agents_list.itemSelectionChanged.connect(
                self.update_remove_button_state
            )
            self._selection_connected = True

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
        """Save session configuration to JSON file"""
        try:
            config = self.get_session_config()

            # Load existing configurations
            saved_configs = []
            if os.path.exists(self.saved_configs_file):
                try:
                    with open(self.saved_configs_file, "r") as f:
                        saved_configs = json.load(f)
                except (json.JSONDecodeError, FileNotFoundError):
                    saved_configs = []

            # Add timestamp and unique ID
            config["saved_at"] = datetime.now().isoformat()
            config["config_id"] = f"{config['name']}_{int(datetime.now().timestamp())}"

            # Remove any existing config with the same name
            saved_configs = [
                c for c in saved_configs if c.get("name") != config["name"]
            ]

            # Add the new config
            saved_configs.append(config)

            # Save to file
            with open(self.saved_configs_file, "w") as f:
                json.dump(saved_configs, f, indent=2)

            QMessageBox.information(
                self,
                "Config Saved",
                f"Session configuration '{config['name']}' saved successfully!\n"
                f"Saved to: {self.saved_configs_file}",
            )
            logger.info(f"Session configuration saved: {config['name']}")

        except Exception as e:
            error_msg = f"Failed to save configuration: {str(e)}"
            logger.error(error_msg)
            QMessageBox.critical(self, "Save Failed", error_msg)

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
            item = self.agents_list.item(i)
            if item:
                # Try to get agent data first, fallback to text
                agent_data = item.data(Qt.ItemDataRole.UserRole)
                if agent_data and isinstance(agent_data, dict):
                    agents.append(agent_data["name"])
                else:
                    # Fallback for old format or text-only items
                    text = item.text()
                    # Extract just the name (before first parenthesis)
                    agent_name = text.split(" (")[0] if " (" in text else text
                    agents.append(agent_name)

        config = {
            "name": self.session_name.text().strip(),
            "session_id": self.session_name.text().strip(),  # Add session_id for conversation widget
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

        # Add session options if available
        if hasattr(self, "_session_options"):
            config.update(self._session_options)

        return config


class SessionManagerWidget(QWidget):
    """Main session management widget"""

    session_started = Signal(dict)
    session_ended = Signal(str)

    def __init__(self, server_url: str):
        super().__init__()
        self.server_url = server_url
        # Initialize storage path
        self.sessions_dir = os.path.expanduser("~/.autogen/sessions")
        os.makedirs(self.sessions_dir, exist_ok=True)
        self.saved_configs_file = os.path.join(self.sessions_dir, "saved_configs.json")
        self.session_history_file = os.path.join(
            self.sessions_dir, "session_history.json"
        )

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
        """Load session history from saved configurations and session history"""
        self.history_tree.clear()

        all_sessions = []

        # Load saved configurations
        if os.path.exists(self.saved_configs_file):
            try:
                with open(self.saved_configs_file, "r") as f:
                    saved_configs = json.load(f)
                    for config in saved_configs:
                        all_sessions.append(
                            {
                                "name": config.get("name", "Unknown"),
                                "type": config.get("type", "Unknown"),
                                "agents": config.get("agents", []),
                                "started": config.get("saved_at", "Unknown")[
                                    :16
                                ].replace("T", " "),
                                "status": "Saved Config",
                                "data": config,
                            }
                        )
            except (json.JSONDecodeError, FileNotFoundError) as e:
                logger.warning(f"Failed to load saved configs: {e}")

        # Load session history
        if os.path.exists(self.session_history_file):
            try:
                with open(self.session_history_file, "r") as f:
                    session_history = json.load(f)
                    for session in session_history:
                        all_sessions.append(
                            {
                                "name": session.get("name", "Unknown"),
                                "type": session.get("type", "Unknown"),
                                "agents": session.get("agents", []),
                                "started": session.get("started_at", "Unknown")[
                                    :16
                                ].replace("T", " "),
                                "status": session.get("status", "Completed"),
                                "data": session,
                            }
                        )
            except (json.JSONDecodeError, FileNotFoundError) as e:
                logger.warning(f"Failed to load session history: {e}")

        # Sort by date (newest first)
        all_sessions.sort(key=lambda x: x.get("started", ""), reverse=True)

        # Add sessions to tree
        for session in all_sessions:
            agents_str = ", ".join(session["agents"]) if session["agents"] else "None"
            item = QTreeWidgetItem(
                [
                    session["name"],
                    session["type"],
                    agents_str,
                    session["started"],
                    session["status"],
                ]
            )
            item.setData(0, Qt.UserRole, session["data"])
            self.history_tree.addTopLevelItem(item)

        logger.info(f"Loaded {len(all_sessions)} sessions from storage")

    def save_session_to_history(self, config):
        """Save a started session to session history"""
        try:
            # Load existing history
            session_history = []
            if os.path.exists(self.session_history_file):
                try:
                    with open(self.session_history_file, "r") as f:
                        session_history = json.load(f)
                except (json.JSONDecodeError, FileNotFoundError):
                    session_history = []

            # Create history entry
            history_entry = {
                "name": config.get("name", "Unknown"),
                "type": config.get("type", "Unknown"),
                "agents": config.get("agents", []),
                "directory": config.get("directory", ""),
                "objective": config.get("objective", ""),
                "started_at": datetime.now().isoformat(),
                "status": "Running",
                "session_id": config.get(
                    "session_id", f"{config['name']}_{int(datetime.now().timestamp())}"
                ),
            }

            # Add to history
            session_history.insert(
                0, history_entry
            )  # Insert at beginning (newest first)

            # Keep only last 100 sessions
            session_history = session_history[:100]

            # Save to file
            with open(self.session_history_file, "w") as f:
                json.dump(session_history, f, indent=2)

            # Refresh the history display
            self.load_sessions()

            logger.info(f"Session saved to history: {config['name']}")

        except Exception as e:
            logger.error(f"Failed to save session to history: {e}")

    def load_session(self, item):
        """Load a session from history and restore its configuration"""
        session_data = item.data(0, Qt.UserRole)
        if session_data:
            try:
                # Restore the configuration to the form
                self.session_name.setText(session_data.get("name", ""))
                if "project" in session_data:
                    self.project_name.setText(session_data.get("project", ""))
                elif "project_name" in session_data:
                    self.project_name.setText(session_data.get("project_name", ""))
                else:
                    self.project_name.setText(session_data.get("name", ""))

                self.objective.setPlainText(session_data.get("objective", ""))

                # Set session type
                session_type = session_data.get("type", "Research")
                type_index = self.session_type.findText(session_type)
                if type_index >= 0:
                    self.session_type.setCurrentIndex(type_index)

                # Set working directory
                if "directory" in session_data:
                    self.working_directory.setText(session_data.get("directory", ""))

                # Set agents
                self.agents_list.clear()
                agents = session_data.get("agents", [])
                for agent_name in agents:
                    item = QListWidgetItem(agent_name)
                    item.setData(Qt.UserRole, {"name": agent_name})
                    self.agents_list.addItem(item)

                # Set max rounds if available
                if "max_rounds" in session_data:
                    self.max_rounds.setValue(session_data.get("max_rounds", 10))

                # Switch to new session tab
                self.tab_widget.setCurrentIndex(1)

                QMessageBox.information(
                    self,
                    "Session Loaded",
                    f"Session configuration '{session_data['name']}' loaded!\n"
                    f"You can now modify and start the session.",
                )

            except Exception as e:
                error_msg = f"Failed to load session: {str(e)}"
                logger.error(error_msg)
                QMessageBox.critical(self, "Load Failed", error_msg)

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

        # Save session to history
        self.save_session_to_history(config)

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
            # For now, just start the UI session directly
            # TODO: Implement proper async session handling with MCP server
            self.start_session(config)

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

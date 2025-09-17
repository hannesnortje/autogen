"""
Agent Selection Dialog
Allow users to select from available agents (presets and custom) for sessions
"""

import logging
from typing import List, Dict, Any
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QGroupBox,
    QTextEdit,
    QCheckBox,
    QMessageBox,
)
from PySide6.QtCore import Qt

logger = logging.getLogger(__name__)


class AgentSelectionDialog(QDialog):
    """Dialog for selecting agents from available presets and custom agents"""

    def __init__(self, parent=None, selected_agents: List[str] = None):
        super().__init__(parent)
        self.selected_agents = selected_agents or []
        self.available_agents = self.get_available_agents()
        self.setup_ui()
        self.load_agents()

    def setup_ui(self):
        """Set up the dialog UI"""
        self.setWindowTitle("Select Agents")
        self.setModal(True)
        self.resize(600, 400)

        layout = QVBoxLayout(self)

        # Instructions
        instructions = QLabel(
            "Select agents to participate in this session. "
            "Use Ctrl+Click to select multiple agents."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Agent list
        agents_group = QGroupBox("Available Agents")
        agents_layout = QVBoxLayout(agents_group)

        self.agents_list = QListWidget()
        selection_mode = QListWidget.SelectionMode.MultiSelection
        self.agents_list.setSelectionMode(selection_mode)
        selection_changed = self.on_selection_changed
        self.agents_list.itemSelectionChanged.connect(selection_changed)
        agents_layout.addWidget(self.agents_list)

        layout.addWidget(agents_group)

        # Agent details
        details_group = QGroupBox("Agent Details")
        details_layout = QVBoxLayout(details_group)

        self.agent_details = QTextEdit()
        self.agent_details.setReadOnly(True)
        self.agent_details.setMaximumHeight(120)
        details_layout.addWidget(self.agent_details)

        layout.addWidget(details_group)

        # Options
        options_group = QGroupBox("Session Options")
        options_layout = QVBoxLayout(options_group)

        self.enable_collaboration = QCheckBox("Enable Agent Collaboration")
        self.enable_collaboration.setChecked(True)
        self.enable_collaboration.setToolTip(
            "Allow agents to communicate and collaborate during the session"
        )
        options_layout.addWidget(self.enable_collaboration)

        self.enable_code_review = QCheckBox("Enable Code Review")
        self.enable_code_review.setChecked(True)
        self.enable_code_review.setToolTip(
            "Enable agents to review each other's code and suggestions"
        )
        options_layout.addWidget(self.enable_code_review)

        layout.addWidget(options_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self.select_all_agents)
        button_layout.addWidget(self.select_all_btn)

        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.clicked.connect(self.clear_selection)
        button_layout.addWidget(self.clear_btn)

        button_layout.addStretch()

        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept)
        self.ok_btn.setDefault(True)
        button_layout.addWidget(self.ok_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

        # Update button state
        self.update_buttons()

    def get_available_agents(self) -> List[Dict[str, Any]]:
        """Get list of available agents (presets + custom)"""
        # Agent presets with Gemini LLM configuration
        presets = [
            {
                "name": "Code Assistant",
                "description": (
                    "Specialized in programming tasks, code review, and "
                    "technical problem-solving. Excellent for development "
                    "workflows and coding assistance. Uses Gemini LLM."
                ),
                "role": "developer",
                "type": "preset",
                "llm_config": {
                    "model": "gemini-2.0-flash",
                    "api_type": "gemini",
                    "temperature": 0.3,
                },
                "system_message": (
                    "You are a skilled software developer and code assistant. "
                    "Help with programming tasks, code review, debugging, and "
                    "technical problem-solving. Write clean, efficient code "
                    "with proper documentation."
                ),
                "capabilities": [
                    "code_execution",
                    "function_calling",
                    "file_operations",
                ],
            },
            {
                "name": "Data Analyst",
                "description": (
                    "Expert in data analysis, visualization, and "
                    "statistical insights. Perfect for data-driven "
                    "projects and analytical tasks. Uses Gemini LLM."
                ),
                "role": "analyst",
                "type": "preset",
                "llm_config": {
                    "model": "gemini-2.0-flash",
                    "api_type": "gemini",
                    "temperature": 0.1,
                },
                "system_message": (
                    "You are a data analyst specializing in data processing, "
                    "statistical analysis, and visualization. Help analyze "
                    "data, create insights, and suggest data-driven solutions."
                ),
                "capabilities": ["code_execution", "function_calling"],
            },
            {
                "name": "Content Writer",
                "description": (
                    "Skilled in content creation, technical writing, and "
                    "documentation. Ideal for documentation and content "
                    "generation tasks. Uses Gemini LLM."
                ),
                "role": "writer",
                "type": "preset",
                "llm_config": {
                    "model": "gemini-2.0-flash",
                    "api_type": "gemini",
                    "temperature": 0.7,
                },
                "system_message": (
                    "You are a professional content writer and technical "
                    "documentation specialist. Create clear, comprehensive "
                    "documentation, READMEs, and user-friendly content."
                ),
                "capabilities": ["human_input", "web_browsing"],
            },
            {
                "name": "Research Assistant",
                "description": (
                    "Specialized in information gathering, research, and "
                    "analysis. Great for research projects and information "
                    "synthesis."
                ),
                "role": "researcher",
                "type": "preset",
                "capabilities": ["web_browsing", "function_calling"],
            },
        ]

        # TODO: Add custom agents from storage
        # This would load from a config file or database
        custom_agents = []

        return presets + custom_agents

    def load_agents(self):
        """Load agents into the list"""
        self.agents_list.clear()

        for agent in self.available_agents:
            item = QListWidgetItem()

            # Display format: "Name (Role) [Type]"
            display_text = f"{agent['name']} ({agent['role']})"
            if agent["type"] == "preset":
                display_text += " [Preset]"
            else:
                display_text += " [Custom]"

            item.setText(display_text)
            item.setData(Qt.UserRole, agent)

            # Select if previously selected
            if agent["name"] in self.selected_agents:
                item.setSelected(True)

            self.agents_list.addItem(item)

        # Show details for first selected item
        if self.agents_list.selectedItems():
            self.show_agent_details(self.agents_list.selectedItems()[0])

    def on_selection_changed(self):
        """Handle agent selection change"""
        selected_items = self.agents_list.selectedItems()

        if selected_items:
            # Show details for the first selected agent
            self.show_agent_details(selected_items[0])
        else:
            self.agent_details.clear()

        self.update_buttons()

    def show_agent_details(self, item: QListWidgetItem):
        """Show details for the selected agent"""
        agent_data = item.data(Qt.UserRole)

        details = f"**{agent_data['name']}**\n\n"
        details += f"Role: {agent_data['role'].title()}\n"
        details += f"Type: {agent_data['type'].title()}\n\n"
        details += f"Description:\n{agent_data['description']}\n\n"

        if agent_data.get("capabilities"):
            details += "Capabilities:\n"
            for cap in agent_data["capabilities"]:
                details += f"• {cap.replace('_', ' ').title()}\n"

        self.agent_details.setPlainText(details)

    def select_all_agents(self):
        """Select all available agents"""
        for i in range(self.agents_list.count()):
            item = self.agents_list.item(i)
            item.setSelected(True)
        self.update_buttons()

    def clear_selection(self):
        """Clear all selections"""
        self.agents_list.clearSelection()
        self.agent_details.clear()
        self.update_buttons()

    def update_buttons(self):
        """Update button states based on selection"""
        has_selection = bool(self.agents_list.selectedItems())
        self.ok_btn.setEnabled(has_selection)

    def get_selected_agents(self) -> List[Dict[str, Any]]:
        """Get the selected agents"""
        selected = []
        for item in self.agents_list.selectedItems():
            selected.append(item.data(Qt.UserRole))
        return selected

    def get_selected_agent_names(self) -> List[str]:
        """Get selected agent names"""
        return [agent["name"] for agent in self.get_selected_agents()]

    def get_session_options(self) -> Dict[str, bool]:
        """Get session collaboration options"""
        return {
            "collaboration_enabled": self.enable_collaboration.isChecked(),
            "code_review_enabled": self.enable_code_review.isChecked(),
        }

    def accept(self):
        """Handle dialog acceptance"""
        selected = self.get_selected_agents()

        if not selected:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select at least one agent for the session.",
            )
            return

        super().accept()

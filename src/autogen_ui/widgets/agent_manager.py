"""
Agent Management Widget - Clean Implementation
Configure and manage AutoGen agents
"""

import logging
from typing import Dict, Any
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QComboBox,
    QSpinBox,
    QLabel,
    QTextEdit,
    QCheckBox,
    QSlider,
    QMessageBox,
    QScrollArea,
    QListWidget,
    QListWidgetItem,
    QSplitter,
)
from PySide6.QtCore import Qt, Signal

logger = logging.getLogger(__name__)


class AgentConfigWidget(QWidget):
    """Agent configuration form"""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        """Set up agent configuration UI"""
        layout = QVBoxLayout(self)

        # Scroll area for long forms
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Basic agent info
        self.setup_basic_info(scroll_layout)

        # Agent capabilities
        self.setup_capabilities(scroll_layout)

        # Model configuration
        self.setup_model_config(scroll_layout)

        # Memory settings
        self.setup_memory_settings(scroll_layout)

        # Add stretch to push content to top
        scroll_layout.addStretch()

        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)

        # Action buttons
        self.setup_action_buttons(layout)

    def setup_basic_info(self, layout):
        """Set up basic agent information form"""
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_group)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter agent name...")
        basic_layout.addRow("Name:", self.name_input)

        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        self.description_input.setPlaceholderText("Agent description...")
        basic_layout.addRow("Description:", self.description_input)

        self.role_input = QLineEdit()
        self.role_input.setPlaceholderText("Agent role (e.g., 'developer', 'analyst')")
        basic_layout.addRow("Role:", self.role_input)

        layout.addWidget(basic_group)

    def setup_capabilities(self, layout):
        """Set up agent capabilities settings"""
        cap_group = QGroupBox("Capabilities")
        cap_layout = QVBoxLayout(cap_group)

        # Code execution
        self.code_execution_cb = QCheckBox("Enable Code Execution")
        self.code_execution_cb.setToolTip("Allow agent to execute code")
        cap_layout.addWidget(self.code_execution_cb)

        # Human input
        self.human_input_cb = QCheckBox("Require Human Input")
        self.human_input_cb.setToolTip("Agent asks for human confirmation")
        cap_layout.addWidget(self.human_input_cb)

        # Function calling
        self.function_calling_cb = QCheckBox("Function Calling")
        self.function_calling_cb.setToolTip("Agent can call functions")
        cap_layout.addWidget(self.function_calling_cb)

        # Web browsing
        self.web_browsing_cb = QCheckBox("Web Browsing")
        self.web_browsing_cb.setToolTip("Agent can browse the web")
        cap_layout.addWidget(self.web_browsing_cb)

        # File operations
        self.file_ops_cb = QCheckBox("File Operations")
        self.file_ops_cb.setToolTip("Agent can read/write files")
        cap_layout.addWidget(self.file_ops_cb)

        layout.addWidget(cap_group)

    def setup_model_config(self, layout):
        """Set up model configuration"""
        model_group = QGroupBox("Model Configuration")
        model_layout = QFormLayout(model_group)

        # Model selection - Gemini as default and primary option
        self.model_combo = QComboBox()
        self.model_combo.addItems(
            [
                "gemini-2.0-flash",  # Primary Gemini model (default)
                "gemini-pro",  # Alternative Gemini model
                "gpt-4o",  # OpenAI models (requires API key)
                "gpt-4o-mini",
                "gpt-4-turbo",
                "claude-3-opus",  # Anthropic models (requires API key)
                "claude-3-sonnet",
                "claude-3-haiku",
                "local-llama",  # Local models
            ]
        )
        # Set Gemini as default selection
        self.model_combo.setCurrentText("gemini-2.0-flash")
        model_layout.addRow("Model:", self.model_combo)

        # Temperature
        temp_layout = QHBoxLayout()
        self.temperature_slider = QSlider(Qt.Horizontal)
        self.temperature_slider.setRange(0, 200)
        self.temperature_slider.setValue(70)
        self.temperature_slider.setTickPosition(QSlider.TicksBelow)
        self.temperature_slider.setTickInterval(25)

        self.temperature_label = QLabel("0.7")
        self.temperature_slider.valueChanged.connect(
            lambda v: self.temperature_label.setText(f"{v / 100:.1f}")
        )

        temp_layout.addWidget(self.temperature_slider)
        temp_layout.addWidget(self.temperature_label)
        model_layout.addRow("Temperature:", temp_layout)

        # Max tokens
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(100, 8192)
        self.max_tokens_spin.setValue(2048)
        model_layout.addRow("Max Tokens:", self.max_tokens_spin)

        # System prompt
        self.system_prompt = QTextEdit()
        self.system_prompt.setMaximumHeight(100)
        self.system_prompt.setPlaceholderText("System prompt for the agent...")
        model_layout.addRow("System Prompt:", self.system_prompt)

        layout.addWidget(model_group)

    def setup_memory_settings(self, layout):
        """Set up memory integration settings"""
        memory_group = QGroupBox("Memory Settings")
        memory_layout = QFormLayout(memory_group)

        # Memory integration
        self.memory_enabled_cb = QCheckBox("Enable Memory Integration")
        memory_layout.addRow("Memory:", self.memory_enabled_cb)

        # Memory scope
        self.memory_scope_combo = QComboBox()
        self.memory_scope_combo.addItems(["conversation", "project", "global"])
        memory_layout.addRow("Memory Scope:", self.memory_scope_combo)

        # Memory retrieval limit
        self.memory_limit_spin = QSpinBox()
        self.memory_limit_spin.setRange(1, 50)
        self.memory_limit_spin.setValue(10)
        memory_layout.addRow("Retrieval Limit:", self.memory_limit_spin)

        layout.addWidget(memory_group)

    def setup_action_buttons(self, layout):
        """Set up action buttons"""
        button_layout = QHBoxLayout()

        self.save_btn = QPushButton("Save Agent")
        self.save_btn.clicked.connect(self.save_agent)
        button_layout.addWidget(self.save_btn)

        self.test_btn = QPushButton("Test Agent")
        self.test_btn.clicked.connect(self.test_agent)
        button_layout.addWidget(self.test_btn)

        self.reset_btn = QPushButton("Reset Form")
        self.reset_btn.clicked.connect(self.reset_form)
        button_layout.addWidget(self.reset_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

    def save_agent(self):
        """Save agent configuration"""
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Warning", "Please enter an agent name")
            return

        config = self.get_agent_config()
        QMessageBox.information(self, "Success", f"Agent '{config['name']}' saved")

    def test_agent(self):
        """Test agent configuration"""
        config = self.get_agent_config()
        QMessageBox.information(
            self,
            "Test Agent",
            f"Testing agent '{config['name']}' with model {config['model']}",
        )

    def reset_form(self):
        """Reset the form"""
        self.name_input.clear()
        self.description_input.clear()
        self.role_input.clear()
        self.code_execution_cb.setChecked(False)
        self.human_input_cb.setChecked(False)
        self.function_calling_cb.setChecked(False)
        self.web_browsing_cb.setChecked(False)
        self.file_ops_cb.setChecked(False)
        self.model_combo.setCurrentIndex(0)
        self.temperature_slider.setValue(70)
        self.max_tokens_spin.setValue(2048)
        self.system_prompt.clear()
        self.memory_enabled_cb.setChecked(False)
        self.memory_scope_combo.setCurrentIndex(0)
        self.memory_limit_spin.setValue(10)

    def get_agent_config(self) -> Dict[str, Any]:
        """Get current agent configuration"""
        return {
            "name": self.name_input.text().strip(),
            "description": self.description_input.toPlainText().strip(),
            "role": self.role_input.text().strip(),
            "capabilities": {
                "code_execution": self.code_execution_cb.isChecked(),
                "human_input": self.human_input_cb.isChecked(),
                "function_calling": self.function_calling_cb.isChecked(),
                "web_browsing": self.web_browsing_cb.isChecked(),
                "file_operations": self.file_ops_cb.isChecked(),
            },
            "model": {
                "name": self.model_combo.currentText(),
                "temperature": self.temperature_slider.value() / 100.0,
                "max_tokens": self.max_tokens_spin.value(),
                "system_prompt": self.system_prompt.toPlainText().strip(),
            },
            "memory": {
                "enabled": self.memory_enabled_cb.isChecked(),
                "scope": self.memory_scope_combo.currentText(),
                "retrieval_limit": self.memory_limit_spin.value(),
            },
        }

    def set_agent_config(self, config: Dict[str, Any]):
        """Set agent configuration"""
        self.name_input.setText(config.get("name", ""))
        self.description_input.setPlainText(config.get("description", ""))
        self.role_input.setText(config.get("role", ""))

        caps = config.get("capabilities", {})
        self.code_execution_cb.setChecked(caps.get("code_execution", False))
        self.human_input_cb.setChecked(caps.get("human_input", False))
        self.function_calling_cb.setChecked(caps.get("function_calling", False))
        self.web_browsing_cb.setChecked(caps.get("web_browsing", False))
        self.file_ops_cb.setChecked(caps.get("file_operations", False))

        model = config.get("model", {})
        model_name = model.get("name", "gpt-4o")
        if model_name in [
            self.model_combo.itemText(i) for i in range(self.model_combo.count())
        ]:
            self.model_combo.setCurrentText(model_name)
        self.temperature_slider.setValue(int(model.get("temperature", 0.7) * 100))
        self.max_tokens_spin.setValue(model.get("max_tokens", 2048))
        self.system_prompt.setPlainText(model.get("system_prompt", ""))

        memory = config.get("memory", {})
        self.memory_enabled_cb.setChecked(memory.get("enabled", False))
        self.memory_scope_combo.setCurrentText(memory.get("scope", "conversation"))
        self.memory_limit_spin.setValue(memory.get("retrieval_limit", 10))


class AgentManagerWidget(QWidget):
    """Main agent management interface"""

    agent_selected = Signal(dict)
    agent_created = Signal(dict)
    agent_updated = Signal(dict)
    agent_deleted = Signal(str)

    def __init__(self, server_url: str):
        super().__init__()
        self.server_url = server_url
        self.current_agents = []

        self.setup_ui()
        self.setup_presets()
        self.load_agents()

    def setup_ui(self):
        """Set up agent management UI"""
        layout = QHBoxLayout(self)

        # Main splitter
        splitter = QSplitter(Qt.Horizontal)

        # Left side - agent list and presets
        self.setup_left_panel(splitter)

        # Right side - agent configuration
        self.setup_right_panel(splitter)

        # Set splitter proportions
        splitter.setSizes([300, 500])

        layout.addWidget(splitter)

    def setup_left_panel(self, splitter):
        """Set up left panel with agent list"""
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # Agent presets
        presets_group = QGroupBox("Agent Presets")
        presets_layout = QVBoxLayout(presets_group)

        self.presets_list = QListWidget()
        self.presets_list.itemClicked.connect(self.on_preset_selected)
        presets_layout.addWidget(self.presets_list)

        left_layout.addWidget(presets_group)

        # Current agents
        agents_group = QGroupBox("Current Agents")
        agents_layout = QVBoxLayout(agents_group)

        self.agents_list = QListWidget()
        self.agents_list.itemClicked.connect(self.on_agent_selected)
        agents_layout.addWidget(self.agents_list)

        # Agent actions
        actions_layout = QHBoxLayout()

        self.new_agent_btn = QPushButton("New")
        self.new_agent_btn.clicked.connect(self.new_agent)
        actions_layout.addWidget(self.new_agent_btn)

        self.delete_agent_btn = QPushButton("Delete")
        self.delete_agent_btn.clicked.connect(self.delete_agent)
        self.delete_agent_btn.setEnabled(False)
        actions_layout.addWidget(self.delete_agent_btn)

        agents_layout.addLayout(actions_layout)
        left_layout.addWidget(agents_group)

        splitter.addWidget(left_widget)

    def setup_right_panel(self, splitter):
        """Set up right panel with agent configuration"""
        self.agent_config = AgentConfigWidget()
        splitter.addWidget(self.agent_config)

    def setup_presets(self):
        """Set up agent presets"""
        presets = [
            {
                "name": "💻 Code Assistant",
                "description": "Expert programmer and code reviewer",
                "role": "developer",
                "capabilities": {
                    "code_execution": True,
                    "function_calling": True,
                    "file_operations": True,
                },
                "model": {
                    "name": "gemini-2.0-flash",
                    "temperature": 0.3,
                    "system_prompt": (
                        "You are an expert programmer. Write clean, "
                        "efficient code and provide detailed explanations."
                    ),
                },
            },
            {
                "name": "📊 Data Analyst",
                "description": "Data analysis and visualization expert",
                "role": "analyst",
                "capabilities": {
                    "code_execution": True,
                    "function_calling": True,
                },
                "model": {
                    "name": "gemini-2.0-flash",
                    "temperature": 0.5,
                    "system_prompt": (
                        "You are a data analyst. Focus on insights, "
                        "patterns, and clear visualizations."
                    ),
                },
            },
            {
                "name": "✍️ Content Writer",
                "description": "Creative and technical writing specialist",
                "role": "writer",
                "capabilities": {
                    "web_browsing": True,
                },
                "model": {
                    "name": "gemini-2.0-flash",
                    "temperature": 0.8,
                    "system_prompt": (
                        "You are a skilled writer. Create engaging, "
                        "well-structured content."
                    ),
                },
            },
            {
                "name": "🔍 Research Assistant",
                "description": "Information gathering and analysis",
                "role": "researcher",
                "capabilities": {
                    "web_browsing": True,
                    "function_calling": True,
                },
                "model": {
                    "name": "gemini-2.0-flash",
                    "temperature": 0.4,
                    "system_prompt": (
                        "You are a research assistant. Provide accurate, "
                        "well-sourced information."
                    ),
                },
                "memory": {"enabled": True, "scope": "project"},
            },
        ]

        for preset in presets:
            item = QListWidgetItem(preset["name"])
            item.setData(Qt.UserRole, preset)
            item.setToolTip(preset["description"])
            self.presets_list.addItem(item)

    def load_agents(self):
        """Load existing agents"""
        # For now, just show placeholder
        self.agents_list.clear()

        # Add some sample agents
        sample_agents = [
            {"name": "Assistant-1", "role": "general", "status": "active"},
            {"name": "Code-Helper", "role": "developer", "status": "inactive"},
        ]

        for agent in sample_agents:
            item = QListWidgetItem(f"{agent['name']} ({agent['role']})")
            item.setData(Qt.UserRole, agent)
            self.agents_list.addItem(item)

    def on_preset_selected(self, item):
        """Handle preset selection"""
        preset = item.data(Qt.UserRole)
        if preset:
            self.agent_config.set_agent_config(preset)

    def on_agent_selected(self, item):
        """Handle agent selection"""
        agent = item.data(Qt.UserRole)
        if agent:
            self.delete_agent_btn.setEnabled(True)
            # Load agent config (placeholder for now)
            self.agent_selected.emit(agent)

    def new_agent(self):
        """Create new agent"""
        self.agent_config.reset_form()
        self.delete_agent_btn.setEnabled(False)

    def delete_agent(self):
        """Delete selected agent"""
        current_item = self.agents_list.currentItem()
        if current_item:
            agent = current_item.data(Qt.UserRole)
            reply = QMessageBox.question(
                self,
                "Delete Agent",
                f"Are you sure you want to delete agent '{agent['name']}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                self.agents_list.takeItem(self.agents_list.row(current_item))
                self.delete_agent_btn.setEnabled(False)
                self.agent_deleted.emit(agent["name"])

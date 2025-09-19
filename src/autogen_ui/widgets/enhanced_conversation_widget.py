"""
Enhanced Conversation Widget with Session Integration
Replaces the mock conversation widget with real session service integration
"""

import logging
from typing import Dict, Optional, List
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QTextEdit,
    QPushButton,
    QLabel,
    QMessageBox,
    QFileDialog,
    QCheckBox,
    QScrollArea,
)
from PySide6.QtGui import QFont, QTextCursor

from ..services.conversation_service import (
    ConversationService,
    ConversationMessage,
    MessageType,
)

logger = logging.getLogger(__name__)


class EnhancedConversationWidget(QWidget):
    """Enhanced conversation widget with agent targeting and message type support"""

    def __init__(self, conversation_service: ConversationService):
        super().__init__()
        self.conversation_service = conversation_service
        self.current_session_id: Optional[str] = None
        self.agent_checkboxes: Dict[str, QCheckBox] = {}

        # Connect to conversation service signals
        self.conversation_service.message_added.connect(self.on_message_added)
        self.conversation_service.message_sent.connect(self.on_message_sent)
        self.conversation_service.agent_typing_started.connect(
            self.on_agent_typing_started
        )
        self.conversation_service.agent_typing_stopped.connect(
            self.on_agent_typing_stopped
        )
        self.conversation_service.conversation_cleared.connect(
            self.on_conversation_cleared
        )
        self.conversation_service.conversation_exported.connect(
            self.on_conversation_exported
        )
        self.conversation_service.error_occurred.connect(self.on_error_occurred)

        self.setup_ui()
        self.setup_styles()

    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)

        # Conversation display area
        self.conversation_display = QTextEdit()
        self.conversation_display.setReadOnly(True)
        self.conversation_display.setFont(QFont("Consolas", 10))
        layout.addWidget(self.conversation_display, stretch=1)

        # Agent targeting section
        agent_section = QGroupBox("Agent Targeting")
        agent_layout = QVBoxLayout(agent_section)

        # Scroll area for agent checkboxes
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        self.agent_checkboxes_layout = QVBoxLayout(scroll_widget)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(150)
        agent_layout.addWidget(scroll_area)

        # All agents checkbox
        self.all_agents_checkbox = QCheckBox("All Agents (Session Chat)")
        self.all_agents_checkbox.setChecked(True)
        self.all_agents_checkbox.toggled.connect(self.on_all_agents_toggled)
        agent_layout.addWidget(self.all_agents_checkbox)

        layout.addWidget(agent_section)

        # Message input area
        input_layout = QHBoxLayout()

        self.message_input = QTextEdit()
        self.message_input.setMaximumHeight(100)
        self.message_input.setPlaceholderText("Type your message here...")
        input_layout.addWidget(self.message_input, stretch=1)

        # Send button
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)

        layout.addLayout(input_layout)

        # Control buttons
        control_layout = QHBoxLayout()

        self.clear_button = QPushButton("Clear Conversation")
        self.clear_button.clicked.connect(self.clear_conversation)
        control_layout.addWidget(self.clear_button)

        self.export_button = QPushButton("Export Conversation")
        self.export_button.clicked.connect(self.export_conversation)
        control_layout.addWidget(self.export_button)

        control_layout.addStretch()

        # Status label
        self.status_label = QLabel("Ready")
        control_layout.addWidget(self.status_label)

        layout.addLayout(control_layout)

    def setup_styles(self):
        """Setup widget styling"""
        self.setStyleSheet(
            """
            QTextEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Consolas', monospace;
            }
            QPushButton {
                background-color: #007ACC;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ccc;
                border-radius: 5px;
                margin: 5px 0px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QCheckBox {
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """
        )

    def set_session(self, session_id: str):
        """Set the current conversation session"""
        self.current_session_id = session_id
        self.conversation_display.clear()
        self.status_label.setText(f"Connected to session: {session_id[:8]}...")

        # Load existing conversation
        try:
            messages = self.conversation_service.get_conversation_history(session_id)
            for message in messages:
                self.display_message(message)
        except Exception as e:
            logger.error(f"Failed to load conversation history: {e}")
            self.status_label.setText("Failed to load conversation history")

    def update_available_agents(self, agents: List[str]):
        """Update the list of available agents for targeting"""
        # Clear existing checkboxes
        for checkbox in self.agent_checkboxes.values():
            checkbox.deleteLater()
        self.agent_checkboxes.clear()

        # Add new checkboxes
        for agent_name in agents:
            checkbox = QCheckBox(agent_name)
            checkbox.toggled.connect(self.on_agent_checkbox_toggled)
            self.agent_checkboxes_layout.addWidget(checkbox)
            self.agent_checkboxes[agent_name] = checkbox

    def on_all_agents_toggled(self, checked: bool):
        """Handle all agents checkbox toggle"""
        if checked:
            # Uncheck individual agent checkboxes
            for checkbox in self.agent_checkboxes.values():
                checkbox.setChecked(False)

    def on_agent_checkbox_toggled(self, checked: bool):
        """Handle individual agent checkbox toggle"""
        if checked:
            # Uncheck all agents checkbox
            self.all_agents_checkbox.setChecked(False)

    def get_selected_agents(self) -> List[str]:
        """Get list of selected agents for targeting"""
        if self.all_agents_checkbox.isChecked():
            return []  # Empty list means all agents (session chat)

        selected = []
        for agent_name, checkbox in self.agent_checkboxes.items():
            if checkbox.isChecked():
                selected.append(agent_name)

        return selected

    def display_message(self, message: ConversationMessage):
        """Display a message in the conversation area with enhanced formatting"""
        cursor = self.conversation_display.textCursor()
        cursor.movePosition(QTextCursor.End)

        # Get message type for styling
        message_type = getattr(message, "message_type", None)
        if isinstance(message_type, MessageType):
            message_type = message_type.value

        # Determine message styling based on type
        if message.role == "user":
            # User messages - Blue
            sender_text = "You"
            color = "#007ACC"
            icon = "🔵"
            border_style = "solid"
        elif message_type == "agent_response":
            # Agent responses - Green
            sender_text = message.agent_name or "Assistant"
            color = "#28A745"
            icon = "🟢"
            border_style = "solid"
        elif message_type == "agent_to_agent":
            # Agent to agent communication - Yellow
            source = message.agent_name or "Agent"
            target = getattr(message, "target_agent", "Unknown")
            sender_text = f"{source} → {target}"
            color = "#FFD700"
            icon = "🟡"
            border_style = "solid"
        elif message_type == "agent_thinking":
            # Agent reasoning/thinking - Orange
            sender_text = f"{message.agent_name or 'Agent'} (thinking)"
            color = "#FF8C00"
            icon = "🟠"
            border_style = "dashed"
        elif message_type == "agent_coordination":
            # Agent coordination - Purple
            sender_text = "Agents coordinating"
            color = "#8A2BE2"
            icon = "🟣"
            border_style = "solid"
        elif message.role == "system":
            # System messages - Gray
            sender_text = "System"
            color = "#808080"
            icon = "⚪"
            border_style = "solid"
        else:
            # Fallback for unknown types - Default blue
            sender_text = message.agent_name or "Assistant"
            color = "#4169E1"
            icon = "🔵"
            border_style = "solid"

        # Add target information for targeted messages
        target_info = ""
        if hasattr(message, "target_agents") and message.target_agents:
            targets = ", ".join(message.target_agents)
            target_info = f" → {targets}"

        # Create enhanced formatted message
        timestamp = message.timestamp.strftime("%H:%M:%S")
        formatted_message = f"""
<div style="margin: 10px 0; padding: 12px; border-left: 4px {border_style} {color}; background-color: {color}10; border-radius: 6px;">
    <div style="display: flex; align-items: center; margin-bottom: 8px;">
        <span style="font-size: 14px; margin-right: 8px;">{icon}</span>
        <strong style="color: {color}; font-size: 12px;">{sender_text}{target_info}</strong>
        <span style="color: #666; font-size: 10px; margin-left: auto;">{timestamp}</span>
    </div>
    <div style="font-size: 11px; line-height: 1.4; color: #333; white-space: pre-wrap;">{message.content}</div>
</div>
"""

        cursor.insertHtml(formatted_message)

        # Auto-scroll to bottom
        scrollbar = self.conversation_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def send_message(self):
        """Send a user message"""
        if not self.current_session_id:
            QMessageBox.warning(
                self, "No Session", "Please select a conversation session first."
            )
            return

        message_text = self.message_input.toPlainText().strip()
        if not message_text:
            return

        try:
            selected_agents = self.get_selected_agents()

            if selected_agents:
                # Send targeted message to specific agents
                message = self.conversation_service.create_targeted_user_message(
                    session_id=self.current_session_id,
                    content=message_text,
                    target_agents=selected_agents,
                )
                self.conversation_service.send_targeted_message(
                    self.current_session_id, message_text, selected_agents
                )
            else:
                # Send to session (all agents)
                message = self.conversation_service.create_user_message(
                    session_id=self.current_session_id, content=message_text
                )
                self.conversation_service.send_message(
                    self.current_session_id, message_text
                )

            # Display the message immediately
            self.display_message(message)

            # Clear input
            self.message_input.clear()
            self.status_label.setText("Sending message...")

        except Exception as e:
            logger.error(f"Failed to send message: {e}")

    def clear_conversation(self):
        """Clear the conversation"""
        if not self.current_session_id:
            return

        reply = QMessageBox.question(
            self,
            "Clear Conversation",
            "Are you sure you want to clear the conversation? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.conversation_display.clear()
            self.conversation_service.clear_conversation(self.current_session_id)

    def export_conversation(self):
        """Export conversation to file"""
        if not self.current_session_id:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Conversation",
            f"conversation_{self.current_session_id[:8]}.txt",
            "Text Files (*.txt);;JSON Files (*.json);;All Files (*)",
        )

        if file_path:
            try:
                messages = self.conversation_service.get_conversation_history(
                    self.current_session_id
                )

                if file_path.endswith(".json"):
                    # Export as JSON
                    import json

                    export_data = [
                        {
                            "timestamp": msg.timestamp.isoformat(),
                            "role": msg.role,
                            "content": msg.content,
                            "agent_name": msg.agent_name,
                            "message_type": (
                                msg.message_type.value
                                if hasattr(msg, "message_type")
                                else None
                            ),
                            "target_agents": getattr(msg, "target_agents", None),
                        }
                        for msg in messages
                    ]
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(export_data, f, indent=2, ensure_ascii=False)
                else:
                    # Export as text
                    with open(file_path, "w", encoding="utf-8") as f:
                        for msg in messages:
                            timestamp = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                            sender = (
                                msg.agent_name
                                if msg.role == "assistant"
                                else msg.role.title()
                            )
                            f.write(f"[{timestamp}] {sender}: {msg.content}\n\n")

                self.status_label.setText(f"Exported to: {file_path}")
            except Exception as e:
                logger.error(f"Failed to export conversation: {e}")
                QMessageBox.critical(
                    self, "Export Error", f"Failed to export conversation: {e}"
                )

    # Signal handlers
    def on_message_added(self, message: ConversationMessage):
        """Handle new message added to conversation"""
        if message.session_id == self.current_session_id:
            self.display_message(message)

    def on_message_sent(self, session_id: str, message_id: str):
        """Handle message sent confirmation"""
        if session_id == self.current_session_id:
            self.status_label.setText("Message sent successfully")

    def on_agent_typing_started(self, session_id: str, agent_name: str):
        """Handle agent started typing"""
        if session_id == self.current_session_id:
            # Show typing indicator
            self.status_label.setText(f"{agent_name} is thinking...")

    def on_agent_typing_stopped(self, session_id: str, agent_name: str):
        """Handle agent stopped typing"""
        if session_id == self.current_session_id:
            # Clear typing indicator
            if self.status_label.text() == f"{agent_name} is thinking...":
                self.status_label.setText("Ready")

    def on_conversation_cleared(self, session_id: str):
        """Handle conversation cleared"""
        if session_id == self.current_session_id:
            self.conversation_display.clear()
            self.status_label.setText("Conversation cleared")

    def on_conversation_exported(self, session_id: str, file_path: str):
        """Handle conversation exported"""
        if session_id == self.current_session_id:
            self.status_label.setText(f"Exported to: {file_path}")

    def on_error_occurred(self, session_id: str, error_message: str):
        """Handle conversation service error"""
        if session_id == self.current_session_id:
            self.status_label.setText(f"Error: {error_message}")
            QMessageBox.critical(self, "Conversation Error", error_message)

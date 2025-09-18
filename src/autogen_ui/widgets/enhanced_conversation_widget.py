"""
Enhanced Conversation Widget with Session Integration
Replaces the mock conversation widget with real session service integration
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
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
    QFrame,
)
from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont, QTextCursor

from ..services.conversation_service import ConversationService, ConversationMessage

logger = logging.getLogger(__name__)


class TypingIndicator(QFrame):
    """Widget to show agent typing indicators"""

    def __init__(self):
        super().__init__()
        self.active_agents = set()
        self.setup_ui()

        # Animation timer
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_frame = 0

    def setup_ui(self):
        """Set up typing indicator UI"""
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet(
            """
            QFrame {
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 4px;
            }
        """
        )
        self.setMaximumHeight(30)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        self.typing_label = QLabel()
        self.typing_label.setStyleSheet(
            "color: #666; font-style: italic; font-size: 11px;"
        )
        layout.addWidget(self.typing_label)

        self.setVisible(False)

    def add_typing_agent(self, agent_name: str):
        """Add an agent to typing indicator"""
        self.active_agents.add(agent_name)
        self.update_display()

    def remove_typing_agent(self, agent_name: str):
        """Remove an agent from typing indicator"""
        self.active_agents.discard(agent_name)
        self.update_display()

    def update_display(self):
        """Update the typing indicator display"""
        if not self.active_agents:
            self.setVisible(False)
            self.animation_timer.stop()
            return

        agents_list = list(self.active_agents)
        if len(agents_list) == 1:
            text = f"{agents_list[0]} is typing"
        elif len(agents_list) == 2:
            text = f"{agents_list[0]} and {agents_list[1]} are typing"
        else:
            text = f"{', '.join(agents_list[:-1])}, and {agents_list[-1]} are typing"

        self.typing_label.setText(text)
        self.setVisible(True)

        # Start animation
        if not self.animation_timer.isActive():
            self.animation_timer.start(500)  # 500ms intervals

    def update_animation(self):
        """Update typing animation"""
        dots = "." * ((self.animation_frame % 3) + 1)
        current_text = self.typing_label.text()
        base_text = current_text.rstrip(".")
        self.typing_label.setText(f"{base_text}{dots}")
        self.animation_frame += 1


class EnhancedConversationWidget(QWidget):
    """Enhanced conversation widget with session service integration"""

    def __init__(self, conversation_service: ConversationService):
        super().__init__()
        self.conversation_service = conversation_service
        self.current_session_id: Optional[str] = None
        self.current_session_config: Optional[Dict[str, Any]] = None

        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        """Set up the enhanced conversation UI"""
        layout = QVBoxLayout(self)

        # Session info header
        self.session_header = QLabel("No active session")
        self.session_header.setStyleSheet(
            """
            QLabel {
                font-weight: bold;
                color: #666;
                padding: 8px;
                background-color: #f8f9fa;
                border-radius: 4px;
                border: 1px solid #e9ecef;
            }
        """
        )
        layout.addWidget(self.session_header)

        # Conversation display
        conv_group = QGroupBox("Conversation")
        conv_layout = QVBoxLayout(conv_group)

        self.conversation_text = QTextEdit()
        self.conversation_text.setReadOnly(True)
        self.conversation_text.setFont(QFont("monospace", 10))
        self.conversation_text.setPlaceholderText(
            "AutoGen conversation will appear here...\n\n"
            "Start a new session to begin a conversation with agents."
        )
        conv_layout.addWidget(self.conversation_text)

        # Typing indicator
        self.typing_indicator = TypingIndicator()
        conv_layout.addWidget(self.typing_indicator)

        layout.addWidget(conv_group)

        # Input area
        input_group = QGroupBox("Your Message")
        input_layout = QVBoxLayout(input_group)

        self.message_input = QTextEdit()
        self.message_input.setMaximumHeight(100)
        self.message_input.setPlaceholderText("Type your message here...")
        input_layout.addWidget(self.message_input)

        # Control buttons
        button_layout = QHBoxLayout()

        self.send_btn = QPushButton("Send Message")
        self.send_btn.clicked.connect(self.send_message)
        self.send_btn.setEnabled(False)
        button_layout.addWidget(self.send_btn)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_conversation)
        button_layout.addWidget(self.clear_btn)

        self.export_btn = QPushButton("Export...")
        self.export_btn.clicked.connect(self.export_conversation)
        self.export_btn.setEnabled(False)
        button_layout.addWidget(self.export_btn)

        button_layout.addStretch()
        input_layout.addLayout(button_layout)

        layout.addWidget(input_group)

        # Status area
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.status_label)

    def connect_signals(self):
        """Connect conversation service signals"""
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

    def set_active_session(self, session_id: str, session_config: Dict[str, Any]):
        """Set the active session for the conversation"""
        self.current_session_id = session_id
        self.current_session_config = session_config

        # Update UI state
        session_name = session_config.get("name", "Unknown Session")
        agents = session_config.get("agents", [])
        self.session_header.setText(
            f"Active Session: {session_name} | Agents: {', '.join(agents)}"
        )
        self.session_header.setStyleSheet(
            """
            QLabel {
                font-weight: bold;
                color: #155724;
                padding: 8px;
                background-color: #d4edda;
                border-radius: 4px;
                border: 1px solid #c3e6cb;
            }
        """
        )

        self.send_btn.setEnabled(True)
        self.export_btn.setEnabled(True)

        # Load existing conversation if any
        self.load_conversation()

        logger.info(f"Set active session: {session_id}")

    def clear_active_session(self):
        """Clear the active session"""
        self.current_session_id = None
        self.current_session_config = None

        self.session_header.setText("No active session")
        self.session_header.setStyleSheet(
            """
            QLabel {
                font-weight: bold;
                color: #666;
                padding: 8px;
                background-color: #f8f9fa;
                border-radius: 4px;
                border: 1px solid #e9ecef;
            }
        """
        )

        self.send_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        self.conversation_text.clear()

        # Clear typing indicators
        self.typing_indicator.active_agents.clear()
        self.typing_indicator.update_display()

    def load_conversation(self):
        """Load conversation history for current session"""
        if not self.current_session_id:
            return

        conversation = self.conversation_service.get_conversation(
            self.current_session_id
        )

        # Clear and rebuild conversation display
        self.conversation_text.clear()

        for message in conversation:
            self.display_message(message)

    def display_message(self, message: ConversationMessage):
        """Display a message in the conversation area"""
        cursor = self.conversation_text.textCursor()
        cursor.movePosition(QTextCursor.End)

        # Format message based on role
        if message.role == "user":
            sender_text = "You"
            color = "#2E8B57"  # Green
        elif message.role == "system":
            sender_text = "System"
            color = "#8B4513"  # Brown
        else:  # assistant
            sender_text = message.agent_name or "Assistant"
            color = "#4169E1"  # Blue

        # Create formatted message
        timestamp = message.timestamp
        formatted_message = (
            f'<div style="margin: 10px 0; padding: 8px; border-left: 3px solid {color};">'
            f'<b style="color: {color};">{sender_text}</b> '
            f'<span style="color: #888; font-size: 10px;">[{timestamp}]</span><br>'
            f"{message.content}"
            f"</div>"
        )

        cursor.insertHtml(formatted_message)
        self.conversation_text.setTextCursor(cursor)

        # Auto-scroll to bottom
        scrollbar = self.conversation_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def send_message(self):
        """Send a user message"""
        if not self.current_session_id:
            QMessageBox.warning(self, "Warning", "No active session")
            return

        message = self.message_input.toPlainText().strip()
        if not message:
            return

        try:
            # Send message through conversation service
            self.conversation_service.send_message(self.current_session_id, message)

            # Clear input
            self.message_input.clear()

            # Update status
            self.status_label.setText("Message sent - waiting for agent responses...")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to send message: {str(e)}")
            logger.error(f"Failed to send message: {e}")

    def clear_conversation(self):
        """Clear the conversation"""
        if not self.current_session_id:
            return

        reply = QMessageBox.question(
            self,
            "Clear Conversation",
            "Are you sure you want to clear the conversation history?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.conversation_service.clear_conversation(self.current_session_id)

    def export_conversation(self):
        """Export conversation to file"""
        if not self.current_session_id:
            return

        # Get export format choice
        reply = QMessageBox.question(
            self,
            "Export Format",
            "Choose export format:\n\nYes = JSON\nNo = Markdown",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.Yes,
        )

        if reply == QMessageBox.Cancel:
            return

        format_type = "json" if reply == QMessageBox.Yes else "markdown"
        extension = "json" if format_type == "json" else "md"

        # Get file path
        default_name = f"conversation_{self.current_session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{extension}"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Conversation",
            default_name,
            f"{'JSON files (*.json)' if format_type == 'json' else 'Markdown files (*.md)'};;All files (*)",
        )

        if file_path:
            success = self.conversation_service.export_conversation(
                self.current_session_id, file_path, format_type
            )
            if success:
                QMessageBox.information(
                    self, "Export Successful", f"Conversation exported to:\n{file_path}"
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
            self.typing_indicator.add_typing_agent(agent_name)
            self.status_label.setText(f"{agent_name} is thinking...")

    def on_agent_typing_stopped(self, session_id: str, agent_name: str):
        """Handle agent stopped typing"""
        if session_id == self.current_session_id:
            self.typing_indicator.remove_typing_agent(agent_name)
            if not self.typing_indicator.active_agents:
                self.status_label.setText("Ready")

    def on_conversation_cleared(self, session_id: str):
        """Handle conversation cleared"""
        if session_id == self.current_session_id:
            self.conversation_text.clear()
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

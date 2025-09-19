"""
Enhanced Conversation Widget with Session Integration
Replaces the mock conversation widget with real session service integration
"""

import logging
from datetime import datetime
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
    QApplication,
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

    def __init__(
        self, conversation_service: ConversationService, use_mcp: bool = False
    ):
        super().__init__()
        self.conversation_service = conversation_service
        self.current_session_id: Optional[str] = None
        self.agent_checkboxes: Dict[str, QCheckBox] = {}
        self.use_mcp_integration = use_mcp  # MCP integration flag

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

    def set_session_id(self, session_id: str):
        """Set the current conversation session"""
        logger.info(
            f"Enhanced Conversation Widget: set_session_id called with: {session_id}"
        )
        self.current_session_id = session_id
        if session_id:
            self.conversation_display.clear()
            self.status_label.setText(f"Connected to session: {session_id[:8]}...")
            logger.info(f"Session connected: {session_id}")

            # Load existing conversation
            try:
                messages = self.conversation_service.get_conversation_history(
                    session_id
                )
                for message in messages:
                    self.display_message(message)
                logger.info(f"Loaded {len(messages)} messages for session {session_id}")
            except Exception as e:
                logger.error(f"Failed to load conversation history: {e}")
                self.status_label.setText("Failed to load conversation history")
        else:
            self.conversation_display.clear()
            self.status_label.setText("No active session")
            logger.info("Session disconnected")

    def set_session(self, session_id: str):
        """Alias for backward compatibility"""
        self.set_session_id(session_id)

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
        timestamp = message.timestamp
        # Handle both string and datetime timestamp formats
        if hasattr(message.timestamp, "strftime"):
            timestamp = message.timestamp.strftime("%H:%M:%S")
        else:
            timestamp = str(message.timestamp)  # Already a string
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
        # BASIC DEBUG - verify method is called
        with open("/tmp/autogen_debug.txt", "a") as f:
            f.write(
                f"[{datetime.now()}] SEND_MESSAGE CALLED - session_id: {self.current_session_id}\n"
            )

        # DIRECT SESSION DETECTION WITH FILE LOGGING
        if not self.current_session_id:
            self.status_label.setText("🔍 Directly checking for active session...")

            debug_file = "/tmp/autogen_debug.txt"
            with open(debug_file, "a") as f:
                f.write("=" * 60 + "\n")
                f.write(
                    f"[{datetime.now()}] ENHANCED CONVERSATION: Direct session detection starting\n"
                )

            # Get the main window directly
            try:
                app = QApplication.instance()
                main_window = None

                with open(debug_file, "a") as f:
                    f.write(f"Found {len(app.topLevelWidgets())} top-level widgets\n")

                for i, widget in enumerate(app.topLevelWidgets()):
                    has_session_manager = hasattr(widget, "session_manager")
                    with open(debug_file, "a") as f:
                        f.write(
                            f"Widget {i}: {type(widget).__name__} - has session_manager: {has_session_manager}\n"
                        )

                    if has_session_manager:
                        main_window = widget
                        break

                if main_window and hasattr(main_window, "session_manager"):
                    session_manager = main_window.session_manager

                    with open(debug_file, "a") as f:
                        f.write(
                            f"SESSION MANAGER FOUND: {type(session_manager).__name__}\n"
                        )
                        f.write(
                            f"Has current_session attr: {hasattr(session_manager, 'current_session')}\n"
                        )

                    if hasattr(session_manager, "current_session"):
                        current_session = session_manager.current_session

                        with open(debug_file, "a") as f:
                            f.write(f"current_session value: {current_session}\n")
                            f.write(f"current_session type: {type(current_session)}\n")

                        if current_session:
                            # Extract session ID
                            session_id = None
                            if isinstance(current_session, dict):
                                with open(debug_file, "a") as f:
                                    f.write(
                                        f"Dict keys: {list(current_session.keys())}\n"
                                    )

                                session_id = (
                                    current_session.get("session_id")
                                    or current_session.get("name")
                                    or current_session.get("id")
                                )

                                with open(debug_file, "a") as f:
                                    f.write(f"Extracted session_id: {session_id}\n")

                            elif isinstance(current_session, str):
                                session_id = current_session
                                with open(debug_file, "a") as f:
                                    f.write(f"String session_id: {session_id}\n")

                            if session_id:
                                self.current_session_id = session_id
                                self.status_label.setText(
                                    f"✅ Direct connection: {session_id}"
                                )
                                with open(debug_file, "a") as f:
                                    f.write(
                                        f"SUCCESS: Connected to session: {session_id}\n"
                                    )
                                    f.write("=" * 60 + "\n")
                            else:
                                self.status_label.setText(
                                    "❌ No session ID in current_session"
                                )
                                with open(debug_file, "a") as f:
                                    f.write("FAILED: No session ID found\n")
                                    f.write("=" * 60 + "\n")
                        else:
                            self.status_label.setText("❌ current_session is None")
                            with open(debug_file, "a") as f:
                                f.write("FAILED: current_session is None\n")
                                f.write("=" * 60 + "\n")
                    else:
                        self.status_label.setText("❌ No current_session attribute")
                        with open(debug_file, "a") as f:
                            f.write("FAILED: No current_session attribute\n")
                            f.write("=" * 60 + "\n")
                else:
                    self.status_label.setText("❌ No main window with session_manager")
                    with open(debug_file, "a") as f:
                        f.write("FAILED: No main window with session_manager found\n")
                        f.write("=" * 60 + "\n")

            except Exception as e:
                error_msg = f"DIRECT: Error finding session: {str(e)}"
                self.status_label.setText("❌ Direct search failed")
                with open(debug_file, "a") as f:
                    f.write(f"ERROR: {error_msg}\n")
                    f.write("=" * 60 + "\n")

        # DEBUG: Session validation
        with open("/tmp/autogen_debug.txt", "a") as f:
            f.write(
                f"[{datetime.now()}] Session ID check - current_session_id: '{self.current_session_id}'\n"
            )

        if not self.current_session_id:
            with open("/tmp/autogen_debug.txt", "a") as f:
                f.write(
                    f"[{datetime.now()}] ERROR: No session ID - showing warning dialog\n"
                )
            QMessageBox.warning(
                self, "No Session", "Please select a conversation session first."
            )
            return

        message_text = self.message_input.toPlainText().strip()
        with open("/tmp/autogen_debug.txt", "a") as f:
            f.write(
                f"[{datetime.now()}] Message text: '{message_text}' (length: {len(message_text)})\n"
            )

        if not message_text:
            with open("/tmp/autogen_debug.txt", "a") as f:
                f.write(f"[{datetime.now()}] ERROR: Empty message text - returning\n")
            return

        try:
            # Clear any previous error messages
            self.status_label.setText("📤 Sending message...")

            selected_agents = self.get_selected_agents()
            with open("/tmp/autogen_debug.txt", "a") as f:
                f.write(f"[{datetime.now()}] Selected agents: {selected_agents}\n")
                f.write(
                    f"[{datetime.now()}] MCP integration enabled: {self.use_mcp_integration}\n"
                )

            logger.info(f"Sending message with session_id: {self.current_session_id}")
            logger.info(f"Selected agents: {selected_agents}")
            logger.info(f"Message: {message_text[:50]}...")

            if selected_agents:
                with open("/tmp/autogen_debug.txt", "a") as f:
                    f.write(
                        f"[{datetime.now()}] TARGETED MESSAGE FLOW - creating targeted message\n"
                    )

                # Send targeted message to specific agents
                self.conversation_service.create_targeted_user_message(
                    session_id=self.current_session_id,
                    content=message_text,
                    target_agents=selected_agents,
                )

                # Use MCP integration if enabled
                if self.use_mcp_integration:
                    with open("/tmp/autogen_debug.txt", "a") as f:
                        f.write(f"[{datetime.now()}] Using MCP integration\n")
                    logger.info("Using MCP integration...")
                    self.status_label.setText("📡 Sending via MCP...")
                    success = self.conversation_service.send_message_via_mcp(
                        self.current_session_id, message_text, selected_agents, "user"
                    )
                    if not success:
                        with open("/tmp/autogen_debug.txt", "a") as f:
                            f.write(
                                f"[{datetime.now()}] MCP send failed, using local\n"
                            )
                        logger.warning("MCP send failed, using local")
                        self.status_label.setText("⚠️ MCP failed, using local...")
                        self.conversation_service.send_targeted_message_local(
                            self.current_session_id, message_text, selected_agents
                        )
                    else:
                        logger.info("MCP send successful")
                        self.status_label.setText("✅ Message sent via MCP")
                else:
                    logger.info("Using local messaging...")
                    self.status_label.setText("📨 Sending locally...")
                    self.conversation_service.send_targeted_message_local(
                        self.current_session_id, message_text, selected_agents
                    )
                    self.status_label.setText("✅ Message sent locally")
            else:
                with open("/tmp/autogen_debug.txt", "a") as f:
                    f.write(
                        f"[{datetime.now()}] ALL AGENTS MESSAGE FLOW - sending to all agents\n"
                    )
                logger.info("Sending to all agents...")
                self.status_label.setText("📨 Sending to all agents...")

                # Add debugging around the conversation service call
                with open("/tmp/autogen_debug.txt", "a") as f:
                    f.write(
                        f"[{datetime.now()}] About to call conversation_service.send_message\n"
                    )

                try:
                    # Send message to all agents
                    self.conversation_service.send_message(
                        self.current_session_id, message_text
                    )
                    with open("/tmp/autogen_debug.txt", "a") as f:
                        f.write(
                            f"[{datetime.now()}] conversation_service.send_message completed successfully\n"
                        )
                except Exception as service_error:
                    with open("/tmp/autogen_debug.txt", "a") as f:
                        f.write(
                            f"[{datetime.now()}] conversation_service.send_message FAILED: {str(service_error)}\n"
                        )
                    raise  # Re-raise the exception to be caught by outer try-catch

                with open("/tmp/autogen_debug.txt", "a") as f:
                    f.write(
                        f"[{datetime.now()}] Message sent to all agents - showing success\n"
                    )
                self.status_label.setText("✅ Message sent to all agents")

            # Clear the input and show success
            self.message_input.clear()
            logger.info("Message sent successfully, clearing input")

            # Show success dialog
            QMessageBox.information(
                self,
                "Message Sent",
                f"Message sent successfully!\nSession: {self.current_session_id}\nAgents: {', '.join(selected_agents) if selected_agents else 'All agents'}",
            )

            # Force refresh conversation after a short delay
            from PySide6.QtCore import QTimer

            QTimer.singleShot(1000, self.refresh_conversation)

        except Exception as e:
            error_msg = f"Failed to send message: {str(e)}"
            logger.error(error_msg)
            self.status_label.setText(f"❌ Send failed: {str(e)[:30]}...")
            QMessageBox.critical(self, "Send Failed", error_msg)

        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            self.status_label.setText(f"Error: {str(e)}")

    def refresh_conversation(self):
        """Refresh the conversation display by reloading messages from the service"""
        if not self.current_session_id:
            return

        try:
            # Get the latest conversation history from the service
            messages = self.conversation_service.get_conversation_history(
                self.current_session_id
            )

            # Clear the current display
            self.conversation_display.clear()

            # Redisplay all messages
            for message in messages:
                self.display_message(message)

            # Scroll to bottom to show latest messages
            scrollbar = self.conversation_display.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

            logger.info(
                f"Refreshed conversation for session {self.current_session_id} with {len(messages)} messages"
            )

        except Exception as e:
            logger.error(f"Failed to refresh conversation: {e}")
            self.status_label.setText(f"❌ Refresh failed: {str(e)[:30]}...")

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
            try:
                self.status_label.setText("🗑️ Clearing conversation...")
                self.conversation_display.clear()
                self.conversation_service.clear_conversation(self.current_session_id)
                self.status_label.setText("✅ Conversation cleared")

                # Show success message
                QMessageBox.information(
                    self,
                    "Conversation Cleared",
                    "The conversation has been cleared successfully!",
                )
            except Exception as e:
                error_msg = f"Failed to clear conversation: {str(e)}"
                logger.error(error_msg)
                self.status_label.setText("❌ Clear failed")
                QMessageBox.critical(self, "Clear Failed", error_msg)

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

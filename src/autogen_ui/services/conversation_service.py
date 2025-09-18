"""
Conversation Service for AutoGen UI
Handles message flow between conversation widgets and session management
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from PySide6.QtCore import QObject, Signal, QThread, QTimer

from .session_service import SessionService

logger = logging.getLogger(__name__)


@dataclass
class ConversationMessage:
    """Data class for conversation messages"""

    id: str
    session_id: str
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: str
    agent_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)


class ConversationWorker(QThread):
    """Worker thread for async conversation operations"""

    message_sent = Signal(str, str)  # session_id, message_id
    message_received = Signal(ConversationMessage)
    agent_typing = Signal(str, str)  # session_id, agent_name
    agent_stopped_typing = Signal(str, str)  # session_id, agent_name
    error_occurred = Signal(str, str)  # session_id, error_message

    def __init__(self, session_service: SessionService):
        super().__init__()
        self.session_service = session_service
        self.active_sessions: Dict[str, bool] = {}
        self.message_queue: List[Dict[str, Any]] = []
        self._running = False

    def run(self):
        """Main worker thread loop"""
        self._running = True
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(self._message_processing_loop())
        except Exception as e:
            logger.error(f"Conversation worker error: {e}")
        finally:
            loop.close()

    async def _message_processing_loop(self):
        """Process queued messages"""
        while self._running:
            if self.message_queue:
                message_data = self.message_queue.pop(0)
                try:
                    await self._send_message_to_session(message_data)
                except Exception as e:
                    self.error_occurred.emit(
                        message_data.get("session_id", ""),
                        f"Failed to send message: {str(e)}",
                    )

            await asyncio.sleep(0.1)  # Small delay to prevent busy waiting

    def send_message_to_session(self, message_data: dict):
        """Send message to session service"""
        # Extract session_id for future use
        session_id = message_data["session_id"]  # noqa: F841

        # Emit typing indicators for agents (simulate agent processing)
        QTimer.singleShot(
            500, lambda: self.typing_indicator_updated.emit("Agent 1", True)
        )
        QTimer.singleShot(
            2000, lambda: self.typing_indicator_updated.emit("Agent 1", False)
        )

        # TODO: Implement real session service communication
        # For now, emit a mock response
        mock_response = ConversationMessage(
            sender="Assistant",
            content="This is a mock response. Real session integration coming soon.",  # noqa: E501
            timestamp=datetime.now(),
            message_type="assistant",
        )

        # Simulate processing delay
        QTimer.singleShot(
            1500, lambda: self.message_received.emit(mock_response.to_dict())
        )

    def queue_message(self, session_id: str, message: str, agents: List[str] = None):
        """Queue a message for processing"""
        self.message_queue.append(
            {"session_id": session_id, "message": message, "agents": agents or []}
        )

    def stop_worker(self):
        """Stop the worker thread"""
        self._running = False


class ConversationService(QObject):
    """Service for managing conversation flow and integration"""

    # Signals
    message_added = Signal(ConversationMessage)
    message_sent = Signal(str, str)  # session_id, message_id
    agent_typing_started = Signal(str, str)  # session_id, agent_name
    agent_typing_stopped = Signal(str, str)  # session_id, agent_name
    conversation_cleared = Signal(str)  # session_id
    conversation_exported = Signal(str, str)  # session_id, file_path
    error_occurred = Signal(str, str)  # session_id, error_message

    def __init__(self, session_service: SessionService):
        super().__init__()
        self.session_service = session_service
        self.conversations: Dict[str, List[ConversationMessage]] = {}
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

        # Initialize worker thread
        self.worker = ConversationWorker(session_service)
        self._connect_worker_signals()
        self.worker.start()

    def _connect_worker_signals(self):
        """Connect worker thread signals"""
        self.worker.message_sent.connect(self.message_sent.emit)
        self.worker.message_received.connect(self._on_message_received)
        self.worker.agent_typing.connect(self.agent_typing_started.emit)
        self.worker.agent_stopped_typing.connect(self.agent_typing_stopped.emit)
        self.worker.error_occurred.connect(self.error_occurred.emit)

    def _on_message_received(self, message: ConversationMessage):
        """Handle received message from worker"""
        self.add_message_to_conversation(message)
        self.message_added.emit(message)

    def start_conversation(self, session_id: str, session_config: Dict[str, Any]):
        """Start a new conversation for a session"""
        self.active_sessions[session_id] = session_config
        self.conversations[session_id] = []

        # Add welcome message
        welcome_message = ConversationMessage(
            id=f"welcome_{session_id}",
            session_id=session_id,
            role="system",
            content=f"Session '{session_config.get('name', 'Unknown')}' started with agents: {', '.join(session_config.get('agents', []))}",
            timestamp=datetime.now().strftime("%H:%M:%S"),
        )

        self.add_message_to_conversation(welcome_message)
        self.message_added.emit(welcome_message)

        logger.info(f"Started conversation for session {session_id}")

    def send_message(self, session_id: str, message: str) -> str:
        """Send a user message to the conversation"""
        if session_id not in self.active_sessions:
            raise ValueError(f"No active session {session_id}")

        # Create user message
        message_id = f"user_{datetime.now().timestamp()}"
        user_message = ConversationMessage(
            id=message_id,
            session_id=session_id,
            role="user",
            content=message,
            timestamp=datetime.now().strftime("%H:%M:%S"),
        )

        # Add to conversation immediately
        self.add_message_to_conversation(user_message)
        self.message_added.emit(user_message)

        # Queue for processing by agents
        session_config = self.active_sessions[session_id]
        agents = session_config.get("agents", [])
        self.worker.queue_message(session_id, message, agents)

        self.message_sent.emit(session_id, message_id)
        logger.info(f"Sent message to session {session_id}: {message[:50]}...")

        return message_id

    def add_message_to_conversation(self, message: ConversationMessage):
        """Add a message to the conversation history"""
        if message.session_id not in self.conversations:
            self.conversations[message.session_id] = []

        self.conversations[message.session_id].append(message)

    def get_conversation(self, session_id: str) -> List[ConversationMessage]:
        """Get conversation history for a session"""
        return self.conversations.get(session_id, []).copy()

    def clear_conversation(self, session_id: str):
        """Clear conversation history for a session"""
        if session_id in self.conversations:
            self.conversations[session_id] = []
            self.conversation_cleared.emit(session_id)
            logger.info(f"Cleared conversation for session {session_id}")

    def end_conversation(self, session_id: str):
        """End conversation for a session"""
        if session_id in self.active_sessions:
            # Add goodbye message
            goodbye_message = ConversationMessage(
                id=f"goodbye_{session_id}",
                session_id=session_id,
                role="system",
                content=f"Session '{self.active_sessions[session_id].get('name', 'Unknown')}' ended.",
                timestamp=datetime.now().strftime("%H:%M:%S"),
            )

            self.add_message_to_conversation(goodbye_message)
            self.message_added.emit(goodbye_message)

            # Clean up session
            del self.active_sessions[session_id]
            logger.info(f"Ended conversation for session {session_id}")

    def export_conversation(
        self, session_id: str, file_path: str, format: str = "json"
    ) -> bool:
        """Export conversation to file"""
        try:
            conversation = self.get_conversation(session_id)
            if not conversation:
                raise ValueError("No conversation to export")

            if format.lower() == "json":
                self._export_to_json(conversation, file_path)
            elif format.lower() == "markdown":
                self._export_to_markdown(conversation, file_path)
            else:
                raise ValueError(f"Unsupported export format: {format}")

            self.conversation_exported.emit(session_id, file_path)
            logger.info(f"Exported conversation {session_id} to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export conversation {session_id}: {e}")
            self.error_occurred.emit(session_id, f"Export failed: {str(e)}")
            return False

    def _export_to_json(self, conversation: List[ConversationMessage], file_path: str):
        """Export conversation to JSON format"""
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "message_count": len(conversation),
            "messages": [msg.to_dict() for msg in conversation],
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

    def _export_to_markdown(
        self, conversation: List[ConversationMessage], file_path: str
    ):
        """Export conversation to Markdown format"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("# Conversation Export\n\n")
            f.write(f"**Exported:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Messages:** {len(conversation)}\n\n")
            f.write("---\n\n")

            for msg in conversation:
                role_display = msg.role.title()
                if msg.agent_name:
                    role_display = f"{msg.agent_name} ({role_display})"

                f.write(f"## {role_display} - {msg.timestamp}\n\n")
                f.write(f"{msg.content}\n\n")
                f.write("---\n\n")

    def get_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Get all active conversation sessions"""
        return self.active_sessions.copy()

    def is_session_active(self, session_id: str) -> bool:
        """Check if a session has an active conversation"""
        return session_id in self.active_sessions

    def cleanup(self):
        """Clean up the service"""
        if hasattr(self, "worker") and self.worker.isRunning():
            self.worker.stop_worker()
            self.worker.wait(3000)  # Wait up to 3 seconds for thread to finish
        logger.info("ConversationService cleaned up")

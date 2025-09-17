"""
Session Service for AutoGen UI
Manages session orchestration with MCP server
"""

import logging
from typing import Dict, Any, List, Optional
import httpx
from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)


class SessionService(QObject):
    """Service for managing AutoGen sessions"""

    # Signals
    session_started = Signal(str, dict)  # session_id, session_info
    session_stopped = Signal(str)  # session_id
    session_error = Signal(str, str)  # session_id, error_message

    def __init__(self, server_url: str):
        super().__init__()
        self.server_url = server_url.rstrip("/")
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

    async def start_session(
        self,
        project: str,
        agents: List[str],
        objective: str,
        working_directory: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Start a new session with working directory support"""
        try:
            request_data = {
                "project": project,
                "agents": agents,
                "objective": objective,
            }

            if working_directory:
                request_data["working_directory"] = working_directory

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.server_url}/orchestrate/start",
                    json=request_data,
                    timeout=30.0,
                )
                response.raise_for_status()

                result = response.json()
                session_id = result.get("session_id")

                if session_id:
                    # Store session info
                    session_info = {
                        "session_id": session_id,
                        "project": project,
                        "agents": agents,
                        "objective": objective,
                        "working_directory": working_directory,
                        "status": result.get("status", "active"),
                    }
                    self.active_sessions[session_id] = session_info

                    # Emit signal
                    self.session_started.emit(session_id, session_info)

                    logger.info(f"Session {session_id} started successfully")
                    return result
                else:
                    raise ValueError("No session_id in response")

        except Exception as e:
            error_msg = f"Failed to start session: {str(e)}"
            logger.error(error_msg)
            self.session_error.emit("", error_msg)
            raise

    async def stop_session(self, session_id: str) -> Dict[str, Any]:
        """Stop a running session"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.server_url}/orchestrate/stop",
                    json={"session_id": session_id},
                    timeout=30.0,
                )
                response.raise_for_status()

                result = response.json()

                # Remove from active sessions
                if session_id in self.active_sessions:
                    del self.active_sessions[session_id]

                # Emit signal
                self.session_stopped.emit(session_id)

                logger.info(f"Session {session_id} stopped successfully")
                return result

        except Exception as e:
            error_msg = f"Failed to stop session {session_id}: {str(e)}"
            logger.error(error_msg)
            self.session_error.emit(session_id, error_msg)
            raise

    async def list_sessions(self) -> List[Dict[str, Any]]:
        """List all sessions"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.server_url}/orchestrate/sessions", timeout=15.0
                )
                response.raise_for_status()

                result = response.json()
                sessions = result.get("sessions", [])

                # Update local cache
                for session in sessions:
                    session_id = session.get("session_id")
                    if session_id:
                        self.active_sessions[session_id] = session

                logger.info(f"Listed {len(sessions)} sessions")
                return sessions

        except Exception as e:
            error_msg = f"Failed to list sessions: {str(e)}"
            logger.error(error_msg)
            raise

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get cached session information"""
        return self.active_sessions.get(session_id)

    def get_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Get all cached active sessions"""
        return self.active_sessions.copy()

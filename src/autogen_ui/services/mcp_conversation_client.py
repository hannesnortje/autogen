"""
MCP Client for Enhanced Conversation System
Handles communication between UI conversation service and MCP server
"""

import asyncio
import logging
from typing import Dict, List, Optional
import aiohttp

logger = logging.getLogger(__name__)


class MCPConversationClient:
    """Client for communicating with MCP server conversation endpoints"""

    def __init__(self, base_url: str = "http://127.0.0.1:9000"):
        self.base_url = base_url.rstrip("/")
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        """Close the HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None

    async def send_message(
        self,
        session_id: str,
        content: str,
        target_agents: Optional[List[str]] = None,
        message_type: str = "user",
    ) -> Dict:
        """Send a message through the MCP server"""
        try:
            session = await self._get_session()
            payload = {
                "session_id": session_id,
                "content": content,
                "target_agents": target_agents,
                "message_type": message_type,
            }

            async with session.post(
                f"{self.base_url}/conversation/send", json=payload
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Message sent via MCP: {result}")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"MCP send message failed: {error_text}")
                    raise Exception(f"MCP server error: {error_text}")

        except Exception as e:
            logger.error(f"Failed to send message via MCP: {e}")
            raise

    async def add_agent_interaction(
        self,
        session_id: str,
        source_agent: str,
        target_agent: str,
        content: str,
        interaction_type: str = "agent_to_agent",
    ) -> Dict:
        """Record agent-to-agent interaction"""
        try:
            session = await self._get_session()
            payload = {
                "session_id": session_id,
                "source_agent": source_agent,
                "target_agent": target_agent,
                "content": content,
                "interaction_type": interaction_type,
            }

            async with session.post(
                f"{self.base_url}/conversation/agent-interaction", json=payload
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Agent interaction recorded: {result}")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"MCP agent interaction failed: {error_text}")
                    raise Exception(f"MCP server error: {error_text}")

        except Exception as e:
            logger.error(f"Failed to record agent interaction: {e}")
            raise

    async def get_conversation_history(
        self, session_id: str, limit: Optional[int] = None
    ) -> List[Dict]:
        """Get conversation history from MCP server"""
        try:
            session = await self._get_session()
            params = {"limit": limit} if limit else {}

            url = f"{self.base_url}/conversation/{session_id}/history"
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    msg_count = len(result["messages"])
                    logger.info(
                        f"Retrieved {msg_count} messages for session {session_id}"
                    )
                    return result["messages"]
                else:
                    error_text = await response.text()
                    logger.error(f"MCP get history failed: {error_text}")
                    raise Exception(f"MCP server error: {error_text}")

        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            raise

    async def clear_conversation(self, session_id: str) -> Dict:
        """Clear conversation history"""
        try:
            session = await self._get_session()

            async with session.delete(
                f"{self.base_url}/conversation/{session_id}"
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Conversation cleared: {result}")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"MCP clear conversation failed: {error_text}")
                    raise Exception(f"MCP server error: {error_text}")

        except Exception as e:
            logger.error(f"Failed to clear conversation: {e}")
            raise

    async def start_agent_typing(self, session_id: str, agent_name: str) -> Dict:
        """Indicate agent started typing"""
        try:
            session = await self._get_session()

            async with session.post(
                f"{self.base_url}/conversation/{session_id}/typing/start",
                params={"agent_name": agent_name},
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.debug(f"Agent typing started: {result}")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"MCP start typing failed: {error_text}")
                    raise Exception(f"MCP server error: {error_text}")

        except Exception as e:
            logger.error(f"Failed to start agent typing: {e}")
            raise

    async def stop_agent_typing(self, session_id: str, agent_name: str) -> Dict:
        """Indicate agent stopped typing"""
        try:
            session = await self._get_session()

            async with session.post(
                f"{self.base_url}/conversation/{session_id}/typing/stop",
                params={"agent_name": agent_name},
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.debug(f"Agent typing stopped: {result}")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"MCP stop typing failed: {error_text}")
                    raise Exception(f"MCP server error: {error_text}")

        except Exception as e:
            logger.error(f"Failed to stop agent typing: {e}")
            raise

    async def get_session_agents(self, session_id: str) -> List[str]:
        """Get available agents for a session"""
        try:
            session = await self._get_session()

            async with session.get(
                f"{self.base_url}/conversation/{session_id}/agents"
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Session agents: {result['agents']}")
                    return result["agents"]
                else:
                    error_text = await response.text()
                    logger.error(f"MCP get session agents failed: {error_text}")
                    raise Exception(f"MCP server error: {error_text}")

        except Exception as e:
            logger.error(f"Failed to get session agents: {e}")
            raise

    async def get_conversation_stats(self) -> Dict:
        """Get conversation system statistics"""
        try:
            session = await self._get_session()

            async with session.get(f"{self.base_url}/conversation/stats") as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Conversation stats: {result}")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"MCP get stats failed: {error_text}")
                    raise Exception(f"MCP server error: {error_text}")

        except Exception as e:
            logger.error(f"Failed to get conversation stats: {e}")
            raise

    # Synchronous wrappers for Qt integration
    def send_message_sync(
        self,
        session_id: str,
        content: str,
        target_agents: Optional[List[str]] = None,
        message_type: str = "user",
    ) -> Dict:
        """Synchronous wrapper for send_message"""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(
                self.send_message(session_id, content, target_agents, message_type)
            )
        except RuntimeError:
            # Create new event loop if none exists
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    self.send_message(session_id, content, target_agents, message_type)
                )
            finally:
                loop.close()

    def get_conversation_history_sync(
        self, session_id: str, limit: Optional[int] = None
    ) -> List[Dict]:
        """Synchronous wrapper for get_conversation_history"""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(
                self.get_conversation_history(session_id, limit)
            )
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    self.get_conversation_history(session_id, limit)
                )
            finally:
                loop.close()

    def get_session_agents_sync(self, session_id: str) -> List[str]:
        """Synchronous wrapper for get_session_agents"""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.get_session_agents(session_id))
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.get_session_agents(session_id))
            finally:
                loop.close()

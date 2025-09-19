"""
Simple Agent Memory Service - Bridge between AutoGen agents and memory system.
Provides memory operations for agent conversations, decisions, and context.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from autogen_mcp.multi_memory import MultiScopeMemoryService, MemoryWriteOptions
from autogen_mcp.memory_collections import CollectionManager, MemoryScope


@dataclass
class AgentContext:
    """Context information for an agent in a conversation turn."""

    agent_id: str
    agent_name: str
    agent_role: str
    session_id: str
    conversation_id: str
    turn_number: int
    timestamp: datetime


@dataclass
class ConversationTurn:
    """Represents a single conversation turn by an agent."""

    context: AgentContext
    input_message: str
    output_message: str
    reasoning: Optional[str] = None
    decisions_made: List[str] = None
    resources_used: List[str] = None

    def __post_init__(self):
        if self.decisions_made is None:
            self.decisions_made = []
        if self.resources_used is None:
            self.resources_used = []


class SimpleAgentMemoryService:
    """
    Simple service that connects AutoGen agents with the memory system.
    Uses the correct MemoryWriteOptions interface.
    """

    def __init__(self, collection_manager: CollectionManager):
        self.collection_manager = collection_manager
        self.memory_service = MultiScopeMemoryService(collection_manager)

        # Initialize the memory service
        try:
            self.memory_service.initialize()
        except Exception as e:
            print(f"Memory initialization warning: {e}")

        self.active_conversations: Dict[str, Dict[str, Any]] = {}

    def start_agent_conversation(
        self,
        agent_id: str,
        agent_name: str,
        agent_role: str,
        session_id: str,
        initial_objective: Optional[str] = None,
    ) -> str:
        """Start a new conversation thread for an agent."""
        conversation_id = str(uuid.uuid4())

        self.active_conversations[conversation_id] = {
            "agent_id": agent_id,
            "agent_name": agent_name,
            "agent_role": agent_role,
            "session_id": session_id,
            "turn_count": 0,
            "started_at": datetime.now(timezone.utc),
            "initial_objective": initial_objective,
        }

        # Write conversation start to memory
        options = MemoryWriteOptions(
            scope=MemoryScope.THREAD,
            thread_id=conversation_id,
            session_id=session_id,
            agent_type=agent_role,
        )

        content = f"Agent {agent_name} ({agent_role}) started conversation in session {session_id}"

        self.memory_service.write_event(
            content=content,
            options=options,
            metadata={
                "message_type": "system",
                "conversation_start": True,
                "initial_objective": initial_objective or "No specific objective",
            },
        )

        return conversation_id

    def record_agent_turn(self, turn: ConversationTurn) -> str:
        """Record an agent's conversation turn in memory."""
        if turn.context.conversation_id not in self.active_conversations:
            raise ValueError(f"Conversation {turn.context.conversation_id} not found")

        # Update conversation metadata
        conv = self.active_conversations[turn.context.conversation_id]
        conv["turn_count"] += 1
        conv["last_turn_at"] = datetime.now(timezone.utc)

        # Prepare turn data for memory
        turn_content = f"""Agent: {turn.context.agent_name} ({turn.context.agent_role})
Turn: {turn.context.turn_number}
Input: {turn.input_message}
Output: {turn.output_message}"""

        if turn.reasoning:
            turn_content += f"\nReasoning: {turn.reasoning}"

        # Write to thread memory
        thread_options = MemoryWriteOptions(
            scope=MemoryScope.THREAD,
            thread_id=turn.context.conversation_id,
            session_id=turn.context.session_id,
            agent_type=turn.context.agent_role,
        )

        event_id = self.memory_service.write_event(
            content=turn_content,
            options=thread_options,
            metadata={
                "message_type": "agent_response",
                "turn_number": turn.context.turn_number,
                "decisions_made": turn.decisions_made,
                "resources_used": turn.resources_used,
            },
        )

        return event_id

    def get_agent_context(
        self,
        agent_role: str,
        conversation_id: str,
        query: Optional[str] = None,
        max_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant context for an agent from memory."""
        try:
            # Get recent conversation history
            results = self.memory_service.search(
                query=query or f"conversation {agent_role}",
                scope="thread",
                limit=max_results,
            )
            return results or []
        except Exception as e:
            print(f"Context retrieval error: {e}")
            return []

    def record_agent_decision(
        self,
        agent_id: str,
        agent_name: str,
        agent_role: str,
        decision: str,
        reasoning: str,
        context: str,
        conversation_id: Optional[str] = None,
    ) -> str:
        """Record a significant decision made by an agent."""
        decision_content = f"""Agent Decision by {agent_name} ({agent_role}):
Decision: {decision}
Reasoning: {reasoning}
Context: {context}"""

        agent_options = MemoryWriteOptions(
            scope=MemoryScope.AGENT, agent_type=agent_role, session_id=conversation_id
        )

        event_id = self.memory_service.write_event(
            content=decision_content,
            options=agent_options,
            metadata={
                "capability": "decision_making",
                "decision_type": "contextual",
                "agent_id": agent_id,
                "source_conversation": conversation_id,
            },
        )

        return event_id

    def end_agent_conversation(
        self, conversation_id: str, summary: Optional[str] = None
    ) -> Optional[str]:
        """End an agent conversation and create a summary record."""
        if conversation_id not in self.active_conversations:
            return None

        conv = self.active_conversations[conversation_id]

        summary_content = f"""Conversation Summary:
Agent: {conv["agent_name"]} ({conv["agent_role"]})
Session: {conv["session_id"]}
Total turns: {conv.get("turn_count", 0)}
Initial objective: {conv.get("initial_objective", "None specified")}"""

        if summary:
            summary_content += f"\nSummary: {summary}"

        # Write summary to memory
        options = MemoryWriteOptions(
            scope=MemoryScope.THREAD,
            thread_id=conversation_id,
            session_id=conv["session_id"],
            agent_type=conv["agent_role"],
        )

        event_id = self.memory_service.write_event(
            content=summary_content,
            options=options,
            metadata={
                "message_type": "system",
                "conversation_status": "completed",
                "turn_count": conv.get("turn_count", 0),
            },
        )

        # Remove from active conversations
        del self.active_conversations[conversation_id]

        return event_id

    def get_agent_performance_insights(
        self, agent_role: str, limit: int = 10
    ) -> Dict[str, Any]:
        """Get performance insights for a specific agent role."""
        try:
            results = self.memory_service.search(
                query=f"agent_type:{agent_role}", scope="agent", limit=limit
            )

            insights = {
                "agent_role": agent_role,
                "total_interactions": len(results),
                "decision_patterns": [],
                "recent_performance": results[:5] if results else [],
            }

            return insights
        except Exception as e:
            return {"error": f"Failed to get insights: {e}"}


# Use SimpleAgentMemoryService as AgentMemoryService for compatibility
AgentMemoryService = SimpleAgentMemoryService

"""
AgentMemoryService - Bridge between AutoGen agents and memory system.
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


class AgentMemoryService:
    """
    Service layer that connects AutoGen agents with the memory system.
    Handles agent-specific memory operations, context management, and conversation history.
    """

    def __init__(self, collection_manager: CollectionManager):
        self.collection_manager = collection_manager
        self.memory_service = MultiScopeMemoryService(collection_manager)
        self.active_conversations: Dict[str, Dict[str, Any]] = {}

    def start_agent_conversation(
        self,
        agent_id: str,
        agent_name: str,
        agent_role: str,
        session_id: str,
        initial_objective: Optional[str] = None,
    ) -> str:
        """
        Start a new conversation thread for an agent.
        Returns conversation_id for tracking.
        """
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

        event_data = {
            "type": "conversation_start",
            "agent_id": agent_id,
            "agent_name": agent_name,
            "agent_role": agent_role,
            "session_id": session_id,
            "conversation_id": conversation_id,
            "initial_objective": initial_objective or "No specific objective",
        }

        self.memory_service.write_event(
            content=f"Agent {agent_name} ({agent_role}) started conversation in session {session_id}",
            options=options,
            metadata={
                "message_type": "system",
                **event_data,
            },
        )

        return conversation_id

    def record_agent_turn(self, turn: ConversationTurn) -> str:
        """
        Record an agent's conversation turn in memory.
        Returns the event ID for the recorded turn.
        """
        if turn.context.conversation_id not in self.active_conversations:
            raise ValueError(f"Conversation {turn.context.conversation_id} not found")

        # Update conversation metadata
        conv = self.active_conversations[turn.context.conversation_id]
        conv["turn_count"] += 1
        conv["last_turn_at"] = datetime.now(timezone.utc)

        # Prepare turn data for memory
        turn_content = f"""
Agent: {turn.context.agent_name} ({turn.context.agent_role})
Turn: {turn.context.turn_number}

Input: {turn.input_message}

Output: {turn.output_message}
"""

        if turn.reasoning:
            turn_content += f"\nReasoning: {turn.reasoning}"

        if turn.decisions_made:
            turn_content += f"\nDecisions Made: {', '.join(turn.decisions_made)}"

        if turn.resources_used:
            turn_content += f"\nResources Used: {', '.join(turn.resources_used)}"

        # Write to thread memory
        event_id = self.memory_service.write_event(
            content=turn_content,
            event_type="agent_turn",
            scope=MemoryScope.THREAD,
            metadata={
                "thread_id": turn.context.conversation_id,
                "message_type": "agent_response",
                "agent_id": turn.context.agent_id,
                "agent_name": turn.context.agent_name,
                "agent_role": turn.context.agent_role,
                "session_id": turn.context.session_id,
                "turn_number": turn.context.turn_number,
                "decisions_made": turn.decisions_made,
                "resources_used": turn.resources_used,
            },
        )

        # Also write agent-specific learning to agent memory
        if turn.reasoning or turn.decisions_made:
            agent_learning_content = f"""
Agent {turn.context.agent_name} learning from turn {turn.context.turn_number}:

Context: {turn.input_message}
Response approach: {turn.output_message}
"""
            if turn.reasoning:
                agent_learning_content += f"\nReasoning process: {turn.reasoning}"

            if turn.decisions_made:
                agent_learning_content += (
                    f"\nDecision patterns: {', '.join(turn.decisions_made)}"
                )

            self.memory_service.write_event(
                content=agent_learning_content,
                event_type="agent_learning",
                scope=MemoryScope.AGENT,
                metadata={
                    "agent_type": turn.context.agent_role,
                    "capability": "conversation_handling",
                    "skill_level": "active_learning",
                    "preference_type": "response_patterns",
                    "source_conversation": turn.context.conversation_id,
                    "source_turn": turn.context.turn_number,
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
        """
        Retrieve relevant context for an agent from memory.
        Combines conversation history, agent-specific knowledge, and relevant memories.
        """
        context_results = []

        # 1. Get recent conversation history from this thread
        thread_results = self.memory_service.search(
            query=f"conversation_id:{conversation_id} OR thread_id:{conversation_id}",
            scope="thread",
            limit=10,
        )
        if thread_results:
            context_results.extend(thread_results)

        # 2. Get agent-specific knowledge and patterns
        agent_results = self.memory_service.search(
            query=f"agent_type:{agent_role}" + (f" {query}" if query else ""),
            scope="agent",
            limit=max_results,
        )
        if agent_results:
            context_results.extend(agent_results)

        # 3. If a specific query is provided, search broader memory
        if query:
            global_results = self.memory_service.search(
                query=query, scope="global", limit=max_results
            )
            if global_results:
                context_results.extend(global_results)

        # Sort by relevance score (if available) or timestamp
        context_results.sort(
            key=lambda x: (
                x.get("score", 0.0),
                x.get("metadata", {}).get("timestamp", "2000-01-01"),
            ),
            reverse=True,
        )

        return context_results[
            : max_results * 2
        ]  # Return up to 2x max to ensure good coverage

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
        """
        Record a significant decision made by an agent.
        This goes to agent-specific memory for future learning.
        """
        decision_content = f"""
Agent Decision by {agent_name} ({agent_role}):

Decision: {decision}
Reasoning: {reasoning}
Context: {context}
"""

        event_id = self.memory_service.write_event(
            content=decision_content,
            event_type="agent_decision",
            scope=MemoryScope.AGENT,
            metadata={
                "agent_type": agent_role,
                "capability": "decision_making",
                "skill_level": "applied",
                "preference_type": "decision_patterns",
                "decision_type": "contextual",
                "agent_id": agent_id,
                "source_conversation": conversation_id,
            },
        )

        return event_id

    def end_agent_conversation(
        self, conversation_id: str, summary: Optional[str] = None
    ) -> str:
        """
        End an agent conversation and create a summary record.
        """
        if conversation_id not in self.active_conversations:
            raise ValueError(f"Conversation {conversation_id} not found")

        conv = self.active_conversations[conversation_id]

        # Generate summary content
        summary_content = f"""
Conversation Summary:
Agent: {conv["agent_name"]} ({conv["agent_role"]})
Session: {conv["session_id"]}
Duration: {conv.get("started_at", "Unknown")} - {datetime.now(timezone.utc)}
Total turns: {conv.get("turn_count", 0)}
Initial objective: {conv.get("initial_objective", "None specified")}
"""

        if summary:
            summary_content += f"\nSummary: {summary}"

        # Write conversation end to memory
        event_id = self.memory_service.write_event(
            content=summary_content,
            event_type="conversation_summary",
            scope=MemoryScope.THREAD,
            metadata={
                "thread_id": conversation_id,
                "message_type": "system",
                "agent_id": conv["agent_id"],
                "agent_name": conv["agent_name"],
                "agent_role": conv["agent_role"],
                "session_id": conv["session_id"],
                "turn_count": conv.get("turn_count", 0),
                "conversation_status": "completed",
            },
        )

        # Remove from active conversations
        del self.active_conversations[conversation_id]

        return event_id

    def get_agent_performance_insights(
        self, agent_role: str, limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get performance insights and patterns for a specific agent role.
        """
        # Search for agent decisions and learnings
        results = self.memory_service.search(
            query=f"agent_type:{agent_role} (agent_decision OR agent_learning)",
            scope="agent",
            limit=limit,
        )

        insights = {
            "agent_role": agent_role,
            "total_interactions": len(results),
            "decision_patterns": [],
            "learning_patterns": [],
            "recent_performance": results[:5] if results else [],
        }

        # Analyze patterns
        for result in results:
            event_type = result.get("metadata", {}).get("event_type", "")
            content = result.get("content", "")

            if event_type == "agent_decision":
                # Extract decision patterns
                if "Decision:" in content:
                    decision_text = content.split("Decision:")[1].split("\n")[0].strip()
                    insights["decision_patterns"].append(decision_text)

            elif event_type == "agent_learning":
                # Extract learning patterns
                if "Reasoning process:" in content:
                    reasoning_text = (
                        content.split("Reasoning process:")[1].split("\n")[0].strip()
                    )
                    insights["learning_patterns"].append(reasoning_text)

        return insights

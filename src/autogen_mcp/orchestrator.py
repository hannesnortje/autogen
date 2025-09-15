"""
Agent orchestrator for AutoGen MCP.
Coordinates agent lifecycles and integrates Gemini completions with memory.
"""

import uuid
from typing import List, Dict, Any, Optional
from autogen_mcp.agents import create_agent
from autogen_mcp.gemini_client import GeminiClient
from autogen_mcp.simple_agent_memory import AgentMemoryService
from autogen_mcp.collections import CollectionManager


class AgentOrchestrator:
    def __init__(
        self,
        agent_configs: List[Dict[str, Any]],
        gemini_client: GeminiClient,
        collection_manager: Optional[CollectionManager] = None,
    ):
        self.gemini = gemini_client
        self.collection_manager = collection_manager
        self.memory_service = None

        # Initialize memory service if collection manager available
        if collection_manager:
            self.memory_service = AgentMemoryService(collection_manager)

        # Create agents with memory service
        self.agents = [
            create_agent(
                cfg["role"],
                cfg["name"],
                cfg.get("config"),
                memory_service=self.memory_service,
            )
            for cfg in agent_configs
        ]

        self.current_session_id: Optional[str] = None
        self.session_objective: Optional[str] = None

    def start_session(self, objective: str) -> str:
        """
        Start a new orchestration session with memory tracking.
        Returns session_id for tracking this orchestration.
        """
        self.current_session_id = str(uuid.uuid4())
        self.session_objective = objective

        # Start conversations for all agents
        for agent in self.agents:
            agent.start_conversation(self.current_session_id, objective)

        return self.current_session_id

    def run_turn(self, prompt: str, session_id: Optional[str] = None) -> Dict[str, str]:
        """
        Run a single turn for all agents, using Gemini for completions and memory context.
        """
        # Ensure we have a session
        if not session_id and not self.current_session_id:
            self.start_session(f"Ad-hoc session: {prompt[:50]}...")

        working_session_id = session_id or self.current_session_id

        results = {}
        for agent in self.agents:
            # Get Gemini completion with agent-specific context
            agent_prompt = f"[{agent.role}] {prompt}"

            # Add context if this is a memory-enabled agent
            if (
                hasattr(agent, "current_conversation_id")
                and agent.current_conversation_id
            ):
                # Agent will get context automatically in act_with_memory
                pass

            # Get completion from Gemini
            completion = self.gemini.complete(agent_prompt)

            # Let the agent process with memory
            if hasattr(agent, "act_with_memory"):
                response = agent.act_with_memory(
                    observation=prompt,
                    session_id=working_session_id,
                    reasoning=f"Using Gemini completion: {completion}",
                    decisions_made=[f"Responded to: {prompt}"],
                    resources_used=["gemini_completion"],
                )
            else:
                # Fallback for agents without memory
                response = agent.act(prompt)

            agent.observe(completion)
            results[agent.name] = response

        return results

    def run_multi_turn_session(
        self, initial_prompt: str, num_turns: int = 3, objective: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Run a multi-turn session where agents can build on each other's responses.
        """
        session_objective = objective or f"Multi-turn session: {initial_prompt}"
        session_id = self.start_session(session_objective)

        all_results = []
        current_prompt = initial_prompt

        for turn in range(num_turns):
            turn_results = self.run_turn(current_prompt, session_id)
            all_results.append(turn_results)

            # Prepare next turn prompt based on current results
            if turn < num_turns - 1:  # Not the last turn
                current_prompt = f"Building on the previous responses: {list(turn_results.values())[0]}"

        return all_results

    def end_session(self, summary: Optional[str] = None) -> Dict[str, Any]:
        """
        End the current session and gather summaries from all agents.
        """
        if not self.current_session_id:
            return {"error": "No active session to end"}

        agent_summaries = {}
        performance_insights = {}

        for agent in self.agents:
            # End agent conversation
            summary_id = agent.end_conversation(summary)
            agent_summaries[agent.name] = summary_id

            # Get performance insights
            insights = agent.get_performance_insights()
            performance_insights[agent.name] = insights

        session_summary = {
            "session_id": self.current_session_id,
            "objective": self.session_objective,
            "agent_summaries": agent_summaries,
            "performance_insights": performance_insights,
            "ended_at": f"Session ended with summary: {summary or 'No summary provided'}",
        }

        self.current_session_id = None
        self.session_objective = None

        return session_summary

    def get_session_status(self) -> Dict[str, Any]:
        """
        Get current session status and agent information.
        """
        return {
            "session_id": self.current_session_id,
            "objective": self.session_objective,
            "agents": [
                {
                    "name": agent.name,
                    "role": agent.role,
                    "agent_id": getattr(agent, "agent_id", "unknown"),
                    "conversation_id": getattr(agent, "current_conversation_id", None),
                    "turn_count": getattr(agent, "turn_counter", 0),
                }
                for agent in self.agents
            ],
            "memory_enabled": self.memory_service is not None,
        }


# Example usage (to be replaced with CLI or server integration)
if __name__ == "__main__":

    agent_configs = [
        {"role": "Agile", "name": "agile1"},
        {"role": "Planner", "name": "planner1"},
        {"role": "Coder", "name": "coder1"},
    ]
    gemini = GeminiClient()
    orchestrator = AgentOrchestrator(agent_configs, gemini)
    prompt = "Summarize the next sprint goal in one sentence."
    results = orchestrator.run_turn(prompt)
    for name, output in results.items():
        print(f"{name}: {output}")

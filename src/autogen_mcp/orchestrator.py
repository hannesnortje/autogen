"""
Agent orchestrator for AutoGen MCP.
Coordinates agent lifecycles and integrates Gemini completions with memory.
Enhanced with comprehensive knowledge management capabilities.
"""

import uuid
from typing import List, Dict, Any, Optional
from autogen_mcp.agents import create_agent
from autogen_mcp.gemini_client import GeminiClient
from autogen_mcp.simple_agent_memory import AgentMemoryService
from autogen_mcp.memory_collections import CollectionManager
from autogen_mcp.knowledge_management import (
    KnowledgeManagementService,
    KnowledgeManagementConfig,
)
from autogen_mcp.multi_memory import MultiScopeMemoryService


class AgentOrchestrator:
    def __init__(
        self,
        agent_configs: List[Dict[str, Any]],
        gemini_client: GeminiClient,
        collection_manager: Optional[CollectionManager] = None,
        knowledge_config: Optional[KnowledgeManagementConfig] = None,
    ):
        self.gemini = gemini_client
        self.collection_manager = collection_manager
        self.memory_service = None
        self.knowledge_management = None

        # Initialize memory service if collection manager available
        if collection_manager:
            self.memory_service = AgentMemoryService(collection_manager)

            # Initialize knowledge management system
            multi_memory_service = MultiScopeMemoryService(collection_manager)
            self.knowledge_management = KnowledgeManagementService(
                multi_memory_service, collection_manager, knowledge_config
            )

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

            # Handle file writing if agent returned structured file data
            if isinstance(response, dict) and response.get("action") == "file_creation":
                self._handle_file_creation(response, working_session_id)

        return results

    def _handle_file_creation(self, agent_response: dict, session_id: str) -> None:
        """
        Handle file creation from agent responses by calling the workspace
        write endpoint.
        """
        import requests
        import os

        files = agent_response.get("files", [])
        agent_name = agent_response.get("agent", "Unknown")

        for file_info in files:
            filename = file_info.get("filename")
            content = file_info.get("content")

            if filename and content:
                try:
                    # Get workspace path and project name
                    workspace_path = os.getenv("MCP_WORKSPACE", os.getcwd())
                    project_name = os.path.basename(workspace_path)

                    # Call the write endpoint
                    write_data = {
                        "file_path": filename,
                        "content": content,
                        "project": project_name,
                    }

                    response = requests.post(
                        "http://127.0.0.1:9000/workspace/write",
                        json=write_data,
                        timeout=10,
                    )

                    if response.status_code == 200:
                        print(f"[Orchestrator] {agent_name} created file: {filename}")
                    else:
                        print(
                            f"[Orchestrator] Failed to write {filename}: "
                            f"{response.text}"
                        )

                except Exception as e:
                    print(f"[Orchestrator] Error writing file {filename}: {str(e)}")

            else:
                print(
                    f"[Orchestrator] Invalid file data from {agent_name}: "
                    f"missing filename or content"
                )

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
            "knowledge_management_enabled": self.knowledge_management is not None,
        }

    def initialize_knowledge_system(
        self, project_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Initialize the knowledge management system."""
        if not self.knowledge_management:
            return {
                "error": "Knowledge management not available - no collection manager",
                "success": False,
            }

        return self.knowledge_management.initialize_knowledge_system(project_ids)

    def run_maintenance_cycle(self) -> Dict[str, Any]:
        """Run knowledge management maintenance cycle."""
        if not self.knowledge_management:
            return {
                "error": "Knowledge management not available",
                "success": False,
            }

        return self.knowledge_management.run_maintenance_cycle()

    def get_knowledge_system_health(self) -> Dict[str, Any]:
        """Get knowledge management system health."""
        if not self.knowledge_management:
            return {
                "error": "Knowledge management not available",
                "overall_status": "unavailable",
            }

        return self.knowledge_management.get_system_health()

    def export_knowledge(self, output_path: str) -> Dict[str, Any]:
        """Export system knowledge."""
        if not self.knowledge_management:
            return {"error": "Knowledge management not available", "success": False}

        return self.knowledge_management.export_system_knowledge(output_path)

    def import_knowledge(self, import_path: str) -> Dict[str, Any]:
        """Import system knowledge."""
        if not self.knowledge_management:
            return {"error": "Knowledge management not available", "success": False}

        return self.knowledge_management.import_system_knowledge(import_path)

    async def run_agile_project(
        self, target_dir: str, project_name: str, project_type: str = "file_system"
    ):
        """Run a comprehensive agile project.

        This integrates with the enhanced scrum agents to execute
        a complete agile project with multiple sprints, comprehensive
        planning, architecture, development, and testing.
        """
        from autogen_mcp.scrum_agents import create_major_agile_project

        print(f"🚀 Starting agile project: {project_name}")
        print(f"📁 Target directory: {target_dir}")
        print(f"🏗️  Project type: {project_type}")
        print()

        # Execute the agile project
        team = await create_major_agile_project(
            target_dir=target_dir, project_name=project_name, project_type=project_type
        )

        # Store project results in knowledge management if available
        if self.knowledge_management:
            project_summary = {
                "project_name": project_name,
                "project_type": project_type,
                "target_dir": target_dir,
                "team_size": len(team.all_members),
                "completion_status": "success",
            }

            # Store in knowledge base for future reference
            self.knowledge_management.add_project_insight(
                project_name,
                f"Completed agile project: {project_name}",
                project_summary,
            )

        return team


# Example usage (to be replaced with CLI or server integration)
if __name__ == "__main__":
    import asyncio

    async def demo_agile_project():
        """Demo the agile project functionality."""
        agent_configs = [
            {"role": "Agile", "name": "agile1"},
            {"role": "Planner", "name": "planner1"},
            {"role": "Coder", "name": "coder1"},
        ]

        # Create orchestrator without Gemini client for agile project demo
        try:
            gemini = GeminiClient()
            orchestrator = AgentOrchestrator(agent_configs, gemini)

            # Test basic agent interaction
            prompt = "Create an agile project for a Ranger file system"
            results = orchestrator.run_turn(prompt)
            for name, output in results.items():
                print(f"{name}: {output}")

        except RuntimeError as e:
            if "GEMINI_API_KEY" in str(e):
                print("⚠️  Gemini API key not set, running agile project directly...")
                orchestrator = AgentOrchestrator(agent_configs, None)

        # Test direct agile project creation (doesn't need Gemini)
        try:
            team = await orchestrator.run_agile_project(
                target_dir="/media/hannesn/storage/Code/Test",
                project_name="Ranger File System",
                project_type="file_system",
            )
            print(
                f"✅ Agile project completed with {len(team.all_members)} team members"
            )
        except Exception as e:
            print(f"❌ Error in agile project: {e}")
            import traceback

            traceback.print_exc()

    asyncio.run(demo_agile_project())

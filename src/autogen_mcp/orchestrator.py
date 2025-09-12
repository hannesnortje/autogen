"""
Agent orchestrator for AutoGen MCP.
Coordinates agent lifecycles and integrates Gemini completions.
"""

from typing import List, Dict, Any
from autogen_mcp.agents import create_agent
from autogen_mcp.gemini_client import GeminiClient


class AgentOrchestrator:
    def __init__(
        self, agent_configs: List[Dict[str, Any]], gemini_client: GeminiClient
    ):
        self.gemini = gemini_client
        self.agents = [
            create_agent(cfg["role"], cfg["name"], cfg.get("config"))
            for cfg in agent_configs
        ]

    def run_turn(self, prompt: str) -> Dict[str, str]:
        """Run a single turn for all agents, using Gemini for completions."""
        results = {}
        for agent in self.agents:
            # Each agent gets the same prompt for now; can be customized per agent
            completion = self.gemini.complete(f"[{agent.role}] {prompt}")
            agent.observe(completion)
            results[agent.name] = completion
        return results


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

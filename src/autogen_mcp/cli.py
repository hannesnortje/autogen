import argparse
from autogen_mcp.orchestrator import AgentOrchestrator
from autogen_mcp.gemini_client import GeminiClient
from autogen_mcp.agents import list_agent_roles

from dotenv import load_dotenv


def main():
    # Debug: print if GEMINI_API_KEY is loaded
    import os
    from pathlib import Path

    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
    print(f"[DEBUG] GEMINI_API_KEY loaded: {os.getenv('GEMINI_API_KEY') is not None}")
    parser = argparse.ArgumentParser(description="Run AutoGen MCP agent orchestrator.")
    parser.add_argument(
        "--prompt", type=str, required=True, help="Prompt for agents to process."
    )
    parser.add_argument(
        "--agents",
        type=str,
        nargs="*",
        default=["Agile", "Planner", "Coder"],
        help="Agent roles to run (default: Agile, Planner, Coder)",
        choices=list_agent_roles(),
    )
    args = parser.parse_args()

    agent_configs = [{"role": role, "name": role.lower()} for role in args.agents]
    gemini = GeminiClient()
    orchestrator = AgentOrchestrator(agent_configs, gemini)
    results = orchestrator.run_turn(args.prompt)
    for name, output in results.items():
        print(f"{name}: {output}")


if __name__ == "__main__":
    main()

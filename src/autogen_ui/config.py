"""
AutoGen UI Configuration
Simple configuration loading for the rebuilt UI
"""

import json
from pathlib import Path
from typing import Dict, Any, List


def load_config() -> Dict[str, Any]:
    """Load configuration from autogen.config.json"""
    config_path = Path(__file__).parent.parent.parent / "autogen.config.json"

    if config_path.exists():
        with open(config_path, "r") as f:
            config = json.load(f)
    else:
        # Default configuration
        config = {
            "ui": {
                "launch_mode": "auto",
                "theme": "system",
                "window_geometry": {"width": 1200, "height": 800},
                "auto_connect_server": True,
                "debug_mode": False,
            },
            "server": {
                "host": "127.0.0.1",
                "port": 9000,
                "log_level": "info",
                "enable_ui_endpoints": True,
                "auto_open_browser": False,
            },
            "agents": {"custom_agents": []},
        }

    return config


def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to autogen.config.json"""
    config_path = Path(__file__).parent.parent.parent / "autogen.config.json"

    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)


def load_custom_agents() -> List[Dict[str, Any]]:
    """Load custom agents from configuration"""
    config = load_config()
    return config.get("agents", {}).get("custom_agents", [])


def save_custom_agents(agents: List[Dict[str, Any]]) -> None:
    """Save custom agents to configuration"""
    config = load_config()

    # Ensure agents section exists
    if "agents" not in config:
        config["agents"] = {}

    config["agents"]["custom_agents"] = agents
    save_config(config)


def save_custom_agent(agent_config: Dict[str, Any]) -> None:
    """Save a single custom agent configuration"""
    agents = load_custom_agents()

    # Replace existing agent with same name or add new one
    existing_index = None
    for i, agent in enumerate(agents):
        if agent.get("name") == agent_config.get("name"):
            existing_index = i
            break

    if existing_index is not None:
        agents[existing_index] = agent_config
    else:
        agents.append(agent_config)

    save_custom_agents(agents)


def delete_custom_agent(agent_name: str) -> bool:
    """
    Delete a custom agent by name.
    Returns True if deleted, False if not found.
    """
    agents = load_custom_agents()
    original_count = len(agents)

    agents = [agent for agent in agents if agent.get("name") != agent_name]

    if len(agents) < original_count:
        save_custom_agents(agents)
        return True
    return False

"""
AutoGen UI Configuration
Simple configuration loading for the rebuilt UI
"""

import json
from pathlib import Path
from typing import Dict, Any


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
        }

    return config

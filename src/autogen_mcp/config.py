"""
AutoGen Configuration System

This module provides centralized configuration management for both
MCP server and UI components, including launch behavior control.
"""

import os
import json
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class UILaunchMode(Enum):
    """UI launch behavior options."""

    NEVER = "never"  # Never auto-launch UI
    AUTO = "auto"  # Always launch UI with server
    ON_DEMAND = "on_demand"  # Launch via API call or CLI flag
    VSCODE_ONLY = "vscode_only"  # Only when VSCode extension requests


@dataclass
class UIConfig:
    """UI-specific configuration."""

    launch_mode: UILaunchMode = UILaunchMode.NEVER
    theme: str = "system"
    window_geometry: Dict[str, int] = None
    auto_connect_server: bool = True
    debug_mode: bool = False

    def __post_init__(self):
        if self.window_geometry is None:
            self.window_geometry = {"width": 1200, "height": 800}


@dataclass
class ServerConfig:
    """MCP server configuration."""

    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "info"
    enable_ui_endpoints: bool = True
    auto_open_browser: bool = False


@dataclass
class AutoGenConfig:
    """Main AutoGen configuration."""

    ui: UIConfig = None
    server: ServerConfig = None
    integration_mode: str = "hybrid"  # direct, http, hybrid
    project_root: Path = None

    def __post_init__(self):
        if self.ui is None:
            self.ui = UIConfig()
        if self.server is None:
            self.server = ServerConfig()
        if self.project_root is None:
            self.project_root = Path(__file__).parent.parent.parent.parent


class ConfigManager:
    """Manages AutoGen configuration loading and saving."""

    DEFAULT_CONFIG_FILE = "autogen.config.json"

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path(self.DEFAULT_CONFIG_FILE)
        self._config: Optional[AutoGenConfig] = None

    def load_config(self) -> AutoGenConfig:
        """Load configuration from file or create default."""

        if self._config is not None:
            return self._config

        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    data = json.load(f)

                # Convert string enums back to enum values
                if "ui" in data and "launch_mode" in data["ui"]:
                    data["ui"]["launch_mode"] = UILaunchMode(data["ui"]["launch_mode"])

                # Create config object
                self._config = AutoGenConfig(
                    ui=UIConfig(**data.get("ui", {})),
                    server=ServerConfig(**data.get("server", {})),
                    integration_mode=data.get("integration_mode", "hybrid"),
                    project_root=Path(data.get("project_root", Path.cwd())),
                )

            except Exception as e:
                print(f"Warning: Failed to load config from {self.config_path}: {e}")
                print("Using default configuration")
                self._config = AutoGenConfig()
        else:
            # Create default config
            self._config = AutoGenConfig()
            self.save_config()  # Save defaults

        return self._config

    def save_config(self, config: Optional[AutoGenConfig] = None) -> None:
        """Save configuration to file."""

        config = config or self._config or AutoGenConfig()

        # Convert to dict for JSON serialization
        data = asdict(config)

        # Convert enum to string
        if "ui" in data and "launch_mode" in data["ui"]:
            data["ui"]["launch_mode"] = data["ui"]["launch_mode"].value

        # Convert Path to string
        if "project_root" in data:
            data["project_root"] = str(data["project_root"])

        try:
            with open(self.config_path, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            print(f"Warning: Failed to save config to {self.config_path}: {e}")

    def update_ui_launch_mode(self, mode: UILaunchMode) -> None:
        """Update UI launch mode and save."""

        config = self.load_config()
        config.ui.launch_mode = mode
        self.save_config(config)
        print(f"UI launch mode updated to: {mode.value}")

    def get_config(self) -> AutoGenConfig:
        """Get current configuration."""
        return self.load_config()


# Environment variable overrides
def apply_env_overrides(config: AutoGenConfig) -> AutoGenConfig:
    """Apply environment variable overrides to configuration."""

    # UI launch mode override
    ui_mode = os.getenv("AUTOGEN_UI_LAUNCH_MODE")
    if ui_mode:
        try:
            config.ui.launch_mode = UILaunchMode(ui_mode.lower())
        except ValueError:
            print(f"Warning: Invalid UI_LAUNCH_MODE '{ui_mode}', using config default")

    # Server config overrides
    if os.getenv("AUTOGEN_SERVER_PORT"):
        try:
            config.server.port = int(os.getenv("AUTOGEN_SERVER_PORT"))
        except ValueError:
            pass

    if os.getenv("AUTOGEN_SERVER_HOST"):
        config.server.host = os.getenv("AUTOGEN_SERVER_HOST")

    # Debug mode override
    if os.getenv("AUTOGEN_UI_DEBUG"):
        config.ui.debug_mode = os.getenv("AUTOGEN_UI_DEBUG").lower() in (
            "true",
            "1",
            "yes",
        )

    return config


# Global config instance
_config_manager = ConfigManager()


def get_config() -> AutoGenConfig:
    """Get the global AutoGen configuration."""
    config = _config_manager.load_config()
    return apply_env_overrides(config)


def update_ui_launch_mode(mode: UILaunchMode) -> None:
    """Update UI launch mode globally."""
    _config_manager.update_ui_launch_mode(mode)


def save_config(config: AutoGenConfig) -> None:
    """Save configuration globally."""
    _config_manager.save_config(config)

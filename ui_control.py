#!/usr/bin/env python3
"""
AutoGen UI Control - Simple CLI for managing UI launch behavior

Usage:
    python ui_control.py status                    # Show current UI mode
    python ui_control.py set never                 # Never auto-launch UI
    python ui_control.py set auto                  # Always auto-launch UI
    python ui_control.py set on_demand             # Launch only when requested
    python ui_control.py set vscode_only           # Launch only for VSCode
    python ui_control.py launch                    # Launch UI now (if server running)
"""

import sys
import argparse
import requests
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from autogen_mcp.config import get_config, update_ui_launch_mode, UILaunchMode


def show_status():
    """Show current configuration status."""
    config = get_config()

    print("=" * 50)
    print("AutoGen UI Configuration Status")
    print("=" * 50)
    print(f"UI Launch Mode:     {config.ui.launch_mode.value}")
    print(f"Server Host:        {config.server.host}")
    print(f"Server Port:        {config.server.port}")
    print(f"Theme:              {config.ui.theme}")
    print(f"Auto-connect:       {config.ui.auto_connect_server}")
    print(f"Debug Mode:         {config.ui.debug_mode}")
    print()

    # Test server connection
    try:
        response = requests.get(
            f"http://{config.server.host}:{config.server.port}/health", timeout=2
        )
        if response.status_code == 200:
            print("✅ MCP Server Status: Running")
        else:
            print(
                f"⚠️ MCP Server Status: Responding but unhealthy ({response.status_code})"
            )
    except requests.ConnectionError:
        print("❌ MCP Server Status: Not running")
    except Exception as e:
        print(f"❌ MCP Server Status: Error - {e}")


def set_ui_mode(mode_str: str):
    """Set the UI launch mode."""
    try:
        mode = UILaunchMode(mode_str)
        update_ui_launch_mode(mode)
        print(f"✅ UI launch mode updated to: {mode.value}")

        if mode == UILaunchMode.NEVER:
            print("   UI will never auto-launch with the server")
        elif mode == UILaunchMode.AUTO:
            print("   UI will always auto-launch when server starts")
        elif mode == UILaunchMode.ON_DEMAND:
            print("   UI will only launch when explicitly requested")
        elif mode == UILaunchMode.VSCODE_ONLY:
            print("   UI will only launch when requested by VSCode extension")

    except ValueError:
        print(f"❌ Invalid mode: {mode_str}")
        print("   Valid modes: never, auto, on_demand, vscode_only")
        return 1

    return 0


def launch_ui_now():
    """Launch the UI immediately (if server is running)."""
    config = get_config()

    # Check if server is running
    try:
        response = requests.get(
            f"http://{config.server.host}:{config.server.port}/health", timeout=2
        )
        if response.status_code != 200:
            print("❌ Cannot launch UI: MCP server not healthy")
            return 1

    except requests.ConnectionError:
        print("❌ Cannot launch UI: MCP server not running")
        print(
            f"   Start server first: poetry run uvicorn src.autogen_mcp.mcp_server:app --port {config.server.port}"
        )
        return 1
    except Exception as e:
        print(f"❌ Cannot check server status: {e}")
        return 1

    # Launch UI
    import subprocess

    try:
        print("🚀 Launching AutoGen Desktop UI...")
        subprocess.Popen([sys.executable, "src/autogen_ui/main.py"], cwd=project_root)
        print("✅ UI launch initiated")
        return 0

    except Exception as e:
        print(f"❌ Failed to launch UI: {e}")
        return 1


def main():
    """Main CLI entry point."""

    parser = argparse.ArgumentParser(
        description="AutoGen UI Control - Manage UI launch behavior",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ui_control.py status              # Show current configuration
  python ui_control.py set never           # Disable auto-launch
  python ui_control.py set auto            # Enable auto-launch
  python ui_control.py launch              # Launch UI now

UI Launch Modes:
  never       - Never auto-launch UI (manual only)
  auto        - Always launch UI when server starts
  on_demand   - Launch only when explicitly requested
  vscode_only - Launch only when VSCode extension requests
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Status command
    subparsers.add_parser("status", help="Show current UI configuration")

    # Set command
    set_parser = subparsers.add_parser("set", help="Set UI launch mode")
    set_parser.add_argument(
        "mode",
        choices=["never", "auto", "on_demand", "vscode_only"],
        help="UI launch mode",
    )

    # Launch command
    subparsers.add_parser("launch", help="Launch UI immediately")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "status":
        show_status()
        return 0
    elif args.command == "set":
        return set_ui_mode(args.mode)
    elif args.command == "launch":
        return launch_ui_now()

    return 1


if __name__ == "__main__":
    sys.exit(main())

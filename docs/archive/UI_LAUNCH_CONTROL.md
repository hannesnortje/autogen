# AutoGen UI Launch Control

## Overview

The AutoGen desktop UI is **completely optional** and configurable. By default, the UI **never auto-launches** when the MCP server starts. You have full control over when and how the UI appears.

## 🎛️ UI Launch Modes

| Mode | Behavior | Use Case |
|------|----------|----------|
| `never` *(default)* | UI never auto-launches | Server-only, API-only, VSCode extension usage |
| `auto` | UI always launches with server | Desktop-first workflow |
| `on_demand` | UI only launches when requested | Manual control, optional UI |
| `vscode_only` | UI only launches from VSCode | VSCode extension integration |

## 🚀 Quick Start

### Current Setup (UI Disabled by Default)

```bash
# Start MCP server only (no UI)
poetry run uvicorn src.autogen_mcp.mcp_server:app --port 8000

# Check current UI configuration
poetry run python ui_control.py status

# Start UI manually if needed
poetry run python src/autogen_ui/main.py
```

### Enable Auto-Launch UI

```bash
# Set UI to always launch with server
poetry run python ui_control.py set auto

# Now when you start the server, UI will auto-launch
poetry run python launch.py
```

### VSCode Extension Mode

```bash
# Set UI to only launch from VSCode extension
poetry run python ui_control.py set vscode_only

# UI will only appear when VSCode extension requests it
poetry run uvicorn src.autogen_mcp.mcp_server:app --port 8000
```

## 📋 Detailed Usage

### 1. Configuration Management

```bash
# Show current configuration
poetry run python ui_control.py status

# Set UI launch mode
poetry run python ui_control.py set never       # Never auto-launch
poetry run python ui_control.py set auto        # Always auto-launch
poetry run python ui_control.py set on_demand   # Manual launch only
poetry run python ui_control.py set vscode_only # VSCode extension only

# Launch UI immediately (if server running)
poetry run python ui_control.py launch
```

### 2. Unified Launcher

```bash
# Use configuration file settings
poetry run python launch.py

# Force server-only (ignore UI config)
poetry run python launch.py --server-only

# Force UI launch with server
poetry run python launch.py --with-ui

# Launch UI only (connect to existing server)
poetry run python launch.py --ui-only
```

### 3. Environment Variables

```bash
# Temporarily override UI mode
AUTOGEN_UI_LAUNCH_MODE=never poetry run python launch.py

# Override server settings
AUTOGEN_SERVER_PORT=8001 poetry run python launch.py

# Enable UI debug mode
AUTOGEN_UI_DEBUG=true poetry run python launch.py --with-ui
```

## 🔧 Integration Scenarios

### Scenario 1: API-Only Usage (Default)
```bash
# Server starts without UI
poetry run uvicorn src.autogen_mcp.mcp_server:app --port 8000

# UI mode: never (default)
# Perfect for: REST API clients, CLI tools, automated systems
```

### Scenario 2: VSCode Extension Usage
```bash
# Set VSCode-only mode
poetry run python ui_control.py set vscode_only

# Server runs without UI until VSCode requests it
poetry run uvicorn src.autogen_mcp.mcp_server:app --port 8000

# UI only appears when VSCode extension activates UI features
```

### Scenario 3: Desktop-First Workflow
```bash
# Enable auto-launch
poetry run python ui_control.py set auto

# Both server and UI start together
poetry run python launch.py

# Perfect for: desktop users, visual workflow management
```

### Scenario 4: Manual Control
```bash
# Set on-demand mode
poetry run python ui_control.py set on_demand

# Start server only
poetry run uvicorn src.autogen_mcp.mcp_server:app --port 8000

# Launch UI when needed
poetry run python ui_control.py launch
```

## 📁 Configuration File

The system creates `autogen.config.json` in the project root:

```json
{
  "ui": {
    "launch_mode": "never",
    "theme": "system",
    "window_geometry": {
      "width": 1200,
      "height": 800
    },
    "auto_connect_server": true,
    "debug_mode": false
  },
  "server": {
    "host": "127.0.0.1",
    "port": 8000,
    "log_level": "info",
    "enable_ui_endpoints": true,
    "auto_open_browser": false
  },
  "integration_mode": "hybrid",
  "project_root": "/path/to/autogen"
}
```

## 🎯 Best Practices

### For VSCode Extension Development
```bash
# Ensure UI doesn't interfere with VSCode workflow
poetry run python ui_control.py set vscode_only
```

### For Server Deployment
```bash
# Disable UI completely for production servers
poetry run python ui_control.py set never
poetry run uvicorn src.autogen_mcp.mcp_server:app --host 0.0.0.0 --port 8000
```

### For Desktop Development
```bash
# Enable UI for visual development workflow
poetry run python ui_control.py set auto
poetry run python launch.py
```

### For CI/CD and Testing
```bash
# Ensure no UI launches in automated environments
AUTOGEN_UI_LAUNCH_MODE=never poetry run python -m pytest
```

## 🔍 Status Checking

```bash
# Check everything
poetry run python ui_control.py status

# Output:
# ==================================================
# AutoGen UI Configuration Status
# ==================================================
# UI Launch Mode:     never
# Server Host:        127.0.0.1
# Server Port:        8000
# Theme:              system
# Auto-connect:       True
# Debug Mode:         False
#
# ✅ MCP Server Status: Running
```

## 🎉 Summary

The AutoGen UI is **completely optional and configurable**:

- ✅ **Default**: UI never auto-launches (perfect for VSCode extension)
- ✅ **Configurable**: 4 different launch modes to suit your workflow
- ✅ **Manual Control**: Launch UI anytime with simple commands
- ✅ **Environment Override**: Temporary mode changes via env vars
- ✅ **Status Monitoring**: Always know what's running and how it's configured

**Your VSCode extension will work perfectly** - the UI won't interfere unless you specifically configure it to appear!

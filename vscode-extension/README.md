# AutoGen MCP VS Code Extension

This VS Code extension provides integration with the AutoGen Model Context Protocol (MCP) server, enabling seamless AI agent orchestration directly within your development environment.

## Features

- **Agent Session Management**: Start and manage AutoGen sessions with multiple AI agents
- **Memory Search**: Search through project memory and context
- **Objective Management**: Add and track project objectives
- **Real-time Communication**: WebSocket support for live updates
- **Dashboard View**: Centralized dashboard for monitoring AutoGen activities

## Commands

- `AutoGen: Start Session` - Launch a new AutoGen session with selected agents
- `AutoGen: Stop Session` - Stop the current AutoGen session
- `AutoGen: Search Memory` - Search through stored project memory
- `AutoGen: Add Objective` - Add new objectives to the current project
- `AutoGen: Show Dashboard` - Open the AutoGen dashboard

## Configuration

Configure the extension in VS Code settings:

```json
{
  "autogen.serverUrl": "http://localhost:9000",
  "autogen.autoStart": false
}
```

## Requirements

- AutoGen MCP Server running (default: http://localhost:9000)
- VS Code 1.74.0 or higher

## Installation

1. Install the extension from the VS Code marketplace (coming soon)
2. Or install from VSIX: `code --install-extension autogen-mcp-0.1.0.vsix`

## Development

To run the extension in development mode:

1. Clone the repository
2. Run `npm install`
3. Press F5 to launch Extension Development Host
4. Test commands via Command Palette (Ctrl+Shift+P)

## Architecture

The extension communicates with the AutoGen MCP server via:
- HTTP REST API for commands and queries
- WebSocket for real-time updates and notifications

## License

MIT License - see LICENSE file for details

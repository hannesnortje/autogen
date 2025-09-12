# ADR-015: VS Code Extension Scaffold Architecture

## Status
Accepted

## Context
We need to create a VS Code extension that provides a user-friendly interface for interacting with the AutoGen MCP (Model Context Protocol) server. The extension should integrate seamlessly with VS Code's UI patterns and provide access to AutoGen functionality through command palette, tree views, and dashboard interfaces.

This addresses Step 16 of the VS Code Integration Plan, establishing the foundation for all subsequent extension features.

## Decision
We will create a TypeScript-based VS Code extension with the following architecture:

### Core Components
1. **Main Extension Module** (`extension.ts`)
   - Entry point with activate/deactivate lifecycle
   - Command registration and VS Code API integration
   - Status bar integration and basic dashboard

2. **MCP Client** (`mcpClient.ts`)
   - HTTP client for communicating with AutoGen MCP server
   - Typed interfaces for API requests/responses
   - Error handling and connection management

3. **Tree Data Providers**
   - `SessionProvider`: Manages AutoGen session tree view
   - `MemoryProvider`: Manages memory search results tree view
   - Both implement VS Code's TreeDataProvider interface

### Command Palette Integration
- `autogen.startSession`: Launch new AutoGen sessions
- `autogen.stopSession`: Stop active sessions
- `autogen.searchMemory`: Search project memory
- `autogen.addObjective`: Add project objectives
- `autogen.showDashboard`: Open dashboard webview
- `autogen.refreshSessions`: Refresh session tree
- `autogen.refreshMemory`: Refresh memory tree

### UI Integration
- Activity bar views for sessions and memory
- Status bar item showing AutoGen status
- Dashboard webview for centralized monitoring
- Command palette for quick access to functionality

### Development Environment
- TypeScript 4.9+ for type safety
- VS Code Extension API 1.104+
- Mocha testing framework
- VSCE for packaging and distribution
- Development host debugging configuration

## Implementation Details

### Extension Manifest (package.json)
```json
{
  "engines": { "vscode": "^1.104.0" },
  "activationEvents": ["onStartupFinished"],
  "main": "./out/extension.js",
  "contributes": {
    "commands": [...],
    "views": {
      "autogen": [
        { "id": "autogen.sessionView" },
        { "id": "autogen.memoryView" }
      ]
    },
    "configuration": {
      "properties": {
        "autogen.serverUrl": { "default": "http://localhost:9000" },
        "autogen.autoStart": { "default": false }
      }
    }
  }
}
```

### TypeScript Configuration
- Target ES2020 for modern JavaScript features
- Include DOM lib for fetch() and Web APIs
- Strict type checking enabled
- Source maps for debugging
- Modular architecture with clear separation

### Communication Protocol
- HTTP REST API for standard operations
- JSON request/response format
- Error handling with user-friendly messages
- Future WebSocket support for real-time updates

## Alternatives Considered

### 1. JavaScript vs TypeScript
- **Decision**: TypeScript
- **Rationale**: Better developer experience, type safety, and VS Code tooling support

### 2. Monolithic vs Modular Architecture
- **Decision**: Modular with separate providers
- **Rationale**: Better maintainability, testability, and follows VS Code extension patterns

### 3. HTTP vs WebSocket Communication
- **Decision**: Start with HTTP, add WebSocket later
- **Rationale**: Simpler initial implementation, WebSocket support planned for Step 17

### 4. Tree Views vs Custom Webviews
- **Decision**: Native tree views for sessions/memory
- **Rationale**: Better VS Code integration, consistent UX, less maintenance

## Consequences

### Positive
- **Native Integration**: Extension feels like part of VS Code
- **Type Safety**: TypeScript prevents runtime errors and improves development experience
- **Modular Design**: Easy to extend and maintain individual components
- **Standard Patterns**: Follows VS Code extension best practices
- **Development Ready**: Includes debugging, testing, and packaging infrastructure

### Negative
- **Initial Complexity**: More setup than simple scripts
- **VS Code Dependency**: Tied to VS Code's release cycle and API changes
- **TypeScript Overhead**: Compilation step required for development

### Neutral
- **Extension Size**: ~440KB packaged size is reasonable for functionality provided
- **Performance**: HTTP communication adds network latency but acceptable for user-initiated actions

## Testing Strategy
- Unit tests for core logic (McpClient, providers)
- Integration tests with mock MCP server
- Manual testing in Extension Development Host
- Automated packaging validation

## Future Considerations
- WebSocket integration for real-time updates (Step 17)
- Advanced dashboard with charts and metrics
- File operation integration with workspace
- Extension marketplace publication
- Auto-update mechanisms
- Telemetry and usage analytics

## References
- [VS Code Extension API](https://code.visualstudio.com/api)
- [Extension Development Guide](https://code.visualstudio.com/api/get-started/your-first-extension)
- [TreeDataProvider API](https://code.visualstudio.com/api/extension-guides/tree-view)
- [Webview API](https://code.visualstudio.com/api/extension-guides/webview)
- VSCODE_INTEGRATION_PLAN.md Step 16

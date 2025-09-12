# ADR-016: VS Code Extension Core Commands Implementation

## Status
Accepted

## Context
Following the VS Code extension scaffold (ADR-015), we need to implement the core commands that provide actual functionality for interacting with the AutoGen MCP server. These commands form the primary user interface for AutoGen functionality within VS Code.

This addresses Step 17 of the VS Code Integration Plan, implementing the essential commands for session management, memory search, and objective handling.

## Decision
We will implement a comprehensive command system with the following architecture:

### Core Commands Implemented
1. **Session Management**
   - `autogen.startSession`: Initialize new AutoGen sessions with agent selection
   - `autogen.stopSession`: Terminate active sessions with confirmation
   - `autogen.checkServerStatus`: Verify MCP server connectivity

2. **Memory Operations**
   - `autogen.searchMemory`: Search project memory with scope selection
   - `autogen.addObjective`: Add project objectives to memory

3. **User Interface**
   - `autogen.showDashboard`: Display interactive dashboard with real-time status
   - `autogen.refreshSessions`: Refresh session tree view
   - `autogen.refreshMemory`: Refresh memory tree view

### Enhanced MCP Client Architecture

#### Error Handling
```typescript
export class McpServerError extends Error {
    constructor(
        message: string,
        public statusCode?: number,
        public response?: any
    ) {
        super(message);
        this.name = 'McpServerError';
    }
}
```

#### Connection Management
- Centralized HTTP request handling with `makeRequest<T>()` method
- Server availability checking with `isServerAvailable()`
- Session state management with `getCurrentSessionId()` / `setCurrentSessionId()`
- Comprehensive error parsing and user-friendly messages

#### Request/Response Types
- Strongly typed interfaces for all API interactions
- `OrchestrationRequest/Response` for session management
- `MemorySearchRequest/Response` for memory operations
- `ObjectiveRequest` for objective management
- `SessionInfo` for session details

### User Experience Enhancements

#### Input Validation
- Multi-step input flows with validation
- Required field checking with helpful error messages
- Agent selection with multi-pick support
- Search scope selection (project/session/global)

#### Progress Indication
- VS Code Progress API integration for long-running operations
- Detailed progress messages during session start/stop
- Loading indicators for search and objective operations

#### Error Communication
- Contextual error messages with specific failure reasons
- Server connectivity checks before command execution
- Graceful handling of server unavailability
- Distinction between network errors and application errors

#### Status Bar Integration
- Real-time connection status display
- Active session indicator with session ID
- Quick access to dashboard via status bar click
- Visual state changes (Ready/Active/Disconnected)

### Dashboard Implementation

#### Interactive Webview
- Real-time server status display
- Quick action buttons for common operations
- Command reference with descriptions
- VS Code theme integration with CSS variables

#### Webview Communication
- Message passing between webview and extension
- Action buttons trigger extension commands
- Status updates reflected in dashboard
- Responsive design for different panel sizes

## Implementation Details

### Command Flow Architecture
```
User Action → Command Registration → Input Validation → Server Check →
API Call → Progress Display → Result Handling → UI Update
```

### Session Management Flow
1. **Start Session**: Check existing session → Agent selection → Objective input → API call → Status update
2. **Stop Session**: Confirm action → API call → Session cleanup → Status update

### Memory Operations Flow
1. **Search Memory**: Query input → Scope selection → API call → Results formatting → Document display
2. **Add Objective**: Project detection → Objective input → API call → Confirmation

### Error Handling Strategy
- **Network Errors**: Generic connectivity messages with server URL
- **HTTP Errors**: Parse response body for detailed error messages
- **Validation Errors**: Immediate feedback during input
- **Server Errors**: Specific error messages from MCP server responses

## Technical Decisions

### 1. Centralized HTTP Client vs Direct Fetch
- **Decision**: Centralized McpClient with makeRequest method
- **Rationale**: Consistent error handling, request configuration, and maintainability

### 2. Session State Management
- **Decision**: Client-side session tracking with server verification
- **Rationale**: Immediate UI updates while maintaining server consistency

### 3. Progress Indication Pattern
- **Decision**: VS Code Progress API for all async operations
- **Rationale**: Native VS Code UX patterns and user feedback

### 4. Error Message Strategy
- **Decision**: User-friendly messages with technical details in logs
- **Rationale**: Better user experience while maintaining debuggability

### 5. Input Validation Approach
- **Decision**: Real-time validation during input with helper text
- **Rationale**: Immediate feedback prevents user errors

## Alternatives Considered

### 1. Command Implementation Strategy
- **Alternative**: Single command with subcommand parameters
- **Decision**: Multiple specific commands
- **Rationale**: Better VS Code integration, clearer command palette, easier discovery

### 2. Error Handling Approach
- **Alternative**: Global error handler with generic messages
- **Decision**: Context-specific error handling per command
- **Rationale**: More helpful error messages and better user experience

### 3. Status Management
- **Alternative**: Poll server for status updates
- **Decision**: Event-driven status updates
- **Rationale**: Better performance and user experience

### 4. Dashboard Technology
- **Alternative**: TreeView-based dashboard
- **Decision**: Webview with HTML/CSS/JS
- **Rationale**: More flexible UI, better visual design, interactive elements

## Consequences

### Positive
- **Rich User Experience**: Comprehensive input validation, progress indication, and error handling
- **Robust Error Handling**: Graceful degradation when server unavailable
- **Type Safety**: Strongly typed API interfaces prevent runtime errors
- **Extensible Architecture**: Easy to add new commands and functionality
- **Native Integration**: Follows VS Code UX patterns and conventions

### Negative
- **Increased Complexity**: More code to maintain than simple command implementations
- **Network Dependency**: Commands require active MCP server connection
- **Error Surface**: More potential failure points with enhanced functionality

### Neutral
- **Bundle Size**: ~65KB compiled TypeScript is reasonable for functionality
- **Performance**: HTTP requests add latency but acceptable for user-initiated actions

## Testing Strategy
- Unit tests for McpClient methods and error handling
- Integration tests for command execution flows
- Manual testing with VS Code Extension Development Host
- Error scenario testing (server unavailable, invalid inputs)

## Future Considerations
- WebSocket integration for real-time session updates (Step 19)
- Workspace integration for automatic project detection (Step 20)
- Command history and favorites
- Batch operations for multiple sessions/objectives
- Settings UI for server configuration
- Keyboard shortcuts for frequently used commands

## Configuration

### Extension Settings
```json
{
  "autogen.serverUrl": {
    "type": "string",
    "default": "http://localhost:9000",
    "description": "AutoGen MCP server URL"
  },
  "autogen.autoStart": {
    "type": "boolean",
    "default": false,
    "description": "Auto-start server checking on extension activation"
  }
}
```

### Command Contributions
All commands registered with VS Code command system under "AutoGen" category for easy discovery in Command Palette.

## References
- [VS Code Command API](https://code.visualstudio.com/api/references/vscode-api#commands)
- [VS Code Progress API](https://code.visualstudio.com/api/references/vscode-api#Progress)
- [VS Code Webview API](https://code.visualstudio.com/api/extension-guides/webview)
- VSCODE_INTEGRATION_PLAN.md Step 17
- ADR-015: VS Code Extension Scaffold Architecture

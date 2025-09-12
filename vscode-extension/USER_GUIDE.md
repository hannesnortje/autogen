# AutoGen MCP VS Code Extension - User Guide

This guide provides comprehensive documentation for using the AutoGen MCP VS Code extension's UI components.

## Table of Contents
1. [Getting Started](#getting-started)
2. [Session Tree View](#session-tree-view)
3. [Memory Explorer Panel](#memory-explorer-panel)
4. [Status Bar Integration](#status-bar-integration)
5. [Agent Configuration Panel](#agent-configuration-panel)
6. [Smart Command Palette](#smart-command-palette)
7. [Session Dashboard](#session-dashboard)
8. [Keyboard Shortcuts](#keyboard-shortcuts)
9. [Configuration](#configuration)
10. [Troubleshooting](#troubleshooting)

## Getting Started

### Prerequisites
- VS Code 1.74.0 or higher
- AutoGen MCP server running and accessible
- Node.js for extension development (if building from source)

### Initial Setup
1. Install the extension in VS Code
2. Open the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`)
3. Run `AutoGen MCP: Check Server Status` to verify connection
4. Configure server settings if needed (see [Configuration](#configuration))

### First Use
1. Start with `AutoGen MCP: Show Dashboard` to get an overview
2. Use `AutoGen MCP: Start Session` to create your first session
3. Explore the Session Tree View in the Explorer sidebar
4. Access the Memory Explorer via `AutoGen MCP: Open Memory Explorer`

## Session Tree View

The Session Tree View provides a hierarchical display of AutoGen sessions and their agents in VS Code's Explorer sidebar.

### Features
- **Session Hierarchy**: Sessions are displayed as top-level items with expandable agent lists
- **Status Indicators**: Visual indicators for session status (active 🟢, stopped 🔴, error 🟡)
- **Agent Details**: Each agent shows its role and current status
- **Context Menus**: Right-click for session and agent management options

### Usage
- **View Sessions**: Sessions appear automatically in the Explorer sidebar under "AutoGen Sessions"
- **Expand Session**: Click the arrow to view agents within a session
- **Open Dashboard**: Click on a session name to open its dashboard
- **Agent Actions**: Right-click on agents for role-specific actions
- **Refresh**: Use the refresh button to update session data

### Context Menu Options

#### Session Context Menu
- **Open Dashboard**: View detailed session information and controls
- **Stop Session**: Safely terminate an active session
- **Archive Session**: Move completed session to archived state
- **Export Session**: Export session data and conversation history
- **Delete Session**: Permanently remove session (with confirmation)

#### Agent Context Menu
- **View Agent Details**: Open agent configuration and status
- **Send Direct Message**: Communicate directly with specific agent
- **View Agent Memory**: Filter memory explorer to this agent
- **Configure Agent**: Modify agent settings and parameters
- **Remove Agent**: Remove agent from session

## Memory Explorer Panel

The Memory Explorer provides advanced capabilities for exploring and managing agent memories across all sessions.

### Features
- **Advanced Search**: Full-text search across all memory types with regex support
- **Multi-Filter System**: Filter by memory type, date range, session, and agent
- **Export Capabilities**: Export filtered memories in JSON or CSV format
- **Batch Operations**: Select multiple memories for bulk actions
- **Timeline View**: Visualize memory creation over time

### Opening the Memory Explorer
- Command Palette: `AutoGen MCP: Open Memory Explorer`
- Status Bar: Click the memory count indicator
- Session Dashboard: Click "Explore Memories" button

### Search and Filtering

#### Search Options
- **Basic Search**: Type in the search box for simple text matching
- **Regex Search**: Use `/pattern/flags` for advanced pattern matching
- **Case Sensitivity**: Toggle case-sensitive search with the Aa button

#### Filter Types
- **Memory Type**: Filter by conversation, code, error, or custom types
- **Date Range**: Set start and end dates for temporal filtering
- **Session Filter**: Limit to specific sessions
- **Agent Filter**: Show only memories from specific agents
- **Tag Filter**: Filter by custom tags (if implemented)

### Memory Operations

#### Individual Memory Actions
- **View Details**: Click memory item to expand full content
- **Copy Content**: Copy memory content to clipboard
- **Tag Memory**: Add custom tags for organization
- **Delete Memory**: Remove individual memory items
- **Link Memory**: Create relationships between memories

#### Batch Operations
- **Select Multiple**: Use checkboxes to select multiple memories
- **Bulk Export**: Export selected memories to file
- **Bulk Delete**: Remove multiple memories at once
- **Bulk Tag**: Apply tags to multiple memories

### Export Options
- **JSON Format**: Complete memory data with metadata
- **CSV Format**: Tabular format for spreadsheet analysis
- **Markdown**: Human-readable format for documentation
- **Custom Format**: Define your own export template

## Status Bar Integration

The Status Bar provides real-time information about AutoGen server status and quick access to common operations.

### Status Bar Items

#### Server Status (Rightmost)
- **🟢 Connected**: Server is accessible and responding
- **🔴 Disconnected**: Cannot reach AutoGen MCP server
- **🟡 Error**: Server responded with error
- **Click Action**: Check server status and show details

#### Session Information
- **Active Sessions**: Shows count of currently active sessions
- **Format**: "Sessions: 3 active"
- **Click Action**: Focus on Session Tree View

#### Agent Count
- **Total Agents**: Shows count of agents across all sessions
- **Format**: "Agents: 12 (4 roles)"
- **Click Action**: Open agent summary view

#### Quick Actions (Leftmost)
- **AutoGen Button**: Quick access to common operations
- **Click Action**: Shows menu with frequently used commands

### Auto-Refresh
- Status items automatically update every 30 seconds
- Manual refresh available via right-click menu
- Configurable refresh interval in settings

## Agent Configuration Panel

The Agent Configuration Panel provides a comprehensive interface for creating and managing AutoGen agents.

### Opening the Panel
- Command Palette: `AutoGen MCP: Configure Agents`
- Session Dashboard: Click "Configure Agents" button
- Session Tree: Right-click agent → "Configure Agent"

### Agent Templates
Pre-configured templates for common agent roles:

#### Built-in Templates
- **Coder**: Focused on writing and generating code
- **Reviewer**: Specialized in code review and quality assurance
- **Tester**: Creates and executes test suites
- **Architect**: Designs system architecture and patterns
- **DevOps**: Handles deployment and infrastructure
- **Security**: Focuses on security analysis and best practices
- **Documentation**: Specializes in writing technical documentation

### Configuration Options

#### Basic Settings
- **Agent Name**: Unique identifier for the agent
- **Display Name**: Human-readable name shown in UI
- **Role**: Agent's primary function and responsibility
- **Description**: Detailed description of agent capabilities

#### Advanced Settings
- **System Message**: Core instructions that define agent behavior
- **Temperature**: Creativity/randomness in responses (0.0-2.0)
- **Max Tokens**: Maximum response length
- **Model Selection**: Choose specific LLM model for agent
- **Memory Settings**: Configure memory access and retention

#### Tool Configuration
- **Available Tools**: Select which tools agent can access
- **Tool Restrictions**: Limit tool usage by context or permissions
- **Custom Tools**: Define agent-specific tools and functions

### Validation and Testing
- **Real-time Validation**: Configuration errors highlighted immediately
- **Preview Mode**: Test agent responses with sample inputs
- **Compatibility Check**: Verify agent works with selected models
- **Export/Import**: Save and share agent configurations

## Smart Command Palette

The Smart Command Palette enhances VS Code's native command palette with AutoGen-specific commands and intelligent parameter collection.

### Enhanced Commands

#### Smart Session Commands
- **Start Session with Parameters**: Guided session creation with validation
- **Search Memory Advanced**: Multi-parameter memory search
- **Add Objective Advanced**: Structured objective definition
- **Stop Session Advanced**: Graceful session termination with options

### Parameter Collection

#### Intelligent Defaults
- **Workspace Detection**: Automatically suggests project-related values
- **Context Awareness**: Uses current file/selection for defaults
- **History Integration**: Suggests previously used values
- **Validation**: Real-time validation with helpful error messages

#### Parameter Types
- **String Input**: Text input with validation and suggestions
- **Number Input**: Numeric input with range validation
- **Choice Selection**: Single selection from predefined options
- **Multi-Choice**: Multiple selections with dependency handling
- **File/Folder Picker**: File system navigation with filtering

### Usage Examples

#### Starting a Session
1. Run `AutoGen MCP: Start Session with Parameters`
2. **Project Name**: Auto-filled from workspace name
3. **Agents**: Multi-select from template list (Coder, Reviewer, etc.)
4. **Objective**: Required text input with minimum length validation
5. **Advanced Options**: Optional settings for experienced users

#### Advanced Memory Search
1. Run `AutoGen MCP: Search Memory Advanced`
2. **Query**: Text input with regex support toggle
3. **Memory Types**: Multi-select filter options
4. **Date Range**: Start and end date pickers
5. **Session Filter**: Dropdown of available sessions

## Session Dashboard

The Session Dashboard provides a comprehensive control panel for managing AutoGen sessions with real-time data visualization.

### Opening the Dashboard
- Command Palette: `AutoGen MCP: Show Dashboard`
- Session Tree: Click on session name
- Status Bar: Click session count indicator

### Dashboard Sections

#### Statistics Overview
- **Session Metrics**: Total sessions, active count, completion rate
- **Agent Activity**: Agent utilization, role distribution, performance metrics
- **Memory Statistics**: Total memories, types breakdown, growth trends
- **Performance Data**: Response times, success rates, error frequency

#### Quick Actions Grid
- **Start New Session**: Launch session creation wizard
- **Configure Agents**: Open agent configuration panel
- **Explore Memories**: Open memory explorer with filters
- **View Logs**: Access system and agent logs
- **Export Data**: Bulk export of session and memory data
- **System Health**: View server status and diagnostics

#### Active Sessions
- **Session Cards**: Visual representation of each active session
- **Real-time Updates**: Live status and agent activity indicators
- **Quick Controls**: Start, stop, pause session actions
- **Agent Overview**: Agent count and status per session

#### Workspace Information
- **Project Context**: Current workspace and file information
- **Git Integration**: Branch status and recent commits
- **File Activity**: Recently modified files and change detection
- **Extension Status**: AutoGen extension health and configuration

### Interactive Features
- **Clickable Elements**: All statistics and cards are interactive
- **Drill-down Navigation**: Click to access detailed views
- **Real-time Updates**: Dashboard refreshes automatically
- **Responsive Layout**: Adapts to VS Code window size

## Keyboard Shortcuts

### Default Shortcuts
- `Ctrl+Shift+A` (`Cmd+Shift+A`): Show AutoGen Dashboard
- `Ctrl+Shift+M` (`Cmd+Shift+M`): Open Memory Explorer
- `Ctrl+Shift+S` (`Cmd+Shift+S`): Start New Session
- `Ctrl+Shift+T` (`Cmd+Shift+T`): Focus Session Tree View

### Session Tree Shortcuts
- `Enter`: Open session dashboard / Expand agent list
- `Space`: Toggle session expansion
- `Delete`: Delete selected session (with confirmation)
- `F2`: Rename session
- `Ctrl+R` (`Cmd+R`): Refresh tree view

### Memory Explorer Shortcuts
- `Ctrl+F` (`Cmd+F`): Focus search box
- `Ctrl+E` (`Cmd+E`): Toggle export panel
- `Ctrl+A` (`Cmd+A`): Select all memories
- `Delete`: Delete selected memories
- `Escape`: Clear search and filters

### Customizing Shortcuts
1. Open VS Code Keyboard Shortcuts (`Ctrl+K Ctrl+S`)
2. Search for "autogen" to find all extension commands
3. Click pencil icon to customize shortcuts
4. Save changes (automatically applied)

## Configuration

### Extension Settings
Access via: File → Preferences → Settings → Extensions → AutoGen MCP

#### Server Configuration
- **Server URL**: AutoGen MCP server endpoint (default: http://localhost:8000)
- **API Key**: Authentication key for server access
- **Timeout**: Request timeout in milliseconds (default: 30000)
- **Retry Attempts**: Number of retry attempts for failed requests (default: 3)

#### UI Preferences
- **Auto Refresh Interval**: How often to update UI data (default: 30 seconds)
- **Tree View Depth**: Maximum depth for session tree expansion
- **Memory Page Size**: Number of memories to load per page (default: 50)
- **Theme Integration**: Use VS Code theme colors for panels

#### Feature Toggles
- **Show Status Bar**: Enable/disable status bar items
- **Auto Session Refresh**: Automatically refresh session data
- **Memory Auto-load**: Load memories in background
- **Advanced Commands**: Show advanced command palette options

### Workspace Settings
Configure per-workspace in `.vscode/settings.json`:

```json
{
    "autogen-mcp.server.url": "http://localhost:8000",
    "autogen-mcp.ui.autoRefreshInterval": 30,
    "autogen-mcp.features.showStatusBar": true,
    "autogen-mcp.memory.pageSize": 100
}
```

### Environment Variables
- `AUTOGEN_MCP_SERVER_URL`: Override server URL
- `AUTOGEN_MCP_API_KEY`: Set API key for authentication
- `AUTOGEN_MCP_DEBUG`: Enable debug logging

## Troubleshooting

### Common Issues

#### Server Connection Problems
**Symptoms**: Red status bar, "Disconnected" messages, command failures

**Solutions**:
1. Verify AutoGen MCP server is running
2. Check server URL in settings
3. Verify network connectivity
4. Review server logs for errors
5. Try manual connection test: `AutoGen MCP: Check Server Status`

#### Session Tree Not Loading
**Symptoms**: Empty session tree, loading indicators

**Solutions**:
1. Refresh tree view manually (refresh button)
2. Check server connection status
3. Verify permissions for session access
4. Clear extension cache: `AutoGen MCP: Clear Cache`
5. Restart VS Code if issues persist

#### Memory Explorer Performance
**Symptoms**: Slow loading, UI freezing, timeout errors

**Solutions**:
1. Reduce memory page size in settings
2. Use more specific search filters
3. Clear memory cache periodically
4. Check available system memory
5. Consider archiving old sessions

#### Agent Configuration Issues
**Symptoms**: Validation errors, save failures, template loading problems

**Solutions**:
1. Verify all required fields are filled
2. Check parameter ranges and formats
3. Ensure agent names are unique
4. Validate JSON in advanced configuration
5. Use templates as starting points

### Debug Mode
Enable debug logging:
1. Open Command Palette
2. Run `Developer: Reload Window with Extensions Disabled`
3. Enable only AutoGen MCP extension
4. Set `AUTOGEN_MCP_DEBUG=true` environment variable
5. Check Debug Console for detailed logs

### Getting Help
- **Extension Issues**: File issues on GitHub repository
- **Documentation**: Check latest docs in repository
- **Community**: Join discussions in project Discord/Slack
- **Support**: Contact maintainers via project channels

### Log Files
Debug information available in:
- **Extension Host**: Help → Toggle Developer Tools → Console
- **Output Panel**: View → Output → AutoGen MCP
- **VS Code Logs**: Help → Open Process Explorer → VS Code logs

## Advanced Usage

### Custom Workflows
- Create workspace-specific agent configurations
- Set up project templates with pre-configured sessions
- Integrate with VS Code tasks and launch configurations
- Use with other extensions (Git, Docker, etc.)

### Automation
- Configure auto-start sessions for specific projects
- Set up memory archiving rules
- Create custom export schedules
- Integrate with CI/CD pipelines

### Extension Development
- Use extension APIs for custom integrations
- Create custom webview panels
- Extend command palette with project commands
- Contribute to open source development

---

For the latest updates and detailed API documentation, visit the [AutoGen MCP GitHub repository](https://github.com/your-org/autogen-mcp).

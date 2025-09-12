# VS Code Integration Plan for AutoGen MCP Server

This plan outlines the step-by-step process to integrate the AutoGen MCP server with VS Code, following the same disciplined approach used in the main implementation plan.

## Phase 1: MCP Server Enhancement
**Goal**: Replace dummy implementations with real services and add proper VS Code integration capabilities.

### Step 14 — Connect Real Services to MCP Server
- Branch: `feature/14-real-mcp-services`
- Scope:
  - [x] Replace dummy memory search with real MemoryService integration
  - [x] Connect orchestrator endpoints to real AgentOrchestrator
  - [x] Add proper error handling and logging
  - [x] Remove settings page (port set at startup only)
- Acceptance:
  - [x] `/memory/search` returns real results from Qdrant
  - [x] `/orchestrate/start` creates actual agent sessions
  - [x] All endpoints have proper error responses
- Tests:
  - [x] Integration: MCP server with real Qdrant backend
  - [x] Unit: endpoint error handling
  - [x] E2E: full orchestration flow
- Artifacts:
  - [x] ADR-013: MCP server real services integration

### Step 15 — Add File Operations and WebSocket Support
- Branch: `feature/15-mcp-realtime`
- Scope:
  - [x] Add `/workspace/write` endpoint for file operations
  - [x] Add `/workspace/files` endpoint for file listing
  - [x] Implement WebSocket endpoint for real-time session updates
  - [x] Add session state management
- Acceptance:
  - [x] MCP server can write files to workspace
  - [x] WebSocket streams agent progress in real-time
  - [x] Session state persists across requests
- Tests:
  - [x] Integration: file write operations
  - [x] WebSocket: connection and message flow
  - [x] Session: state persistence
- Artifacts:
  - [x] ADR-014: Real-time updates and file operations

## Phase 2: VS Code Extension Development
**Goal**: Create a VS Code extension that provides seamless integration with the MCP server.

### Step 16 — VS Code Extension Scaffold
- Branch: `feature/16-vscode-extension`
- Scope:
  - [x] Create VS Code extension structure using `yo code`
  - [x] Set up TypeScript project with proper dependencies
  - [x] Add basic activation and command registration
  - [x] Configure extension manifest (package.json)
- Acceptance:
  - [x] Extension loads in VS Code development host
  - [x] Basic commands appear in command palette
  - [x] Extension activates on workspace open
- Tests:
  - [x] Manual: extension loads without errors
  - [x] Commands: registered and callable
- Artifacts:
  - [x] Extension scaffold in `vscode-extension/` directory
  - [x] ADR-015: VS Code extension architecture

### Step 17 — Core Extension Commands
- Branch: `feature/17-extension-commands`
- Scope:
  - [x] Implement `autogen.startSession` command
  - [x] Implement `autogen.stopSession` command
  - [x] Implement `autogen.searchMemory` command
  - [x] Add HTTP client for MCP server communication
- Acceptance:
  - [x] Commands successfully call MCP server endpoints
  - [x] Results displayed in VS Code (output panel or notifications)
  - [x] Error handling for server unavailable
- Tests:
  - [x] Unit: HTTP client functions
  - [x] Integration: command → server → response flow
- Artifacts:
  - [x] Working extension commands
  - [x] Server communication layer
  - [x] ADR-016: Core extension commands architecture

### Step 18 — Extension UI Components
- Branch: `feature/18-extension-ui`
- Scope:
  - [ ] Create sidebar panel for session management
  - [ ] Add status bar item for active session
  - [ ] Implement memory search results view
  - [ ] Add quick input for objectives and queries
- Acceptance:
  - [ ] Sidebar shows session status and controls
  - [ ] Status bar indicates active/inactive state
  - [ ] Search results displayed in tree view
- Tests:
  - [ ] UI: panels render correctly
  - [ ] Interaction: clicks trigger appropriate actions
- Artifacts:
  - [ ] Complete UI components
  - [ ] User interaction flows

## Phase 3: Advanced Integration
**Goal**: Add sophisticated features for seamless development workflow.

### Step 19 — WebSocket Integration and Real-time Updates
- Branch: `feature/19-realtime-extension`
- Scope:
  - [ ] Add WebSocket client to extension
  - [ ] Stream agent progress to VS Code progress API
  - [ ] Real-time memory updates in sidebar
  - [ ] Live session status updates
- Acceptance:
  - [ ] Extension shows real-time agent progress
  - [ ] Memory view updates automatically
  - [ ] Session changes reflected immediately
- Tests:
  - [ ] WebSocket: connection handling
  - [ ] Real-time: message processing
  - [ ] UI: automatic updates
- Artifacts:
  - [ ] Real-time extension features
  - [ ] ADR-016: Real-time communication patterns

### Step 20 — Workspace Integration and File Operations
- Branch: `feature/20-workspace-integration`
- Scope:
  - [ ] Auto-detect workspace projects and initialize
  - [ ] File watching for automatic memory updates
  - [ ] Direct file writing from agent outputs
  - [ ] Git integration for agent-generated commits
- Acceptance:
  - [ ] Extension auto-configures per workspace
  - [ ] Agent outputs appear as workspace files
  - [ ] File changes trigger memory updates
- Tests:
  - [ ] Workspace: auto-detection and setup
  - [ ] File ops: write and watch operations
  - [ ] Git: commit creation
- Artifacts:
  - [ ] Complete workspace integration
  - [ ] ADR-017: Workspace and file management

## Phase 4: Polish and Distribution
**Goal**: Prepare extension for distribution and production use.

### Step 21 — Extension Testing and Packaging
- Branch: `feature/21-extension-packaging`
- Scope:
  - [ ] Add comprehensive extension tests
  - [ ] Configure CI/CD for extension builds
  - [ ] Add extension documentation and README
  - [ ] Package extension for VS Code marketplace
- Acceptance:
  - [ ] All tests pass in CI
  - [ ] Extension packages without errors
  - [ ] Documentation complete and clear
- Tests:
  - [ ] Unit: all extension functions
  - [ ] Integration: full workflow tests
  - [ ] E2E: manual testing scenarios
- Artifacts:
  - [ ] Packaged VSIX file
  - [ ] ADR-018: Extension testing and distribution

### Step 22 — Documentation and User Guide
- Branch: `feature/22-integration-docs`
- Scope:
  - [ ] Update main README with VS Code integration guide
  - [ ] Create extension user guide and tutorials
  - [ ] Add troubleshooting documentation
  - [ ] Update ADR index and changelog
- Acceptance:
  - [ ] Clear setup instructions for users
  - [ ] Working examples and screenshots
  - [ ] Common issues documented
- Tests:
  - [ ] Manual: follow documentation as new user
  - [ ] Docs: links and examples work
- Artifacts:
  - [ ] Complete integration documentation
  - [ ] ADR-019: Integration documentation strategy

---

## Status Snapshot
- [x] Step 14 — Connect Real Services to MCP Server
- [x] Step 15 — Add File Operations and WebSocket Support
- [x] Step 16 — VS Code Extension Scaffold
- [x] Step 17 — Core Extension Commands
- [ ] Step 18 — Extension UI Components
- [ ] Step 19 — WebSocket Integration and Real-time Updates
- [ ] Step 20 — Workspace Integration and File Operations
- [ ] Step 21 — Extension Testing and Packaging
- [ ] Step 22 — Documentation and User Guide

---

## Integration Architecture Overview

```
┌─────────────────┐    HTTP/WebSocket    ┌─────────────────┐
│   VS Code       │◄──────────────────────│   MCP Server    │
│   Extension     │                      │   (Port 9000)   │
│                 │                      │                 │
│ ┌─────────────┐ │                      │ ┌─────────────┐ │
│ │ Commands    │ │                      │ │ Memory      │ │
│ │ Sidebar     │ │                      │ │ Orchestrator│ │
│ │ Status Bar  │ │                      │ │ File Ops    │ │
│ └─────────────┘ │                      │ └─────────────┘ │
└─────────────────┘                      └─────────────────┘
         │                                        │
         │                                        │
         ▼                                        ▼
┌─────────────────┐                      ┌─────────────────┐
│   Workspace     │                      │   Qdrant +      │
│   Files         │                      │   AutoGen       │
│   Git Repos     │                      │   Services      │
└─────────────────┘                      └─────────────────┘
```

---

## Next Steps
Ready to begin Step 14: Connect Real Services to MCP Server. This will establish the foundation for all subsequent VS Code integration work.

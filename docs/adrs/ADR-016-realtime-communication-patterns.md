# ADR-016: Real-time Communication Patterns

## Status
Accepted

## Context

The AutoGen MCP VS Code extension requires real-time communication to provide users with immediate feedback on agent activities, session progress, and memory updates. This includes:

- Live session status updates as agents work
- Progress indicators for long-running operations
- Automatic UI refresh when data changes on the server
- Memory synchronization across multiple views
- Multi-session support with concurrent updates

The extension needs to handle various real-time scenarios while maintaining good performance and user experience.

## Decision

We implement a WebSocket-based real-time communication pattern with the following architecture:

### 1. WebSocket Client Architecture
- **RealtimeClient class**: Manages WebSocket connections and message routing
- **Per-session connections**: One WebSocket connection per active session
- **Event-driven messaging**: Uses VS Code's EventEmitter pattern for loose coupling
- **Automatic cleanup**: Connections disposed when sessions end or extension deactivates

### 2. Message Protocol
```typescript
interface RealtimeMessage {
    type: string;           // Message type (e.g., 'session_update', 'memory_update')
    session_id?: string;    // Associated session ID
    data?: any;            // Type-specific payload
}
```

### 3. Server-side Broadcasting
- **Session lifecycle events**: started, active, stopped
- **Periodic progress updates**: Every 2 seconds with progress_step and status
- **Event-triggered broadcasts**: On significant state changes
- **Connection management**: Per-session WebSocket endpoints at `/ws/session/{id}`

### 4. Client-side Integration
- **Global message subscription**: Extension-wide listener for all session updates
- **Automatic UI refresh**: Session tree, memory view, and status bar update on messages
- **Progress streaming**: Integration with VS Code's Progress API for user feedback
- **Dashboard live updates**: Real-time webview content updates

### 5. Error Handling and Resilience
- **Graceful degradation**: UI functions without WebSocket connectivity
- **Malformed message tolerance**: JSON parse errors don't crash the client
- **Connection cleanup**: Proper disposal on errors and session termination
- **Future enhancement hooks**: Ready for reconnection logic and backoff strategies

## Implementation Details

### WebSocket URL Construction
```typescript
private toWsUrl(httpUrl: string): string {
    if (httpUrl.startsWith('https://')) return 'wss://' + httpUrl.slice('https://'.length);
    if (httpUrl.startsWith('http://')) return 'ws://' + httpUrl.slice('http://'.length);
    return httpUrl.replace(/^/, 'ws://');
}
```

### Message Flow
1. **Session Start**: Extension calls `/orchestrate/start` → Server creates session → Extension connects WebSocket
2. **Progress Updates**: Server broadcasts periodic `session_update` messages with current status
3. **UI Updates**: Extension receives messages → Refreshes tree view, status bar, and open dashboards
4. **Session Stop**: Server broadcasts final `session_update` with stopped status → Extension closes WebSocket

### Performance Considerations
- **Connection pooling**: Reuse connections for the same session
- **Message throttling**: Server limits broadcast frequency to avoid overwhelming clients
- **Selective subscriptions**: Only connect WebSocket when UI components need updates
- **Memory management**: Proper cleanup of event listeners and connections

## Consequences

### Positive
- **Immediate user feedback**: Users see progress without manual refresh
- **Better UX**: Real-time updates create a more responsive feel
- **Scalable architecture**: Per-session connections support multiple concurrent sessions
- **Loose coupling**: Event-driven design allows easy addition of new UI components
- **VS Code integration**: Uses platform-native progress indicators and event patterns

### Negative
- **Increased complexity**: WebSocket management adds error handling requirements
- **Network dependency**: Real-time features require stable server connectivity
- **Resource usage**: Additional network connections and event listeners
- **Testing complexity**: Real-time behavior requires more sophisticated test scenarios

### Mitigations
- **Graceful fallback**: All features work without WebSocket connectivity
- **Comprehensive testing**: Extensive test suite covers connection handling and message processing
- **Error boundaries**: WebSocket errors don't affect core extension functionality
- **Future enhancements**: Architecture supports reconnection and resilience improvements

## Alternatives Considered

### 1. Polling-based Updates
- **Pros**: Simpler implementation, better compatibility
- **Cons**: Higher latency, more server load, poor user experience
- **Verdict**: Rejected - WebSocket provides superior real-time experience

### 2. Server-Sent Events (SSE)
- **Pros**: Simpler than WebSocket, automatic reconnection
- **Cons**: Unidirectional, limited browser support in VS Code context
- **Verdict**: Rejected - WebSocket bidirectional capability valuable for future features

### 3. HTTP Long Polling
- **Pros**: Works through firewalls, simpler server implementation
- **Cons**: Resource intensive, complex timeout handling
- **Verdict**: Rejected - WebSocket more efficient for frequent updates

## Future Enhancements

### Reconnection Logic
```typescript
class RealtimeClient {
    private reconnect(sessionId: string, attempt: number = 1) {
        const delay = Math.min(1000 * Math.pow(2, attempt), 30000);
        setTimeout(() => this.connect(sessionId), delay);
    }
}
```

### Message Queuing
- Buffer messages during disconnection
- Replay on reconnection
- Persistence for critical updates

### Enhanced Monitoring
- Connection health indicators in UI
- WebSocket performance metrics
- Diagnostic commands for troubleshooting

## References

- [WebSocket API Documentation](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [VS Code Extension API - Events](https://code.visualstudio.com/api/references/vscode-api#events)
- [VS Code Extension API - Progress](https://code.visualstudio.com/api/references/vscode-api#window.withProgress)
- [FastAPI WebSocket Documentation](https://fastapi.tiangolo.com/advanced/websockets/)

---

**Date**: September 12, 2025
**Authors**: AutoGen MCP Team
**Reviewers**: VS Code Extension Team

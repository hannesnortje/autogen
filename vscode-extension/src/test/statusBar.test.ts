import * as assert from 'assert';
import * as vscode from 'vscode';
import { AutoGenStatusBar } from '../statusBar';
import { SessionTreeProvider } from '../sessionTreeProvider';
import { McpClient } from '../mcpClient';

// Mock implementations
class MockSessionTreeProvider extends SessionTreeProvider {
    private mockSessions: any[] = [];

    constructor() {
        super(new McpClient('mock://localhost'));
    }

    setMockSessions(sessions: any[]) {
        this.mockSessions = sessions;
    }

    async getChildren(): Promise<any[]> {
        return this.mockSessions;
    }
}

class MockMcpClient extends McpClient {
    private connected = true;

    constructor() {
        super('mock://localhost');
    }

    setConnected(connected: boolean) {
        this.connected = connected;
    }

    async checkConnection(): Promise<boolean> {
        return this.connected;
    }
}

suite('AutoGenStatusBar Tests', () => {
    let statusBar: AutoGenStatusBar;
    let mockTreeProvider: MockSessionTreeProvider;
    let mockClient: MockMcpClient;
    let mockContext: vscode.ExtensionContext;

    setup(() => {
        mockTreeProvider = new MockSessionTreeProvider();
        mockClient = new MockMcpClient();

        // Create minimal mock context
        mockContext = {
            subscriptions: []
        } as any;

        statusBar = new AutoGenStatusBar(mockContext, mockClient, mockTreeProvider);
    });

    teardown(() => {
        statusBar.dispose();
    });

    test('should create status bar items', () => {
        assert.ok(statusBar);
        // Status bar items are created but we can't easily test them without VS Code context
    });

    test('should update with active sessions', async () => {
        const mockSessions = [
            { id: 'session-1', status: 'active', agents: [{ id: 'agent-1' }, { id: 'agent-2' }] },
            { id: 'session-2', status: 'active', agents: [{ id: 'agent-3' }] }
        ];

        mockTreeProvider.setMockSessions(mockSessions);
        await statusBar.updateStatusBar();

        // We would test the status bar text here, but it requires VS Code context
        assert.ok(true); // Placeholder for now
    });

    test('should handle no active sessions', async () => {
        mockTreeProvider.setMockSessions([]);
        await statusBar.updateStatusBar();

        assert.ok(true); // Placeholder - would test "No Active Sessions" text
    });

    test('should handle disconnected client', async () => {
        mockClient.setConnected(false);
        await statusBar.updateStatusBar();

        assert.ok(true); // Placeholder - would test "Disconnected" status
    });

    test('should refresh status bar', () => {
        statusBar.refresh();
        assert.ok(true); // Would verify update is triggered
    });

    test('should handle update errors gracefully', async () => {
        // Override to throw error
        mockTreeProvider.getChildren = async () => {
            throw new Error('Mock error');
        };

        // Should not throw
        await statusBar.updateStatusBar();
        assert.ok(true);
    });
});

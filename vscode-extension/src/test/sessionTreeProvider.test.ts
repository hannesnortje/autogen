import * as assert from 'assert';
import * as vscode from 'vscode';
import { SessionTreeProvider, SessionTreeItem, AgentTreeItem } from '../sessionTreeProvider';
import { McpClient } from '../mcpClient';

// Mock MCP Client
class MockMcpClient extends McpClient {
    private mockSessions: any[] = [];

    constructor() {
        super('mock://localhost');
        // Set default mock data that matches the expected API structure
        this.mockSessions = [
            {
                session_id: 'session-1',
                status: 'active',
                project: 'Test Project 1',
                created_at: '2024-01-01T10:00:00Z',
                agents: ['agent-1', 'agent-2']
            },
            {
                session_id: 'session-2',
                status: 'stopped',
                project: 'Test Project 2',
                created_at: '2024-01-01T09:00:00Z',
                agents: ['agent-3']
            }
        ];
    }

    setMockSessions(sessions: any[]) {
        this.mockSessions = sessions;
    }

    async listSessions(): Promise<any[]> {
        return this.mockSessions;
    }

    async isServerAvailable(): Promise<boolean> {
        return true;
    }
}

suite('SessionTreeProvider Tests', () => {
    let provider: SessionTreeProvider;
    let mockClient: MockMcpClient;

    setup(async () => {
        mockClient = new MockMcpClient();
        provider = new SessionTreeProvider(mockClient);

        // Wait a bit for the async refresh to complete
        await new Promise(resolve => setTimeout(resolve, 50));
    });

    test('should return root session items', async () => {
        const items = await provider.getChildren();

        assert.strictEqual(items.length, 2);
        assert.strictEqual(items[0].label, 'Test Project 1');
        assert.strictEqual(items[1].label, 'Test Project 2');
    });

    test('should return agent children for session items', async () => {
        const sessions = await provider.getChildren();
        const sessionItem = sessions[0] as SessionTreeItem;
        const agents = await provider.getChildren(sessionItem);

        assert.strictEqual(agents.length, 2);
        assert.strictEqual(agents[0].label, 'agent-1');
        assert.strictEqual(agents[1].label, 'agent-2');
    });

    test('should create session tree items with correct properties', async () => {
        const items = await provider.getChildren();
        const sessionItem = items[0] as SessionTreeItem;

        assert.strictEqual(sessionItem.label, 'Test Project 1');
        assert.ok(typeof sessionItem.description === 'string');
        assert.strictEqual(sessionItem.contextValue, 'session-active');
        assert.strictEqual(sessionItem.collapsibleState, vscode.TreeItemCollapsibleState.Collapsed);
    });

    test('should create agent tree items with correct properties', async () => {
        const sessions = await provider.getChildren();
        const sessionItem = sessions[0] as SessionTreeItem;
        const agents = await provider.getChildren(sessionItem);
        const agentItem = agents[0] as AgentTreeItem;

        assert.strictEqual(agentItem.label, 'agent-1');
        assert.strictEqual(agentItem.contextValue, 'agent');
        assert.strictEqual(agentItem.collapsibleState, vscode.TreeItemCollapsibleState.None);
    });

    test('should handle empty session list', async () => {
        // Override the mock to return empty list
        mockClient.setMockSessions([]);

        // Refresh the provider to pick up the new mock data
        provider.refresh();
        await new Promise(resolve => setTimeout(resolve, 50));

        const items = await provider.getChildren();
        assert.strictEqual(items.length, 0);
    });

    test('should refresh tree view', async () => {
        let refreshFired = false;
        provider.onDidChangeTreeData(() => {
            refreshFired = true;
        });

        provider.refresh();
        assert.strictEqual(refreshFired, true);
    });

    test('should handle session without agents', async () => {
        // Override mock to return session without agents
        mockClient.setMockSessions([{
            session_id: 'session-no-agents',
            status: 'active',
            project: 'Empty Session',
            created_at: '2024-01-01T10:00:00Z',
            agents: []
        }]);

        // Refresh the provider to pick up the new mock data
        provider.refresh();
        await new Promise(resolve => setTimeout(resolve, 50));

        const sessions = await provider.getChildren();
        const sessionItem = sessions[0] as SessionTreeItem;
        const agents = await provider.getChildren(sessionItem);

        assert.strictEqual(agents.length, 0);
    });
});

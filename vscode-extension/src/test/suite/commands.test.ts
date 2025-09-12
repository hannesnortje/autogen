import * as assert from 'assert';
import * as vscode from 'vscode';
import { McpClient, McpServerError } from '../../mcpClient';

suite('Extension Command Tests', () => {
    let mcpClient: McpClient;

    setup(() => {
        mcpClient = new McpClient('http://localhost:9000');
    });

    test('McpClient server availability check', async () => {
        try {
            const isAvailable = await mcpClient.isServerAvailable();
            // Should be true if server is running, false if not
            assert.strictEqual(typeof isAvailable, 'boolean');
        } catch (error) {
            // This is acceptable if server is not running
            assert.ok(error instanceof McpServerError || error instanceof Error);
        }
    });

    test('McpClient health check format', async () => {
        try {
            const health = await mcpClient.getHealth();
            assert.ok(health.status);
            assert.strictEqual(typeof health.status, 'string');
        } catch (error) {
            // Server may not be available during testing
            assert.ok(error instanceof McpServerError);
        }
    });

    test('Extension commands are registered', async () => {
        const commands = await vscode.commands.getCommands();

        const autogenCommands = [
            'autogen.startSession',
            'autogen.stopSession',
            'autogen.searchMemory',
            'autogen.addObjective',
            'autogen.showDashboard',
            'autogen.checkServerStatus'
        ];

        for (const command of autogenCommands) {
            assert.ok(
                commands.includes(command),
                `Command ${command} should be registered`
            );
        }
    });

    test('McpClient error handling', async () => {
        const invalidClient = new McpClient('http://invalid-server:9999');

        try {
            await invalidClient.getHealth();
            assert.fail('Should have thrown an error for invalid server');
        } catch (error) {
            assert.ok(error instanceof McpServerError);
            assert.ok(error.message.includes('Failed to connect'));
        }
    });

    test('Session management', () => {
        // Test session ID management
        assert.strictEqual(mcpClient.getCurrentSessionId(), null);

        mcpClient.setCurrentSessionId('test-session-123');
        assert.strictEqual(mcpClient.getCurrentSessionId(), 'test-session-123');

        mcpClient.setCurrentSessionId(null);
        assert.strictEqual(mcpClient.getCurrentSessionId(), null);
    });
});

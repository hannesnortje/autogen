import * as assert from 'assert';
import * as vscode from 'vscode';
import { McpClient } from '../../mcpClient';

suite('Extension Test Suite', () => {
    vscode.window.showInformationMessage('Start all tests.');

    test('McpClient creation', () => {
        const client = new McpClient('http://localhost:9000');
        assert.strictEqual(client.serverUrl, 'http://localhost:9000');
    });

    test('Extension activation', async () => {
        // Test that the extension can be activated
        const extension = vscode.extensions.getExtension('autogen.autogen-mcp');
        if (extension) {
            await extension.activate();
            assert.strictEqual(extension.isActive, true);
        }
    });
});

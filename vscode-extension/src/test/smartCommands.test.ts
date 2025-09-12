import * as assert from 'assert';
import * as vscode from 'vscode';
import { SmartCommandPalette } from '../smartCommands';
import { SessionTreeProvider } from '../sessionTreeProvider';
import { McpClient } from '../mcpClient';

// Mock implementations
class MockSessionTreeProvider extends SessionTreeProvider {
    constructor() {
        super(new McpClient('mock://localhost'));
    }

    async getChildren(): Promise<any[]> {
        return [
            { id: 'session-1', label: 'Session 1' },
            { id: 'session-2', label: 'Session 2' }
        ];
    }
}

class MockMcpClient extends McpClient {
    constructor() {
        super('mock://localhost');
    }

    async listTools(): Promise<any[]> {
        return [
            { name: 'create_session', description: 'Create a new session' },
            { name: 'send_message', description: 'Send a message' }
        ];
    }

    async getAgentTemplates(): Promise<any[]> {
        return [
            { name: 'assistant', description: 'General assistant agent' },
            { name: 'code_executor', description: 'Code execution agent' }
        ];
    }
}

suite('SmartCommandPalette Tests', () => {
    let smartCommands: SmartCommandPalette;
    let mockTreeProvider: MockSessionTreeProvider;
    let mockClient: MockMcpClient;
    let mockContext: vscode.ExtensionContext;

    setup(() => {
        mockTreeProvider = new MockSessionTreeProvider();
        mockClient = new MockMcpClient();

        // Create minimal mock context that avoids command registration
        mockContext = {
            subscriptions: [],
            workspaceState: {
                get: () => undefined,
                update: () => Promise.resolve()
            } as any,
            globalState: {
                get: () => undefined,
                update: () => Promise.resolve()
            } as any
        } as any;

        // Skip actual command registration during tests by mocking VS Code commands
        const originalRegisterCommand = vscode.commands.registerCommand;
        vscode.commands.registerCommand = () => ({ dispose: () => {} }) as any;

        smartCommands = new SmartCommandPalette(mockContext, mockClient, mockTreeProvider);

        // Restore original function
        vscode.commands.registerCommand = originalRegisterCommand;
    });

    test('should initialize smart command palette', () => {
        assert.ok(smartCommands);
    });

    test('should return smart commands configuration', () => {
        const commands = smartCommands.getSmartCommands();
        assert.ok(commands instanceof Map);
        assert.ok(commands.size > 0);
    });

    test('should have registered autogen.startSessionWithParams command', () => {
        const commands = smartCommands.getSmartCommands();
        assert.ok(commands.has('autogen.startSessionWithParams'));

        const config = commands.get('autogen.startSessionWithParams');
        assert.ok(config);
        assert.strictEqual(config.showInPalette, true);
        assert.strictEqual(config.requiresServer, true);
        assert.strictEqual(config.promptForParams, true);
    });

    test('should have registered autogen.searchMemoryAdvanced command', () => {
        const commands = smartCommands.getSmartCommands();
        assert.ok(commands.has('autogen.searchMemoryAdvanced'));

        const config = commands.get('autogen.searchMemoryAdvanced');
        assert.ok(config);
        assert.strictEqual(config.showInPalette, true);
        assert.strictEqual(config.requiresServer, true);
    });

    test('should have parameter schemas for configured commands', () => {
        const commands = smartCommands.getSmartCommands();
        const startSessionConfig = commands.get('autogen.startSessionWithParams');

        assert.ok(startSessionConfig);
        assert.ok(startSessionConfig.paramSchema);
        assert.ok(startSessionConfig.paramSchema.length > 0);

        // Check that essential parameters are present
        const paramNames = startSessionConfig.paramSchema.map(p => p.name);
        assert.ok(paramNames.includes('projectName'));
        assert.ok(paramNames.includes('agents'));
        assert.ok(paramNames.includes('objective'));
    });

    test('should configure choice parameters correctly', () => {
        const commands = smartCommands.getSmartCommands();
        const startSessionConfig = commands.get('autogen.startSessionWithParams');

        assert.ok(startSessionConfig);
        assert.ok(startSessionConfig.paramSchema);

        const agentsParam = startSessionConfig.paramSchema.find(p => p.name === 'agents');
        assert.ok(agentsParam);
        assert.strictEqual(agentsParam.type, 'multiChoice');
        assert.ok(agentsParam.choices);
        assert.ok(agentsParam.choices.length > 0);

        // Check for expected agent choices
        const choiceValues = agentsParam.choices.map(c => c.value);
        assert.ok(choiceValues.includes('Coder'));
        assert.ok(choiceValues.includes('Reviewer'));
        assert.ok(choiceValues.includes('Tester'));
    });

    test('should handle multiple registered commands', () => {
        const commands = smartCommands.getSmartCommands();

        // Should have at least the core smart commands
        const expectedCommands = [
            'autogen.startSessionWithParams',
            'autogen.searchMemoryAdvanced',
            'autogen.addObjectiveAdvanced',
            'autogen.stopSessionAdvanced'
        ];

        expectedCommands.forEach(cmd => {
            assert.ok(commands.has(cmd), `Command ${cmd} should be registered`);
        });
    });
});

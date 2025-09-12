import * as vscode from 'vscode';
import { AutoGenSessionProvider } from './sessionProvider';
import { AutoGenMemoryProvider } from './memoryProvider';
import { McpClient } from './mcpClient';

let mcpClient: McpClient;
let sessionProvider: AutoGenSessionProvider;
let memoryProvider: AutoGenMemoryProvider;

export function activate(context: vscode.ExtensionContext) {
    console.log('AutoGen MCP extension is now active!');

    // Initialize MCP client
    const config = vscode.workspace.getConfiguration('autogen');
    const serverUrl = config.get<string>('serverUrl', 'http://localhost:9000');
    mcpClient = new McpClient(serverUrl);

    // Initialize providers
    sessionProvider = new AutoGenSessionProvider(mcpClient);
    memoryProvider = new AutoGenMemoryProvider(mcpClient);

    // Register tree data providers
    vscode.window.createTreeView('autogen.sessionView', {
        treeDataProvider: sessionProvider,
        showCollapseAll: true
    });

    vscode.window.createTreeView('autogen.memoryView', {
        treeDataProvider: memoryProvider,
        showCollapseAll: true
    });

    // Register commands
    const commands = [
        vscode.commands.registerCommand('autogen.startSession', async () => {
            await startSession();
        }),

        vscode.commands.registerCommand('autogen.stopSession', async () => {
            await stopSession();
        }),

        vscode.commands.registerCommand('autogen.searchMemory', async () => {
            await searchMemory();
        }),

        vscode.commands.registerCommand('autogen.addObjective', async () => {
            await addObjective();
        }),

        vscode.commands.registerCommand('autogen.showDashboard', async () => {
            await showDashboard();
        }),

        vscode.commands.registerCommand('autogen.refreshSessions', () => {
            sessionProvider.refresh();
        }),

        vscode.commands.registerCommand('autogen.refreshMemory', () => {
            memoryProvider.refresh();
        })
    ];

    // Add all commands to context subscriptions
    commands.forEach(command => context.subscriptions.push(command));

    // Auto-start server if configured
    const autoStart = config.get<boolean>('autoStart', false);
    if (autoStart) {
        vscode.window.showInformationMessage('AutoGen MCP: Auto-start is enabled');
    }

    // Show status in status bar
    const statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBarItem.text = "$(robot) AutoGen";
    statusBarItem.tooltip = "AutoGen MCP Status";
    statusBarItem.command = 'autogen.showDashboard';
    statusBarItem.show();
    context.subscriptions.push(statusBarItem);
}

async function startSession() {
    try {
        const projectName = vscode.workspace.name || 'default-project';
        const agents = await vscode.window.showQuickPick(
            ['Coder', 'Reviewer', 'Tester', 'Architect', 'DevOps'],
            {
                canPickMany: true,
                placeHolder: 'Select agents for the session'
            }
        );

        if (!agents || agents.length === 0) {
            vscode.window.showWarningMessage('No agents selected');
            return;
        }

        const objective = await vscode.window.showInputBox({
            prompt: 'Enter the objective for this session',
            placeHolder: 'e.g., Implement user authentication system'
        });

        if (!objective) {
            vscode.window.showWarningMessage('No objective provided');
            return;
        }

        const response = await mcpClient.startOrchestration({
            project: projectName,
            agents: agents,
            objective: objective
        });

        vscode.window.showInformationMessage(`Session started: ${response.session_id}`);
        sessionProvider.refresh();

    } catch (error) {
        vscode.window.showErrorMessage(`Failed to start session: ${error}`);
    }
}

async function stopSession() {
    // For now, just show a placeholder
    vscode.window.showInformationMessage('Stop session functionality to be implemented');
}

async function searchMemory() {
    try {
        const query = await vscode.window.showInputBox({
            prompt: 'Enter search query',
            placeHolder: 'Search memory...'
        });

        if (!query) {
            return;
        }

        const results = await mcpClient.searchMemory({
            query: query,
            scope: 'project',
            k: 10
        });

        // Show results in a new document
        const doc = await vscode.workspace.openTextDocument({
            content: `Memory Search Results for: "${query}"\n\n${JSON.stringify(results, null, 2)}`,
            language: 'json'
        });

        await vscode.window.showTextDocument(doc);

    } catch (error) {
        vscode.window.showErrorMessage(`Search failed: ${error}`);
    }
}

async function addObjective() {
    try {
        const projectName = vscode.workspace.name || 'default-project';
        const objective = await vscode.window.showInputBox({
            prompt: 'Enter new objective',
            placeHolder: 'e.g., Add unit tests for authentication module'
        });

        if (!objective) {
            return;
        }

        await mcpClient.addObjective({
            objective: objective,
            project: projectName
        });

        vscode.window.showInformationMessage('Objective added successfully');
        memoryProvider.refresh();

    } catch (error) {
        vscode.window.showErrorMessage(`Failed to add objective: ${error}`);
    }
}

async function showDashboard() {
    // Create and show a simple dashboard webview
    const panel = vscode.window.createWebviewPanel(
        'autogenDashboard',
        'AutoGen Dashboard',
        vscode.ViewColumn.One,
        {
            enableScripts: true
        }
    );

    panel.webview.html = getDashboardHtml();
}

function getDashboardHtml(): string {
    return `
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AutoGen Dashboard</title>
            <style>
                body { font-family: var(--vscode-font-family); padding: 20px; }
                .status { margin: 10px 0; padding: 10px; border-radius: 4px; }
                .status.connected { background: var(--vscode-terminal-ansiGreen); }
                .status.disconnected { background: var(--vscode-terminal-ansiRed); }
            </style>
        </head>
        <body>
            <h1>AutoGen MCP Dashboard</h1>
            <div class="status connected">
                <h3>Server Status: Connected</h3>
                <p>MCP Server: ${mcpClient?.serverUrl || 'Not configured'}</p>
            </div>
            <h3>Quick Actions</h3>
            <ul>
                <li>Use Command Palette (Ctrl+Shift+P) → "AutoGen: Start Session"</li>
                <li>Use Command Palette → "AutoGen: Search Memory"</li>
                <li>Use Command Palette → "AutoGen: Add Objective"</li>
            </ul>
        </body>
        </html>
    `;
}

export function deactivate() {
    console.log('AutoGen MCP extension is now deactivated');
}

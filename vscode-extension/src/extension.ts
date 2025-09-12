import * as vscode from 'vscode';
import { AutoGenSessionProvider } from './sessionProvider';
import { AutoGenMemoryProvider } from './memoryProvider';
import { McpClient, McpServerError } from './mcpClient';

let mcpClient: McpClient;
let sessionProvider: AutoGenSessionProvider;
let memoryProvider: AutoGenMemoryProvider;
let statusBarItem: vscode.StatusBarItem;

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
        }),

        vscode.commands.registerCommand('autogen.checkServerStatus', async () => {
            await checkServerStatus();
        })
    ];

    // Add all commands to context subscriptions
    commands.forEach(command => context.subscriptions.push(command));

    // Show status in status bar
    statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBarItem.command = 'autogen.showDashboard';
    statusBarItem.show();
    context.subscriptions.push(statusBarItem);

    // Initial server status check
    updateStatusBar();

    // Auto-start server if configured
    const autoStart = config.get<boolean>('autoStart', false);
    if (autoStart) {
        vscode.window.showInformationMessage('AutoGen MCP: Auto-start is enabled');
    }
}

async function checkServerConnection(): Promise<boolean> {
    try {
        return await mcpClient.isServerAvailable();
    } catch (error) {
        return false;
    }
}

async function updateStatusBar() {
    const isConnected = await checkServerConnection();
    const sessionId = mcpClient.getCurrentSessionId();

    if (isConnected) {
        if (sessionId) {
            statusBarItem.text = "$(robot) AutoGen (Active)";
            statusBarItem.tooltip = `AutoGen MCP - Session: ${sessionId.substring(0, 8)}...`;
        } else {
            statusBarItem.text = "$(robot) AutoGen (Ready)";
            statusBarItem.tooltip = "AutoGen MCP - Ready";
        }
    } else {
        statusBarItem.text = "$(robot) AutoGen (Disconnected)";
        statusBarItem.tooltip = `AutoGen MCP - Server unavailable at ${mcpClient.serverUrl}`;
    }
}

async function checkServerStatus() {
    const isConnected = await checkServerConnection();
    if (isConnected) {
        vscode.window.showInformationMessage(`AutoGen MCP server is available at ${mcpClient.serverUrl}`);
    } else {
        vscode.window.showErrorMessage(`AutoGen MCP server is not available at ${mcpClient.serverUrl}`);
    }
    await updateStatusBar();
}

async function startSession() {
    try {
        // Check server connection first
        if (!(await checkServerConnection())) {
            vscode.window.showErrorMessage('AutoGen MCP server is not available. Please check your configuration.');
            return;
        }

        // Check if there's already an active session
        const currentSessionId = mcpClient.getCurrentSessionId();
        if (currentSessionId) {
            const choice = await vscode.window.showWarningMessage(
                `There is already an active session (${currentSessionId.substring(0, 8)}...). Stop it first?`,
                'Stop Current',
                'Cancel'
            );
            if (choice === 'Stop Current') {
                await stopSession();
            } else {
                return;
            }
        }

        const projectName = vscode.workspace.name || vscode.workspace.workspaceFolders?.[0]?.name || 'default-project';

        const agents = await vscode.window.showQuickPick(
            ['Coder', 'Reviewer', 'Tester', 'Architect', 'DevOps'],
            {
                canPickMany: true,
                placeHolder: 'Select agents for the session (you can select multiple)'
            }
        );

        if (!agents || agents.length === 0) {
            vscode.window.showWarningMessage('No agents selected');
            return;
        }

        const objective = await vscode.window.showInputBox({
            prompt: 'Enter the objective for this session',
            placeHolder: 'e.g., Implement user authentication system',
            validateInput: (value) => {
                if (!value.trim()) {
                    return 'Objective cannot be empty';
                }
                if (value.length < 10) {
                    return 'Please provide a more detailed objective (at least 10 characters)';
                }
                return null;
            }
        });

        if (!objective) {
            vscode.window.showWarningMessage('No objective provided');
            return;
        }

        // Show progress indicator
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Starting AutoGen session...",
            cancellable: false
        }, async (progress) => {
            progress.report({ increment: 0, message: "Initializing..." });

            const response = await mcpClient.startOrchestration({
                project: projectName,
                agents: agents,
                objective: objective.trim()
            });

            progress.report({ increment: 100, message: "Session started!" });

            vscode.window.showInformationMessage(
                `AutoGen session started successfully! Session ID: ${response.session_id.substring(0, 8)}...`
            );

            sessionProvider.refresh();
            await updateStatusBar();
        });

    } catch (error) {
        if (error instanceof McpServerError) {
            vscode.window.showErrorMessage(`Failed to start session: ${error.message}`);
        } else {
            vscode.window.showErrorMessage(`Failed to start session: ${error}`);
        }
        console.error('Start session error:', error);
    }
}

async function stopSession() {
    try {
        const currentSessionId = mcpClient.getCurrentSessionId();
        if (!currentSessionId) {
            vscode.window.showInformationMessage('No active session to stop');
            return;
        }

        const choice = await vscode.window.showWarningMessage(
            `Stop the current AutoGen session (${currentSessionId.substring(0, 8)}...)?`,
            'Stop Session',
            'Cancel'
        );

        if (choice !== 'Stop Session') {
            return;
        }

        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Stopping AutoGen session...",
            cancellable: false
        }, async (progress) => {
            progress.report({ increment: 0, message: "Stopping session..." });

            const response = await mcpClient.stopSession();

            progress.report({ increment: 100, message: "Session stopped!" });

            vscode.window.showInformationMessage(`Session stopped: ${response.message}`);
            sessionProvider.refresh();
            await updateStatusBar();
        });

    } catch (error) {
        if (error instanceof McpServerError) {
            vscode.window.showErrorMessage(`Failed to stop session: ${error.message}`);
        } else {
            vscode.window.showErrorMessage(`Failed to stop session: ${error}`);
        }
        console.error('Stop session error:', error);
    }
}

async function searchMemory() {
    try {
        // Check server connection first
        if (!(await checkServerConnection())) {
            vscode.window.showErrorMessage('AutoGen MCP server is not available. Please check your configuration.');
            return;
        }

        const query = await vscode.window.showInputBox({
            prompt: 'Enter search query',
            placeHolder: 'Search memory...',
            validateInput: (value) => {
                if (!value.trim()) {
                    return 'Search query cannot be empty';
                }
                if (value.length < 3) {
                    return 'Please provide a more specific search query (at least 3 characters)';
                }
                return null;
            }
        });

        if (!query) {
            return;
        }

        const scope = await vscode.window.showQuickPick(
            ['project', 'session', 'global'],
            {
                placeHolder: 'Select search scope'
            }
        );

        if (!scope) {
            return;
        }

        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Searching memory...",
            cancellable: false
        }, async (progress) => {
            progress.report({ increment: 0, message: "Searching..." });

            const results = await mcpClient.searchMemory({
                query: query.trim(),
                scope: scope,
                k: 10
            });

            progress.report({ increment: 100, message: "Search complete!" });

            // Format results for better readability
            let content = `# Memory Search Results\n\n`;
            content += `**Query:** ${query}\n`;
            content += `**Scope:** ${scope}\n`;
            content += `**Results:** ${results.results.length} found\n\n`;

            if (results.results.length === 0) {
                content += '*No results found.*\n';
            } else {
                results.results.forEach((result, index) => {
                    content += `## Result ${index + 1} (Score: ${result.score.toFixed(3)})\n\n`;
                    content += `${result.content}\n\n`;
                    if (result.metadata && Object.keys(result.metadata).length > 0) {
                        content += `**Metadata:** ${JSON.stringify(result.metadata, null, 2)}\n\n`;
                    }
                    content += '---\n\n';
                });
            }

            // Show results in a new document
            const doc = await vscode.workspace.openTextDocument({
                content: content,
                language: 'markdown'
            });

            await vscode.window.showTextDocument(doc);
            memoryProvider.refresh();
        });

    } catch (error) {
        if (error instanceof McpServerError) {
            vscode.window.showErrorMessage(`Memory search failed: ${error.message}`);
        } else {
            vscode.window.showErrorMessage(`Memory search failed: ${error}`);
        }
        console.error('Search memory error:', error);
    }
}

async function addObjective() {
    try {
        // Check server connection first
        if (!(await checkServerConnection())) {
            vscode.window.showErrorMessage('AutoGen MCP server is not available. Please check your configuration.');
            return;
        }

        const projectName = vscode.workspace.name || vscode.workspace.workspaceFolders?.[0]?.name || 'default-project';

        const objective = await vscode.window.showInputBox({
            prompt: 'Enter new objective',
            placeHolder: 'e.g., Add unit tests for authentication module',
            validateInput: (value) => {
                if (!value.trim()) {
                    return 'Objective cannot be empty';
                }
                if (value.length < 10) {
                    return 'Please provide a more detailed objective (at least 10 characters)';
                }
                return null;
            }
        });

        if (!objective) {
            return;
        }

        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Adding objective...",
            cancellable: false
        }, async (progress) => {
            progress.report({ increment: 0, message: "Saving objective..." });

            await mcpClient.addObjective({
                objective: objective.trim(),
                project: projectName
            });

            progress.report({ increment: 100, message: "Objective added!" });

            vscode.window.showInformationMessage('Objective added successfully');
            memoryProvider.refresh();
        });

    } catch (error) {
        if (error instanceof McpServerError) {
            vscode.window.showErrorMessage(`Failed to add objective: ${error.message}`);
        } else {
            vscode.window.showErrorMessage(`Failed to add objective: ${error}`);
        }
        console.error('Add objective error:', error);
    }
}

async function showDashboard() {
    try {
        // Create and show dashboard webview
        const panel = vscode.window.createWebviewPanel(
            'autogenDashboard',
            'AutoGen Dashboard',
            vscode.ViewColumn.One,
            {
                enableScripts: true
            }
        );

        // Check server status for dashboard
        const isConnected = await checkServerConnection();
        const sessionId = mcpClient.getCurrentSessionId();

        panel.webview.html = getDashboardHtml(isConnected, sessionId);

        // Handle messages from the webview
        panel.webview.onDidReceiveMessage(
            async message => {
                switch (message.command) {
                    case 'checkStatus':
                        await checkServerStatus();
                        break;
                    case 'startSession':
                        await startSession();
                        break;
                    case 'stopSession':
                        await stopSession();
                        break;
                }
            },
            undefined,
            []
        );

    } catch (error) {
        vscode.window.showErrorMessage(`Failed to show dashboard: ${error}`);
        console.error('Show dashboard error:', error);
    }
}

function getDashboardHtml(isConnected: boolean, sessionId: string | null): string {
    const statusClass = isConnected ? 'connected' : 'disconnected';
    const statusText = isConnected ? 'Connected' : 'Disconnected';
    const sessionInfo = sessionId ? `<p><strong>Active Session:</strong> ${sessionId.substring(0, 8)}...</p>` : '<p>No active session</p>';

    return `
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AutoGen Dashboard</title>
            <style>
                body {
                    font-family: var(--vscode-font-family);
                    padding: 20px;
                    background-color: var(--vscode-editor-background);
                    color: var(--vscode-editor-foreground);
                }
                .status {
                    margin: 10px 0;
                    padding: 15px;
                    border-radius: 4px;
                    border: 1px solid var(--vscode-panel-border);
                }
                .status.connected {
                    background-color: var(--vscode-terminal-ansiGreen);
                    color: var(--vscode-terminal-background);
                }
                .status.disconnected {
                    background-color: var(--vscode-terminal-ansiRed);
                    color: var(--vscode-terminal-background);
                }
                .actions {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                    margin: 20px 0;
                }
                .action-button {
                    padding: 15px;
                    border: 1px solid var(--vscode-button-border);
                    border-radius: 4px;
                    background-color: var(--vscode-button-background);
                    color: var(--vscode-button-foreground);
                    text-align: center;
                    cursor: pointer;
                    transition: all 0.2s;
                }
                .action-button:hover {
                    background-color: var(--vscode-button-hoverBackground);
                }
                .section {
                    margin: 20px 0;
                    padding: 15px;
                    border: 1px solid var(--vscode-panel-border);
                    border-radius: 4px;
                }
                .command-list {
                    list-style-type: none;
                    padding: 0;
                }
                .command-list li {
                    padding: 8px 0;
                    border-bottom: 1px solid var(--vscode-panel-border);
                }
                .command-list li:last-child {
                    border-bottom: none;
                }
                .command-code {
                    font-family: var(--vscode-editor-font-family);
                    background-color: var(--vscode-textCodeBlock-background);
                    padding: 2px 6px;
                    border-radius: 3px;
                }
            </style>
        </head>
        <body>
            <h1>🤖 AutoGen MCP Dashboard</h1>

            <div class="status ${statusClass}">
                <h3>Server Status: ${statusText}</h3>
                <p><strong>MCP Server:</strong> ${mcpClient?.serverUrl || 'Not configured'}</p>
                ${sessionInfo}
            </div>

            <div class="actions">
                <div class="action-button" onclick="sendMessage('checkStatus')">
                    🔍 Check Server Status
                </div>
                <div class="action-button" onclick="sendMessage('startSession')">
                    ▶️ Start New Session
                </div>
                <div class="action-button" onclick="sendMessage('stopSession')">
                    ⏹️ Stop Current Session
                </div>
            </div>

            <div class="section">
                <h3>📋 Available Commands</h3>
                <ul class="command-list">
                    <li><span class="command-code">AutoGen: Start Session</span> - Launch a new AutoGen session with selected agents</li>
                    <li><span class="command-code">AutoGen: Stop Session</span> - Stop the current AutoGen session</li>
                    <li><span class="command-code">AutoGen: Search Memory</span> - Search through stored project memory</li>
                    <li><span class="command-code">AutoGen: Add Objective</span> - Add new objectives to the current project</li>
                    <li><span class="command-code">AutoGen: Check Server Status</span> - Verify MCP server connectivity</li>
                </ul>
            </div>

            <div class="section">
                <h3>🚀 Quick Start</h3>
                <ol>
                    <li>Ensure the AutoGen MCP server is running on ${mcpClient?.serverUrl || 'http://localhost:9000'}</li>
                    <li>Use <kbd>Ctrl+Shift+P</kbd> to open the Command Palette</li>
                    <li>Type "AutoGen" to see available commands</li>
                    <li>Start with "AutoGen: Start Session" to begin</li>
                </ol>
            </div>

            <script>
                const vscode = acquireVsCodeApi();

                function sendMessage(command) {
                    vscode.postMessage({
                        command: command
                    });
                }
            </script>
        </body>
        </html>
    `;
}

export function deactivate() {
    console.log('AutoGen MCP extension is now deactivated');
}

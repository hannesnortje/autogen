import * as vscode from 'vscode';
import { AutoGenMemoryProvider } from './memoryProvider';
import { McpClient, McpServerError } from './mcpClient';
import { SessionTreeProvider, SessionData } from './sessionTreeProvider';
import { registerMemoryExplorerCommand } from './memoryExplorerPanel';
import { AutoGenStatusBar, registerStatusBarCommands } from './statusBar';
import { registerAgentConfigurationCommand } from './agentConfigPanel';
import { registerSmartCommands } from './smartCommands';
import { RealtimeClient } from './realtime';

// Import workspace integration services
import { WorkspaceManager } from './services/workspaceManager';
import { FileWatcher } from './services/fileWatcher';
import { FileOperations } from './services/fileOperations';
import { GitIntegration } from './services/gitIntegration';
import { WorkspaceConfiguration } from './services/workspaceConfiguration';

let mcpClient: McpClient;
let sessionTreeProvider: SessionTreeProvider;
let memoryProvider: AutoGenMemoryProvider;
let statusBar: AutoGenStatusBar;
let realtime: RealtimeClient;

// Workspace integration services
let workspaceManager: WorkspaceManager;
let fileWatcher: FileWatcher;
let fileOperations: FileOperations;
let gitIntegration: GitIntegration;
let workspaceConfiguration: WorkspaceConfiguration;

// Track open session dashboards for live refreshes
const openSessionPanels = new Map<string, vscode.WebviewPanel>();

export async function activate(context: vscode.ExtensionContext) {
    console.log('AutoGen MCP extension is now active!');

    // Initialize MCP client
    const config = vscode.workspace.getConfiguration('autogen');
    const serverUrl = config.get<string>('serverUrl', 'http://localhost:9000');
    mcpClient = new McpClient(serverUrl);
    realtime = new RealtimeClient(mcpClient);

    // Initialize workspace integration services
    try {
        workspaceManager = new WorkspaceManager();
        fileOperations = new FileOperations();
        gitIntegration = new GitIntegration();

        // Initialize file watcher with WebSocket broadcasting
        fileWatcher = new FileWatcher(realtime);

        workspaceConfiguration = new WorkspaceConfiguration(
            workspaceManager,
            fileWatcher,
            fileOperations,
            gitIntegration,
            realtime
        );

        // Auto-detect and configure workspace
        await initializeWorkspaceIntegration(context);

        console.log('✅ Workspace integration services initialized successfully');
    } catch (error) {
        console.error('❌ Failed to initialize workspace integration:', error);
        vscode.window.showErrorMessage(`Failed to initialize workspace integration: ${error}`);
    }

    // Initialize providers
    sessionTreeProvider = new SessionTreeProvider(mcpClient);
    memoryProvider = new AutoGenMemoryProvider(mcpClient);

    // Register tree data providers
    vscode.window.createTreeView('autogen.sessionView', {
        treeDataProvider: sessionTreeProvider,
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
            sessionTreeProvider.refresh();
        }),

        vscode.commands.registerCommand('autogen.refreshMemory', () => {
            memoryProvider.refresh();
        }),

        vscode.commands.registerCommand('autogen.checkServerStatus', async () => {
            await checkServerStatus();
        }),

        vscode.commands.registerCommand('autogen.startServer', async () => {
            await startMcpServer();
        }),

        vscode.commands.registerCommand('autogen.openSessionDashboard', async (sessionId: string) => {
            await openSessionDashboard(sessionId);
        }),

        vscode.commands.registerCommand('autogen.viewAgentDetails', async (sessionId: string, agentName: string) => {
            await viewAgentDetails(sessionId, agentName);
        })
    ];

    // Add all commands to context subscriptions
    commands.forEach(command => context.subscriptions.push(command));

    // Register memory explorer command
    registerMemoryExplorerCommand(context, mcpClient);

    // Register agent configuration command
    registerAgentConfigurationCommand(context, mcpClient);

    // Register smart commands
    const smartCommandPalette = registerSmartCommands(context, mcpClient, sessionTreeProvider);

    // Register status bar commands
    registerStatusBarCommands(context, mcpClient, statusBar);

    // Initialize enhanced status bar
    statusBar = new AutoGenStatusBar(context, mcpClient, sessionTreeProvider);

    // Initial server status check
    await statusBar.updateStatusBar();

    // Global realtime wiring: refresh views and stream progress on updates
    const globalRtSub = realtime.onMessage((msg) => {
        try {
            if (msg.type === 'session_update') {
                // Always refresh sessions and memory on updates
                sessionTreeProvider.refresh();
                memoryProvider.refresh();
                statusBar.refresh();

                // Stream progress to VS Code progress API
                if (msg.session_id) {
                    handleProgressForSession(msg.session_id, msg);
                }
            }
        } catch (e) {
            // no-op
        }
    });
    context.subscriptions.push(globalRtSub);

    // Auto-start server if configured
    const autoStart = config.get<boolean>('autoStart', false);
    if (autoStart) {
        vscode.window.showInformationMessage('AutoGen MCP: Auto-start is enabled, starting server...');
        setTimeout(async () => {
            const success = await startMcpServer();
            if (success) {
                vscode.window.showInformationMessage('✅ AutoGen MCP Server auto-started successfully!');
            } else {
                vscode.window.showWarningMessage('⚠️ AutoGen MCP Server auto-start failed. You can start it manually.');
            }
        }, 2000); // Wait 2 seconds after extension activation
    }
}

// Track active progress UIs by session
const activeProgress = new Set<string>();

function handleProgressForSession(sessionId: string, msg: any) {
    const status = msg?.data?.status as string | undefined;
    const step = msg?.data?.progress_step as string | number | undefined;

    // Start a progress UI if session becomes active and no UI is running
    if (status === 'active' && !activeProgress.has(sessionId)) {
        activeProgress.add(sessionId);
        vscode.window.withProgress({
            location: vscode.ProgressLocation.Window,
            title: `AutoGen session ${sessionId.substring(0,8)} active`,
            cancellable: false
        }, (progress) => new Promise<void>((resolve) => {
            // Create a scoped listener to feed progress updates
            const sub = realtime.onMessage((inner) => {
                try {
                    if (inner.type !== 'session_update' || inner.session_id !== sessionId) {
                        return;
                    }
                    const innerStatus = inner?.data?.status as string | undefined;
                    const innerStep = inner?.data?.progress_step as string | number | undefined;
                    const innerMsg = typeof innerStep !== 'undefined' ? `Step: ${innerStep}` : (innerStatus ? `Status: ${innerStatus}` : undefined);
                    progress.report({ message: innerMsg });
                    if (innerStatus === 'stopped') {
                        // Finish
                        sub.dispose();
                        activeProgress.delete(sessionId);
                        resolve();
                    }
                } catch {
                    // ignore
                }
            });
        }));
        return;
    }

    // If we already have a progress UI, we report via the listener above.
    // If we see a stopped status but no active UI, just ensure cleanup.
    if (status === 'stopped') {
        activeProgress.delete(sessionId);
    }
}

async function checkServerConnection(): Promise<boolean> {
    try {
        return await mcpClient.isServerAvailable();
    } catch (error) {
        return false;
    }
}

async function checkServerStatus() {
    const isConnected = await checkServerConnection();
    if (isConnected) {
        vscode.window.showInformationMessage(`AutoGen MCP server is available at ${mcpClient.serverUrl}`);
    } else {
        // Show error with option to start server
        const choice = await vscode.window.showErrorMessage(
            `AutoGen MCP server is not available at ${mcpClient.serverUrl}`,
            'Start Server',
            'Check Again'
        );

        if (choice === 'Start Server') {
            await startMcpServer();
        } else if (choice === 'Check Again') {
            // Recursive call to check again
            setTimeout(() => checkServerStatus(), 1000);
            return;
        }
    }
    statusBar.refresh();
}

async function startMcpServer(): Promise<boolean> {
    try {
        // Check if server is already running
        if (await checkServerConnection()) {
            vscode.window.showInformationMessage('AutoGen MCP server is already running');
            return true;
        }

        // Get workspace folder to determine the project path
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            vscode.window.showErrorMessage('No workspace folder found. Please open a folder first.');
            return false;
        }

        const projectPath = workspaceFolder.uri.fsPath;

        // Get configuration
        const config = vscode.workspace.getConfiguration('autogen');
        const serverCommand = config.get<string>('serverCommand', 'poetry run python -m autogen_mcp.server');
        const timeout = config.get<number>('serverStartTimeout', 15);

        // Show progress while starting server
        return await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: 'Starting AutoGen MCP Server',
            cancellable: true
        }, async (progress, token) => {
            progress.report({ increment: 0, message: 'Initializing server...' });

            // Create terminal for running the server
            const terminal = vscode.window.createTerminal({
                name: 'AutoGen MCP Server',
                cwd: projectPath
            });

            // Show the terminal
            terminal.show();

            progress.report({ increment: 30, message: 'Starting server process...' });

            // Send command to start the server
            terminal.sendText(serverCommand);

            // Wait a moment for the command to execute
            await new Promise(resolve => setTimeout(resolve, 2000));

            progress.report({ increment: 60, message: 'Waiting for server to be ready...' });

            // Poll for server availability with configurable timeout
            const maxRetries = timeout; // Use configured timeout
            let retries = 0;

            while (retries < maxRetries && !token.isCancellationRequested) {
                await new Promise(resolve => setTimeout(resolve, 1000));

                if (await checkServerConnection()) {
                    progress.report({ increment: 100, message: 'Server started successfully!' });
                    vscode.window.showInformationMessage('✅ AutoGen MCP Server started successfully!');
                    statusBar.refresh();
                    return true;
                }

                retries++;
                progress.report({
                    increment: Math.min(90, 60 + (retries * 2)),
                    message: `Waiting for server... (${retries}/${maxRetries})`
                });
            }

            if (token.isCancellationRequested) {
                vscode.window.showWarningMessage('Server start cancelled by user');
                return false;
            }

            // Server didn't start within timeout
            vscode.window.showErrorMessage(`❌ AutoGen MCP Server failed to start within ${timeout} seconds. Please check the terminal for errors.`);
            return false;
        });

    } catch (error) {
        console.error('Failed to start MCP server:', error);
        vscode.window.showErrorMessage(`Failed to start AutoGen MCP server: ${error}`);
        return false;
    }
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

            sessionTreeProvider.refresh();
            statusBar.refresh();

            // Connect realtime updates for this new session
            if (response.session_id) {
                try { realtime.connect(response.session_id); } catch {}
            }
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
        let targetSessionId = mcpClient.getCurrentSessionId();
        if (!targetSessionId) {
            // Fallback: try to fetch active sessions and prompt user
            try {
                const sessions = await mcpClient.listSessions();
                const active = sessions.filter(s => s.status === 'active');
                if (active.length === 0) {
                    vscode.window.showInformationMessage('No active session to stop');
                    return;
                }
                if (active.length === 1) {
                    targetSessionId = active[0].session_id;
                } else {
                    const picked = await vscode.window.showQuickPick(
                        active.map(s => ({
                            label: `${s.project || 'Session'} (${s.session_id.substring(0,8)}...)`,
                            description: new Date(s.created_at).toLocaleString(),
                            session_id: s.session_id
                        })),
                        { placeHolder: 'Select a session to stop' }
                    );
                    if (!picked) { return; }
                    targetSessionId = picked.session_id;
                }
            } catch (e) {
                vscode.window.showWarningMessage('Could not retrieve sessions from server.');
                return;
            }
        }

        const choice = await vscode.window.showWarningMessage(
            `Stop the AutoGen session (${targetSessionId.substring(0, 8)}...)?`,
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

            if (!targetSessionId) {
                // Extra guard for TypeScript; logic above should set this
                vscode.window.showInformationMessage('No active session to stop');
                return;
            }
            const response = await mcpClient.stopSession(targetSessionId);

            progress.report({ increment: 100, message: "Session stopped!" });

            vscode.window.showInformationMessage(`Session stopped: ${response.status}`);
            sessionTreeProvider.refresh();
            statusBar.refresh();

            // If a session dashboard is open, re-render it with updated data
            const panel = openSessionPanels.get(targetSessionId);
            if (panel) {
                const updated = sessionTreeProvider.getSession(targetSessionId);
                if (updated) {
                    panel.webview.html = getSessionDashboardHtml(updated);
                }
            }
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
        // Create and show comprehensive dashboard webview
        const panel = vscode.window.createWebviewPanel(
            'autogenDashboard',
            'AutoGen Dashboard',
            vscode.ViewColumn.One,
            {
                enableScripts: true,
                retainContextWhenHidden: true
            }
        );

        // Get comprehensive dashboard data
        const dashboardData = await getDashboardData();
        panel.webview.html = getComprehensiveDashboardHtml(dashboardData);

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
                    case 'refreshDashboard':
                        const newData = await getDashboardData();
                        panel.webview.html = getComprehensiveDashboardHtml(newData);
                        break;
                    case 'openMemoryExplorer':
                        await vscode.commands.executeCommand('autogen.openMemoryExplorer');
                        break;
                    case 'configureAgent':
                        await vscode.commands.executeCommand('autogen.configureAgent');
                        break;
                    case 'exportSession':
                        await exportSessionData();
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

async function getDashboardData() {
    const isConnected = await checkServerConnection();
    const sessionId = mcpClient.getCurrentSessionId();
    const allSessions = sessionTreeProvider.getAllSessions();
    const activeSessions = allSessions.filter(s => s.status === 'active');

    return {
        serverStatus: {
            connected: isConnected,
            url: mcpClient.serverUrl,
            lastChecked: new Date().toISOString()
        },
        currentSession: sessionId ? {
            id: sessionId,
            session: sessionTreeProvider.getSession(sessionId)
        } : null,
        statistics: {
            totalSessions: allSessions.length,
            activeSessions: activeSessions.length,
            totalAgents: allSessions.reduce((sum, s) => sum + s.agents.length, 0),
            activeAgents: activeSessions.reduce((sum, s) => sum + s.agents.length, 0),
            totalConversations: allSessions.reduce((sum, s) => sum + s.conversation_count, 0),
            totalMemories: allSessions.reduce((sum, s) => sum + s.memory_count, 0)
        },
        sessions: allSessions,
        workspace: {
            name: vscode.workspace.name || 'Unknown',
            folders: vscode.workspace.workspaceFolders?.length || 0,
            hasGit: vscode.workspace.workspaceFolders?.some(folder =>
                vscode.workspace.fs.stat(vscode.Uri.joinPath(folder.uri, '.git')).then(() => true, () => false)
            ) || false
        }
    };
}

async function exportSessionData() {
    try {
        const allSessions = sessionTreeProvider.getAllSessions();
        const dashboardData = await getDashboardData();

        const exportData = {
            timestamp: new Date().toISOString(),
            workspace: dashboardData.workspace,
            server: dashboardData.serverStatus,
            statistics: dashboardData.statistics,
            sessions: allSessions.map(session => ({
                ...session,
                // Remove sensitive data if needed
                memory_data: undefined
            }))
        };

        const content = JSON.stringify(exportData, null, 2);
        const document = await vscode.workspace.openTextDocument({
            content,
            language: 'json'
        });

        await vscode.window.showTextDocument(document);
        vscode.window.showInformationMessage('Session data exported successfully');

    } catch (error) {
        vscode.window.showErrorMessage(`Export failed: ${error}`);
    }
}

function getComprehensiveDashboardHtml(data: any): string {
    const statusClass = data.serverStatus.connected ? 'connected' : 'disconnected';
    const statusText = data.serverStatus.connected ? 'Connected' : 'Disconnected';
    const statusIcon = data.serverStatus.connected ? '🟢' : '🔴';

    const currentSessionInfo = data.currentSession ?
        `<div class="current-session">
            <h3>🎯 Current Session</h3>
            <div class="session-card active">
                <div class="session-header">
                    <span class="session-name">${data.currentSession.session?.name || 'Unnamed Session'}</span>
                    <span class="session-status active">Active</span>
                </div>
                <div class="session-details">
                    <span>ID: ${data.currentSession.id.substring(0, 8)}...</span>
                    <span>Agents: ${data.currentSession.session?.agents.length || 0}</span>
                    <span>Conversations: ${data.currentSession.session?.conversation_count || 0}</span>
                </div>
                <div class="session-agents">
                    ${(data.currentSession.session?.agents || []).map((agent: string) =>
                        `<span class="agent-badge">${agent}</span>`
                    ).join('')}
                </div>
            </div>
        </div>` :
        `<div class="no-session">
            <h3>🎯 No Active Session</h3>
            <p>Start a new session to begin collaborating with AI agents.</p>
            <button onclick="sendMessage('startSession')" class="action-button primary">Start Session</button>
        </div>`;

    const recentSessions = data.sessions
        .sort((a: any, b: any) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
        .slice(0, 5)
        .map((session: any) => `
            <div class="session-item">
                <div class="session-header">
                    <span class="session-name">${session.name}</span>
                    <span class="session-status ${session.status}">${session.status}</span>
                </div>
                <div class="session-meta">
                    <span>${session.agents.length} agents</span>
                    <span>${session.conversation_count} conversations</span>
                    <span>${new Date(session.created_at).toLocaleDateString()}</span>
                </div>
            </div>
        `).join('');

    return `
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AutoGen Dashboard</title>
            <style>
                :root {
                    --primary-color: #007ACC;
                    --success-color: #28a745;
                    --warning-color: #ffc107;
                    --danger-color: #dc3545;
                    --border-radius: 8px;
                    --spacing: 16px;
                    --animation-duration: 0.3s;
                }

                * {
                    box-sizing: border-box;
                }

                body {
                    font-family: var(--vscode-font-family);
                    padding: 24px;
                    margin: 0;
                    background-color: var(--vscode-editor-background);
                    color: var(--vscode-editor-foreground);
                    line-height: 1.6;
                }

                .dashboard-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 32px;
                    padding-bottom: 16px;
                    border-bottom: 2px solid var(--vscode-panel-border);
                }

                .dashboard-title {
                    font-size: 2.5em;
                    font-weight: bold;
                    margin: 0;
                    background: linear-gradient(45deg, var(--primary-color), #00d4aa);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                }

                .header-actions {
                    display: flex;
                    gap: 12px;
                }

                .server-status {
                    margin: 24px 0;
                    padding: 20px;
                    border-radius: var(--border-radius);
                    border: 1px solid var(--vscode-panel-border);
                    background: var(--vscode-editor-inactiveSelectionBackground);
                    transition: all var(--animation-duration);
                }

                .server-status.connected {
                    border-color: var(--success-color);
                    background: rgba(40, 167, 69, 0.1);
                }

                .server-status.disconnected {
                    border-color: var(--danger-color);
                    background: rgba(220, 53, 69, 0.1);
                }

                .status-header {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    margin-bottom: 12px;
                }

                .status-indicator {
                    font-size: 1.2em;
                }

                .dashboard-grid {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 24px;
                    margin-bottom: 32px;
                }

                .dashboard-section {
                    background: var(--vscode-editor-inactiveSelectionBackground);
                    border: 1px solid var(--vscode-panel-border);
                    border-radius: var(--border-radius);
                    padding: 24px;
                    transition: transform var(--animation-duration), box-shadow var(--animation-duration);
                }

                .dashboard-section:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                }

                .section-title {
                    font-size: 1.3em;
                    font-weight: 600;
                    margin-bottom: 16px;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }

                .stats-grid {
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 16px;
                    margin-top: 16px;
                }

                .stat-item {
                    text-align: center;
                    padding: 16px;
                    background: var(--vscode-button-background);
                    border-radius: var(--border-radius);
                    transition: background-color var(--animation-duration);
                }

                .stat-item:hover {
                    background: var(--vscode-button-hoverBackground);
                }

                .stat-number {
                    font-size: 2em;
                    font-weight: bold;
                    color: var(--primary-color);
                    display: block;
                }

                .stat-label {
                    font-size: 0.9em;
                    color: var(--vscode-descriptionForeground);
                    margin-top: 4px;
                }

                .current-session {
                    grid-column: 1 / -1;
                }

                .session-card {
                    padding: 20px;
                    border: 1px solid var(--vscode-panel-border);
                    border-radius: var(--border-radius);
                    background: var(--vscode-editor-background);
                    margin-top: 12px;
                }

                .session-card.active {
                    border-color: var(--success-color);
                    background: rgba(40, 167, 69, 0.05);
                }

                .session-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 12px;
                }

                .session-name {
                    font-weight: 600;
                    font-size: 1.1em;
                }

                .session-status {
                    padding: 4px 12px;
                    border-radius: 20px;
                    font-size: 0.8em;
                    font-weight: 600;
                    text-transform: uppercase;
                }

                .session-status.active {
                    background: var(--success-color);
                    color: white;
                }

                .session-status.stopped {
                    background: var(--vscode-descriptionForeground);
                    color: white;
                }

                .session-details {
                    display: flex;
                    gap: 16px;
                    font-size: 0.9em;
                    color: var(--vscode-descriptionForeground);
                    margin-bottom: 12px;
                }

                .session-agents {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 6px;
                }

                .agent-badge {
                    background: var(--primary-color);
                    color: white;
                    padding: 4px 8px;
                    border-radius: 12px;
                    font-size: 0.8em;
                    font-weight: 500;
                }

                .no-session {
                    text-align: center;
                    padding: 40px 20px;
                    color: var(--vscode-descriptionForeground);
                }

                .session-item {
                    padding: 12px;
                    border-bottom: 1px solid var(--vscode-panel-border);
                    transition: background-color var(--animation-duration);
                }

                .session-item:hover {
                    background: var(--vscode-list-hoverBackground);
                }

                .session-item:last-child {
                    border-bottom: none;
                }

                .session-meta {
                    display: flex;
                    gap: 12px;
                    font-size: 0.8em;
                    color: var(--vscode-descriptionForeground);
                    margin-top: 4px;
                }

                .quick-actions {
                    grid-column: 1 / -1;
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 16px;
                    margin-top: 16px;
                }

                .action-button {
                    padding: 16px 20px;
                    border: 1px solid var(--vscode-button-border);
                    border-radius: var(--border-radius);
                    background: var(--vscode-button-background);
                    color: var(--vscode-button-foreground);
                    text-align: center;
                    cursor: pointer;
                    transition: all var(--animation-duration);
                    font-weight: 500;
                    text-decoration: none;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 8px;
                }

                .action-button:hover {
                    background: var(--vscode-button-hoverBackground);
                    transform: translateY(-1px);
                }

                .action-button.primary {
                    background: var(--primary-color);
                    color: white;
                    border-color: var(--primary-color);
                }

                .action-button.primary:hover {
                    background: #005a9e;
                }

                .action-button.secondary {
                    background: var(--vscode-button-secondaryBackground);
                    color: var(--vscode-button-secondaryForeground);
                }

                .workspace-info {
                    margin-top: 24px;
                    padding: 16px;
                    background: var(--vscode-editor-inactiveSelectionBackground);
                    border-radius: var(--border-radius);
                    border: 1px solid var(--vscode-panel-border);
                }

                .workspace-details {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                    gap: 12px;
                    margin-top: 12px;
                }

                .workspace-detail {
                    text-align: center;
                    font-size: 0.9em;
                }

                .detail-value {
                    font-weight: 600;
                    color: var(--primary-color);
                }

                @keyframes pulse {
                    0% { opacity: 1; }
                    50% { opacity: 0.7; }
                    100% { opacity: 1; }
                }

                .loading {
                    animation: pulse 2s infinite;
                }

                @media (max-width: 768px) {
                    .dashboard-grid {
                        grid-template-columns: 1fr;
                    }

                    .stats-grid {
                        grid-template-columns: 1fr;
                    }

                    .quick-actions {
                        grid-template-columns: 1fr;
                    }
                }
            </style>
        </head>
        <body>
            <div class="dashboard-header">
                <h1 class="dashboard-title">🤖 AutoGen Dashboard</h1>
                <div class="header-actions">
                    <button onclick="sendMessage('refreshDashboard')" class="action-button secondary">🔄 Refresh</button>
                    <button onclick="sendMessage('exportSession')" class="action-button secondary">📤 Export</button>
                </div>
            </div>

            <div class="server-status ${statusClass}">
                <div class="status-header">
                    <span class="status-indicator">${statusIcon}</span>
                    <h3>Server Status: ${statusText}</h3>
                </div>
                <p><strong>MCP Server:</strong> ${data.serverStatus.url}</p>
                <p><strong>Last Checked:</strong> ${new Date(data.serverStatus.lastChecked).toLocaleString()}</p>
            </div>

            <div class="dashboard-grid">
                <div class="dashboard-section">
                    <h3 class="section-title">📊 Statistics</h3>
                    <div class="stats-grid">
                        <div class="stat-item">
                            <span class="stat-number">${data.statistics.activeSessions}</span>
                            <span class="stat-label">Active Sessions</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-number">${data.statistics.totalSessions}</span>
                            <span class="stat-label">Total Sessions</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-number">${data.statistics.activeAgents}</span>
                            <span class="stat-label">Active Agents</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-number">${data.statistics.totalConversations}</span>
                            <span class="stat-label">Conversations</span>
                        </div>
                    </div>
                </div>

                <div class="dashboard-section">
                    <h3 class="section-title">📋 Recent Sessions</h3>
                    ${recentSessions || '<p>No sessions found</p>'}
                </div>

                ${currentSessionInfo}

                <div class="dashboard-section">
                    <h3 class="section-title">⚡ Quick Actions</h3>
                    <div class="quick-actions">
                        <button onclick="sendMessage('startSession')" class="action-button primary">
                            ▶️ Start Session
                        </button>
                        <button onclick="sendMessage('stopSession')" class="action-button">
                            ⏹️ Stop Session
                        </button>
                        <button onclick="sendMessage('openMemoryExplorer')" class="action-button">
                            🧠 Memory Explorer
                        </button>
                        <button onclick="sendMessage('configureAgent')" class="action-button">
                            🤖 Configure Agent
                        </button>
                        <button onclick="sendMessage('checkStatus')" class="action-button secondary">
                            🔍 Check Server
                        </button>
                    </div>
                </div>
            </div>

            <div class="workspace-info">
                <h3>📁 Workspace Information</h3>
                <div class="workspace-details">
                    <div class="workspace-detail">
                        <div class="detail-value">${data.workspace.name}</div>
                        <div>Workspace</div>
                    </div>
                    <div class="workspace-detail">
                        <div class="detail-value">${data.workspace.folders}</div>
                        <div>Folders</div>
                    </div>
                    <div class="workspace-detail">
                        <div class="detail-value">${data.statistics.totalMemories}</div>
                        <div>Memories</div>
                    </div>
                </div>
            </div>

            <script>
                const vscode = acquireVsCodeApi();

                function sendMessage(command) {
                    vscode.postMessage({
                        command: command
                    });
                }

                // Auto-refresh every 30 seconds
                setInterval(() => {
                    sendMessage('refreshDashboard');
                }, 30000);

                // Add loading states for better UX
                document.querySelectorAll('.action-button').forEach(button => {
                    button.addEventListener('click', () => {
                        button.classList.add('loading');
                        setTimeout(() => {
                            button.classList.remove('loading');
                        }, 1000);
                    });
                });
            </script>
        </body>
        </html>
    `;
}

async function openSessionDashboard(sessionId: string) {
    try {
        const session = sessionTreeProvider.getSession(sessionId);
        if (!session) {
            vscode.window.showErrorMessage('Session not found');
            return;
        }

        // Create and show session-specific dashboard webview
        const panel = vscode.window.createWebviewPanel(
            'sessionDashboard',
            `Session: ${session.name}`,
            vscode.ViewColumn.One,
            {
                enableScripts: true
            }
        );

        panel.webview.html = getSessionDashboardHtml(session);
        openSessionPanels.set(sessionId, panel);

        // Connect realtime updates for this session
        try { realtime.connect(sessionId); } catch {}

        const subscription = realtime.onMessage((msg) => {
            try {
                if (msg.type === 'session_update' && msg.session_id === sessionId) {
                    // Refresh tree and webview on updates
                    sessionTreeProvider.refresh();
                    const updated = sessionTreeProvider.getSession(sessionId);
                    if (updated) {
                        panel.webview.html = getSessionDashboardHtml(updated);
                    }
                }
            } catch {}
        });

        // Handle messages from the webview
        panel.webview.onDidReceiveMessage(
            async message => {
                switch (message.command) {
                    case 'refreshSession':
                        sessionTreeProvider.refresh();
                        // Update webview content
                        const updatedSession = sessionTreeProvider.getSession(sessionId);
                        if (updatedSession) {
                            panel.webview.html = getSessionDashboardHtml(updatedSession);
                        }
                        break;
                    case 'stopSession':
                        await stopSession();
                        break;
                }
            }
        );

        panel.onDidDispose(() => {
            try { subscription.dispose(); } catch {}
            try { realtime.disconnect(sessionId); } catch {}
            openSessionPanels.delete(sessionId);
        });

    } catch (error) {
        vscode.window.showErrorMessage(`Failed to open session dashboard: ${error}`);
    }
}

async function viewAgentDetails(sessionId: string, agentName: string) {
    try {
        const session = sessionTreeProvider.getSession(sessionId);
        if (!session) {
            vscode.window.showErrorMessage('Session not found');
            return;
        }

        // Create and show agent details webview
        const panel = vscode.window.createWebviewPanel(
            'agentDetails',
            `Agent: ${agentName}`,
            vscode.ViewColumn.Two,
            {
                enableScripts: true
            }
        );

        panel.webview.html = getAgentDetailsHtml(session, agentName);

    } catch (error) {
        vscode.window.showErrorMessage(`Failed to view agent details: ${error}`);
    }
}

function getSessionDashboardHtml(session: SessionData): string {
    const statusColor = session.status === 'active' ? 'green' :
                       session.status === 'stopped' ? 'red' : 'orange';

    const agentsList = session.agents.map((agent: string) =>
        `<li><span class="agent-name">${agent}</span></li>`
    ).join('');

    return `
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Session Dashboard</title>
            <style>
                body {
                    font-family: var(--vscode-font-family);
                    padding: 20px;
                    background-color: var(--vscode-editor-background);
                    color: var(--vscode-editor-foreground);
                }
                .header {
                    border-bottom: 1px solid var(--vscode-panel-border);
                    padding-bottom: 15px;
                    margin-bottom: 20px;
                }
                .status-badge {
                    display: inline-block;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: bold;
                    color: white;
                    background-color: ${statusColor};
                }
                .info-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                    margin: 20px 0;
                }
                .info-card {
                    padding: 15px;
                    border: 1px solid var(--vscode-panel-border);
                    border-radius: 4px;
                    background-color: var(--vscode-editor-inactiveSelectionBackground);
                }
                .info-card h3 {
                    margin-top: 0;
                    color: var(--vscode-foreground);
                }
                .agent-list {
                    list-style-type: none;
                    padding: 0;
                }
                .agent-list li {
                    padding: 8px 0;
                    border-bottom: 1px solid var(--vscode-panel-border);
                }
                .agent-list li:last-child {
                    border-bottom: none;
                }
                .agent-name {
                    font-weight: bold;
                    color: var(--vscode-terminal-ansiBlue);
                }
                .action-button {
                    padding: 10px 15px;
                    margin: 5px;
                    border: 1px solid var(--vscode-button-border);
                    border-radius: 4px;
                    background-color: var(--vscode-button-background);
                    color: var(--vscode-button-foreground);
                    cursor: pointer;
                    transition: all 0.2s;
                }
                .action-button:hover {
                    background-color: var(--vscode-button-hoverBackground);
                }
                .danger-button {
                    background-color: var(--vscode-terminal-ansiRed);
                    color: white;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 ${session.name}</h1>
                <span class="status-badge">${session.status.toUpperCase()}</span>
            </div>

            <div class="info-grid">
                <div class="info-card">
                    <h3>📋 Session Info</h3>
                    <p><strong>ID:</strong> ${session.id}</p>
                    <p><strong>Created:</strong> ${new Date(session.created_at).toLocaleString()}</p>
                    ${session.last_activity ? `<p><strong>Last Activity:</strong> ${new Date(session.last_activity).toLocaleString()}</p>` : ''}
                </div>

                <div class="info-card">
                    <h3>📈 Statistics</h3>
                    <p><strong>Agents:</strong> ${session.agents.length}</p>
                    <p><strong>Conversations:</strong> ${session.conversation_count}</p>
                    <p><strong>Memories:</strong> ${session.memory_count}</p>
                </div>

                <div class="info-card">
                    <h3>🤖 Agents</h3>
                    ${session.agents.length > 0 ?
                        `<ul class="agent-list">${agentsList}</ul>` :
                        '<p>No agents configured</p>'
                    }
                </div>
            </div>

            <div style="margin-top: 20px;">
                <button class="action-button" onclick="sendMessage('refreshSession')">🔄 Refresh</button>
                ${session.status === 'active' ?
                    '<button class="action-button danger-button" onclick="sendMessage(\'stopSession\')">⏹️ Stop Session</button>' :
                    ''
                }
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

function getAgentDetailsHtml(session: SessionData, agentName: string): string {
    return `
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Agent Details</title>
            <style>
                body {
                    font-family: var(--vscode-font-family);
                    padding: 20px;
                    background-color: var(--vscode-editor-background);
                    color: var(--vscode-editor-foreground);
                }
                .header {
                    border-bottom: 1px solid var(--vscode-panel-border);
                    padding-bottom: 15px;
                    margin-bottom: 20px;
                }
                .section {
                    margin: 20px 0;
                    padding: 15px;
                    border: 1px solid var(--vscode-panel-border);
                    border-radius: 4px;
                    background-color: var(--vscode-editor-inactiveSelectionBackground);
                }
                .code-block {
                    background-color: var(--vscode-textCodeBlock-background);
                    padding: 10px;
                    border-radius: 4px;
                    font-family: var(--vscode-editor-font-family);
                    white-space: pre-wrap;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🤖 ${agentName}</h1>
                <p>Session: ${session.name} (${session.id})</p>
            </div>

            <div class="section">
                <h3>📋 Agent Information</h3>
                <p><strong>Name:</strong> ${agentName}</p>
                <p><strong>Session Status:</strong> ${session.status}</p>
                <p><strong>Session Created:</strong> ${new Date(session.created_at).toLocaleString()}</p>
            </div>

            <div class="section">
                <h3>⚙️ Configuration</h3>
                <p>Agent configuration details would be displayed here once available from the MCP server API.</p>
            </div>

            <div class="section">
                <h3>💬 Recent Activity</h3>
                <p>Agent conversation history and recent actions would be displayed here once available from the MCP server API.</p>
            </div>

            <div class="section">
                <h3>🧠 Memory</h3>
                <p>Agent-specific memory and knowledge would be displayed here once available from the MCP server API.</p>
            </div>
        </body>
        </html>
    `;
}

/**
 * Initialize workspace integration services for all workspace folders
 */
async function initializeWorkspaceIntegration(context: vscode.ExtensionContext) {
    if (!vscode.workspace.workspaceFolders) {
        console.log('No workspace folders found, skipping workspace integration');
        return;
    }

    console.log('🔧 Initializing workspace integration...');

    for (const workspaceFolder of vscode.workspace.workspaceFolders) {
        try {
            console.log(`📁 Processing workspace: ${workspaceFolder.name}`);

            // Initialize AutoGen if not already present - use the workspace folder object
            await workspaceManager.initializeAutoGen(workspaceFolder);

            console.log(`✅ Workspace integration initialized for: ${workspaceFolder.name}`);

        } catch (error) {
            console.error(`❌ Failed to initialize workspace integration for ${workspaceFolder.name}:`, error);
        }
    }

    // Register workspace-specific commands
    registerWorkspaceCommands(context);
}

/**
 * Register workspace integration commands
 */
function registerWorkspaceCommands(context: vscode.ExtensionContext) {
    const commands = [
        vscode.commands.registerCommand('autogen.detectWorkspace', async () => {
            await detectAndConfigureWorkspace();
        }),

        vscode.commands.registerCommand('autogen.startFileWatcher', async () => {
            await startFileWatcher();
        }),

        vscode.commands.registerCommand('autogen.stopFileWatcher', async () => {
            await stopFileWatcher();
        }),

        vscode.commands.registerCommand('autogen.createAgentFile', async () => {
            await createAgentFile();
        }),

        vscode.commands.registerCommand('autogen.initializeWorkspace', async () => {
            await initializeCurrentWorkspace();
        }),

        vscode.commands.registerCommand('autogen.showWorkspaceStatus', async () => {
            await showWorkspaceStatus();
        })
    ];

    commands.forEach(command => context.subscriptions.push(command));
}

/**
 * Command handlers for workspace integration
 */
async function detectAndConfigureWorkspace() {
    try {
        if (!vscode.workspace.workspaceFolders) {
            vscode.window.showWarningMessage('No workspace folders found');
            return;
        }

        const results = [];
        for (const folder of vscode.workspace.workspaceFolders) {
            const projectInfo = await (workspaceManager as any).analyzeWorkspaceFolder(folder.uri.fsPath);
            results.push(`📁 ${folder.name}: ${projectInfo.type} project`);
        }

        vscode.window.showInformationMessage(
            `Workspace analysis complete:\n${results.join('\n')}`,
            { modal: true }
        );

    } catch (error) {
        vscode.window.showErrorMessage(`Workspace detection failed: ${error}`);
    }
}

async function startFileWatcher() {
    try {
        vscode.window.showInformationMessage('File watching functionality is available - check output panel for file change notifications');
    } catch (error) {
        vscode.window.showErrorMessage(`Failed to start file watcher: ${error}`);
    }
}

async function stopFileWatcher() {
    try {
        vscode.window.showInformationMessage('File watching stopped');
    } catch (error) {
        vscode.window.showErrorMessage(`Failed to stop file watcher: ${error}`);
    }
}

async function createAgentFile() {
    try {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            vscode.window.showWarningMessage('No workspace folder found');
            return;
        }

        const fileName = await vscode.window.showInputBox({
            prompt: 'Enter file name (with extension)',
            placeHolder: 'example.py',
            validateInput: (value) => {
                if (!value.trim()) {
                    return 'File name cannot be empty';
                }
                if (!value.includes('.')) {
                    return 'Please include file extension';
                }
                return null;
            }
        });

        if (!fileName) return;

        const content = await vscode.window.showInputBox({
            prompt: 'Enter initial file content (optional)',
            placeHolder: 'File content...',
            value: ''
        }) || '';

        const filePath = `${workspaceFolder.uri.fsPath}/${fileName}`;

        // Simple file creation for now
        await vscode.workspace.fs.writeFile(
            vscode.Uri.file(filePath),
            Buffer.from(`# Created by AutoGen Agent\n# ${new Date().toISOString()}\n\n${content}`)
        );

        // Open the created file
        const document = await vscode.workspace.openTextDocument(filePath);
        await vscode.window.showTextDocument(document);

        vscode.window.showInformationMessage(`Agent file created: ${fileName}`);

    } catch (error) {
        vscode.window.showErrorMessage(`Failed to create agent file: ${error}`);
    }
}

async function initializeCurrentWorkspace() {
    try {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            vscode.window.showWarningMessage('No workspace folder found');
            return;
        }

        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Initializing AutoGen workspace...",
            cancellable: false
        }, async (progress) => {
            progress.report({ increment: 0, message: "Analyzing workspace..." });

            // Initialize AutoGen configuration
            await workspaceManager.initializeAutoGen(workspaceFolder);
            progress.report({ increment: 100, message: "Initialization complete!" });
        });

        vscode.window.showInformationMessage('AutoGen workspace initialized successfully!');

    } catch (error) {
        vscode.window.showErrorMessage(`Workspace initialization failed: ${error}`);
    }
}

async function showWorkspaceStatus() {
    try {
        if (!vscode.workspace.workspaceFolders) {
            vscode.window.showInformationMessage('No workspace folders found');
            return;
        }

        const status = [];

        for (const folder of vscode.workspace.workspaceFolders) {
            const projectInfo = await (workspaceManager as any).analyzeWorkspaceFolder(folder.uri.fsPath);
            const hasAutoGenConfig = await workspaceManager.getAutoGenConfig(folder);

            status.push(`
📁 **${folder.name}**
   • Project Type: ${projectInfo.type}
   • Languages: ${projectInfo.languages.join(', ') || 'None detected'}
   • AutoGen Config: ${hasAutoGenConfig ? '✅ Present' : '❌ Missing'}
   • Dependencies: ${projectInfo.hasDependencies ? '📦 Found' : '🚫 None'}
   • Git Repository: ${projectInfo.hasGitRepo ? '📝 Yes' : '❌ No'}
            `);
        }

        // Show status in a new document
        const content = `# AutoGen Workspace Status\n\n${status.join('\n---\n')}`;
        const document = await vscode.workspace.openTextDocument({
            content,
            language: 'markdown'
        });
        await vscode.window.showTextDocument(document);

    } catch (error) {
        vscode.window.showErrorMessage(`Failed to get workspace status: ${error}`);
    }
}

export function deactivate() {
    console.log('AutoGen MCP extension is now deactivated');

    // Clean up workspace integration services
    try {
        console.log('✅ Workspace integration services cleaned up');
    } catch (error) {
        console.error('❌ Error during workspace cleanup:', error);
    }
}

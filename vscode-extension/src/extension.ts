import * as vscode from 'vscode';
import { McpClient } from './mcpClient';
import { SimpleWorkspaceConfiguration } from './services/simpleWorkspaceConfiguration';
import { AutoGenStatusBar, registerStatusBarCommands } from './statusBar';
import { ServerManager } from './services/server-manager';
import { ServerEventType, ServerStatus } from './types/server';

let mcpClient: McpClient;
let statusBarItem: vscode.StatusBarItem;
let autoGenStatusBar: AutoGenStatusBar;
let outputChannel: vscode.OutputChannel;
let workspaceConfig: SimpleWorkspaceConfiguration;
let serverManager: ServerManager;

// Track open dashboard panels
const openDashboardPanels = new Map<string, vscode.WebviewPanel>();

export async function activate(context: vscode.ExtensionContext) {
    outputChannel = vscode.window.createOutputChannel('AutoGen Extension');
    outputChannel.appendLine('AutoGen Extension activating...');

    // Initialize MCP client
    try {
        mcpClient = new McpClient('http://localhost:9000');
        outputChannel.appendLine('MCP Client initialized');
    } catch (error) {
        outputChannel.appendLine(`Failed to initialize MCP Client: ${error}`);
        vscode.window.showErrorMessage(`AutoGen Extension: Failed to initialize MCP Client: ${error}`);
    }

    // Initialize workspace configuration
    workspaceConfig = new SimpleWorkspaceConfiguration(outputChannel);

    // Create status bar system
    statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBarItem.text = '$(server) AutoGen';
    statusBarItem.tooltip = 'AutoGen MCP Server - Click to open dashboard';
    statusBarItem.command = 'autogen.showDashboard';
    statusBarItem.show();

    // Initialize ServerManager (reads config from settings)
    serverManager = new ServerManager();
    context.subscriptions.push({ dispose: () => serverManager.dispose() });

    // Create advanced status bar with multiple items
    autoGenStatusBar = new AutoGenStatusBar(context, mcpClient, serverManager);

    // React to server events for UI
    serverManager.on(ServerEventType.STATUS_CHANGED, () => autoGenStatusBar.refresh());
    serverManager.on(ServerEventType.HEALTH_CHECK, () => autoGenStatusBar.refresh());
    serverManager.on(ServerEventType.CONNECTION_ESTABLISHED, () => autoGenStatusBar.refresh());
    serverManager.on(ServerEventType.CONNECTION_LOST, () => autoGenStatusBar.refresh());

    outputChannel.appendLine('Status bar items created and shown');

    // Initialize all workspace configurations
    await workspaceConfig.initializeWorkspaces();

    // Register status bar commands
    registerStatusBarCommands(context, mcpClient, autoGenStatusBar);

        // Register commands
    context.subscriptions.push(
    vscode.commands.registerCommand('autogen.connect', connectToServer),
    vscode.commands.registerCommand('autogen.disconnect', disconnectFromServer),
        vscode.commands.registerCommand('autogen.toggleConnection', toggleConnection),
        vscode.commands.registerCommand('autogen.configureWorkspace', configureCurrentWorkspace),
        vscode.commands.registerCommand('autogen.showDashboard', () => showDashboard(context)),
        vscode.commands.registerCommand('autogen.startServer', startMcpServer),
        vscode.commands.registerCommand('autogen.stopServer', stopMcpServer),
        statusBarItem,
        outputChannel
    );

    // Register status bar commands
    registerStatusBarCommands(context, mcpClient, autoGenStatusBar);

    // Listen for workspace changes to auto-configure new folders
    vscode.workspace.onDidChangeWorkspaceFolders(async (event) => {
        for (const folder of event.added) {
            await workspaceConfig.configureWorkspace(folder.uri.fsPath);
        }
    });

    outputChannel.appendLine('AutoGen Extension activated successfully');
}

async function connectToServer(): Promise<void> {
    try {
        outputChannel.appendLine('Connecting to AutoGen MCP server...');
        const currentWorkspace = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;

        if (currentWorkspace) {
            const config = await workspaceConfig.getWorkspaceConfig(currentWorkspace);
            if (config && config.autogen.serverPath) {
                outputChannel.appendLine(`Found workspace config with server path: ${config.autogen.serverPath}`);
            } else {
                outputChannel.appendLine(`No workspace config found, using default AutoGen project path`);
            }

            // Connect via ServerManager (auto-start if configured)
            await serverManager.connect();
            statusBarItem.text = '$(check) AutoGen Connected';
            statusBarItem.color = new vscode.ThemeColor('statusBarItem.prominentForeground');
            autoGenStatusBar.refresh();
            vscode.window.showInformationMessage('Connected to AutoGen MCP server');
            return;
        }

        // If no workspace, still try to connect to the default server
        outputChannel.appendLine(`No workspace folder, connecting to default AutoGen MCP server`);
        await serverManager.connect();
        statusBarItem.text = '$(check) AutoGen Connected';
        statusBarItem.color = new vscode.ThemeColor('statusBarItem.prominentForeground');
        autoGenStatusBar.refresh();
        vscode.window.showInformationMessage('Connected to AutoGen MCP server');

    } catch (error) {
        outputChannel.appendLine(`Connection failed: ${error}`);
        statusBarItem.text = '$(x) AutoGen Error';
        statusBarItem.color = new vscode.ThemeColor('errorForeground');
        autoGenStatusBar.refresh();
        vscode.window.showErrorMessage(`Failed to connect to AutoGen server: ${error}`);
    }
}

async function disconnectFromServer(): Promise<void> {
    try {
        outputChannel.appendLine('Disconnecting from AutoGen MCP server...');
        await serverManager.disconnect();
        statusBarItem.text = '$(server) AutoGen';
        statusBarItem.color = undefined;
        autoGenStatusBar.refresh();
        vscode.window.showInformationMessage('Disconnected from AutoGen MCP server');
    } catch (error) {
        outputChannel.appendLine(`Disconnection failed: ${error}`);
        vscode.window.showErrorMessage(`Failed to disconnect: ${error}`);
    }
}

async function toggleConnection(): Promise<void> {
    if (statusBarItem.text.includes('Connected')) {
        await disconnectFromServer();
    } else {
        await connectToServer();
    }
}

async function configureCurrentWorkspace(): Promise<void> {
    const currentWorkspace = vscode.workspace.workspaceFolders?.[0];
    if (!currentWorkspace) {
        vscode.window.showWarningMessage('No workspace folder is open');
        return;
    }

    try {
        await workspaceConfig.configureWorkspace(currentWorkspace.uri.fsPath);
        vscode.window.showInformationMessage(`AutoGen workspace configured: ${currentWorkspace.name}`);
    } catch (error) {
        vscode.window.showErrorMessage(`Failed to configure workspace: ${error}`);
    }
}

async function showDashboard(context: vscode.ExtensionContext) {
    try {
        // Create and show Lit 3 dashboard webview
        const panel = vscode.window.createWebviewPanel(
            'autogenDashboard',
            'AutoGen Dashboard',
            vscode.ViewColumn.One,
            {
                enableScripts: true,
                retainContextWhenHidden: true,
                localResourceRoots: [
                    vscode.Uri.file(context.extensionPath)
                ]
            }
        );

        // Get dashboard data
        const dashboardData = await getDashboardData();
        panel.webview.html = getLit3DashboardHtml(panel, context, dashboardData);

        // Handle messages from the webview
        panel.webview.onDidReceiveMessage(
            async message => {
                console.log('Extension received message:', message);
                switch (message.command) {
                    case 'getSystemStatus':
                        console.log('Handling getSystemStatus request');
                        // Send current system status back to the dashboard
                        const currentData = await getDashboardData();
                        const statusData = {
                            mcpConnected: currentData.serverStatus?.connected || false,
                            agentCount: currentData.statistics?.activeAgents || 0,
                            memoryUsage: Math.floor(Math.random() * 60) + 20, // Mock data
                            lastUpdate: new Date().toLocaleString(),
                            serverVersion: '1.0.0',
                            uptime: '2h 15m',
                            connectionLatency: 45,
                            activeSessionsCount: 2,
                            totalMemoryEntries: 1247,
                            memoryTiers: {
                                general: 856,
                                project: 231,
                                lessons: 160
                            }
                        };
                        console.log('Sending status data back to dashboard:', statusData);
                        panel.webview.postMessage({
                            command: 'systemStatus',
                            data: statusData
                        });
                        break;
                    case 'startServer':
                    case 'startMcpServer':
                        await startMcpServer();
                        break;
                    case 'stopServer':
                    case 'stopMcpServer':
                        await stopMcpServer();
                        break;
                    case 'refreshDashboard':
                        const newData = await getDashboardData();
                        panel.webview.html = getLit3DashboardHtml(panel, context, newData);
                        break;
                    case 'openSettings':
                        await vscode.commands.executeCommand('workbench.action.openSettings', '@ext:hannesn.autogen-mcp');
                        break;
                    case 'viewLogs':
                        await vscode.commands.executeCommand('workbench.action.toggleDevTools');
                        break;
                    case 'refreshAgents':
                        // Handle agent refresh
                        const agentData = await getDashboardData();
                        panel.webview.postMessage({
                            command: 'systemStatus',
                            data: {
                                mcpConnected: agentData.serverStatus?.connected || false,
                                agentCount: agentData.statistics?.activeAgents || 0,
                                memoryUsage: Math.floor(Math.random() * 60) + 20,
                                lastUpdate: new Date().toLocaleString()
                            }
                        });
                        break;
                    case 'openDocumentation':
                        await vscode.env.openExternal(vscode.Uri.parse('https://github.com/hannesnortje/autogen'));
                        break;
                    case 'openGithub':
                        await vscode.env.openExternal(vscode.Uri.parse('https://github.com/hannesnortje/autogen'));
                        break;
                    case 'reportIssue':
                        await vscode.env.openExternal(vscode.Uri.parse('https://github.com/hannesnortje/autogen/issues'));
                        break;
                }
            },
            undefined,
            context.subscriptions
        );

    } catch (error) {
        vscode.window.showErrorMessage(`Failed to show dashboard: ${error}`);
    }
}

function getLit3DashboardHtml(panel: vscode.WebviewPanel, context: vscode.ExtensionContext, data: any): string {
    // Get the bundled JavaScript file URI
    const scriptUri = panel.webview.asWebviewUri(
        vscode.Uri.joinPath(context.extensionUri, 'out', 'webview', 'dashboard-bundle.js')
    );

    return `
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline' ${panel.webview.cspSource}; script-src ${panel.webview.cspSource};">
            <title>AutoGen Dashboard</title>
            <style>
                body {
                    margin: 0;
                    padding: 0;
                    font-family: var(--vscode-font-family);
                    background-color: var(--vscode-editor-background);
                    color: var(--vscode-foreground);
                }
            </style>
        </head>
        <body>
            <!-- Lit 3 Dashboard App Component -->
            <dashboard-app
                data-mcp-connected="${data.serverStatus?.connected || false}"
                data-agent-count="${data.statistics?.activeAgents || 0}"
                data-memory-usage="${Math.floor(Math.random() * 60) + 20}"
                data-last-update="${new Date().toLocaleString()}">
            </dashboard-app>

            <!-- Load the bundled Lit 3 components -->
            <script src="${scriptUri}"></script>
        </body>
        </html>
    `;
}

async function getDashboardData() {
    const serverStatus = await checkServerStatus();

    return {
        serverStatus: {
            connected: serverStatus,
            url: mcpClient.serverUrl,
            lastChecked: new Date().toISOString()
        },
        statistics: {
            activeSessions: 0, // Mock data - will be implemented later
            totalSessions: 0, // Mock data - will be implemented later
            activeAgents: serverStatus ? 3 : 0, // Mock data
            totalConversations: 0, // Mock data - will be implemented later
            totalMemories: 0 // Mock data - will be implemented later
        },
        workspace: {
            name: vscode.workspace.name || 'Untitled Workspace',
            folders: vscode.workspace.workspaceFolders?.length || 0
        },
        sessions: []
    };
}

async function checkServerStatus(): Promise<boolean> {
    try {
        // Use ServerManager health check
    const result = await serverManager.healthCheck();
    return result.status === 'healthy';
    } catch (error) {
        console.log('Server health check failed:', error);
        return false;
    }
}

async function startMcpServer(): Promise<void> {
    try {
        outputChannel.appendLine('Starting AutoGen MCP Server...');
        vscode.window.showInformationMessage('Starting AutoGen MCP Server...');

        // Update status bar
        statusBarItem.text = "$(loading~spin) AutoGen";
        statusBarItem.tooltip = "Starting AutoGen MCP Server...";

    // Delegate to ServerManager which reads settings and uses Poetry
    outputChannel.appendLine('Delegating server start to ServerManager...');

        // Show progress
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Starting AutoGen MCP Server",
            cancellable: false
        }, async (progress) => {
            progress.report({ increment: 0, message: "Initializing..." });

            progress.report({ increment: 50, message: "Starting server process..." });
            await serverManager.startServer();

            // Wait a bit for server to start
            await new Promise(resolve => setTimeout(resolve, 3000));

            progress.report({ increment: 100, message: "Server started!" });
        });

        // Check if server is responsive
        setTimeout(async () => {
            const isHealthy = await checkServerStatus();
            if (isHealthy) {
                statusBarItem.text = "$(check) AutoGen";
                statusBarItem.tooltip = "AutoGen MCP Server is running (click for dashboard)";
                autoGenStatusBar.refresh(); // Update the advanced status bar
                vscode.window.showInformationMessage('✅ AutoGen MCP Server is running and healthy!');
                outputChannel.appendLine('Server is healthy and running');
            } else {
                statusBarItem.text = "$(x) AutoGen";
                statusBarItem.tooltip = "AutoGen MCP Server may have issues (click for dashboard)";
                autoGenStatusBar.refresh(); // Update the advanced status bar
                vscode.window.showWarningMessage('⚠️ AutoGen MCP Server started but may not be fully ready yet.');
                outputChannel.appendLine('Server started but health check failed');
            }
        }, 5000);

    } catch (error) {
        console.error('Failed to start MCP server:', error);
        outputChannel.appendLine(`Failed to start MCP server: ${error}`);
        statusBarItem.text = "$(x) AutoGen";
        statusBarItem.tooltip = "AutoGen MCP Server failed to start (click to retry)";
        autoGenStatusBar.refresh(); // Update the advanced status bar
        vscode.window.showErrorMessage(`Failed to start AutoGen MCP Server: ${error}`);
    }
}

async function stopMcpServer(): Promise<void> {
    try {
        outputChannel.appendLine('Stopping AutoGen MCP Server...');
        vscode.window.showInformationMessage('Stopping AutoGen MCP Server...');

        // Update status bar
        statusBarItem.text = "$(loading~spin) AutoGen";
        statusBarItem.tooltip = "Stopping AutoGen MCP Server...";

        // Delegate to ServerManager
        outputChannel.appendLine('Delegating server stop to ServerManager...');

        // Show progress
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Stopping AutoGen MCP Server",
            cancellable: false
        }, async (progress) => {
            progress.report({ increment: 0, message: "Shutting down..." });

            progress.report({ increment: 50, message: "Stopping server process..." });
            await serverManager.stopServer();

            // Wait a bit for server to stop
            await new Promise(resolve => setTimeout(resolve, 2000));

            progress.report({ increment: 100, message: "Server stopped!" });
        });

        // Update status
        statusBarItem.text = "$(server) AutoGen";
        statusBarItem.tooltip = "AutoGen MCP Server is stopped (click for dashboard)";
        autoGenStatusBar.refresh();
        vscode.window.showInformationMessage('✅ AutoGen MCP Server stopped successfully!');
        outputChannel.appendLine('Server stopped successfully');

    } catch (error) {
        console.error('Failed to stop MCP server:', error);
        outputChannel.appendLine(`Failed to stop MCP server: ${error}`);
        statusBarItem.text = "$(x) AutoGen";
        statusBarItem.tooltip = "AutoGen MCP Server stop failed (click for dashboard)";
        autoGenStatusBar.refresh();
        vscode.window.showErrorMessage(`Failed to stop AutoGen MCP Server: ${error}`);
    }
}

export function deactivate() {
    console.log('AutoGen MCP extension is now deactivated');

    // Dispose of status bar
    if (autoGenStatusBar) {
        autoGenStatusBar.dispose();
    }
}

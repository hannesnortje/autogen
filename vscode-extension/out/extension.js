"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const path = __importStar(require("path"));
const server_manager_1 = require("./services/server-manager");
const server_status_1 = require("./providers/server-status");
const server_1 = require("./types/server");
/**
 * AutoGen Agile Assistant Extension
 * Main extension entry point that initializes the AutoGen integration with server management
 */
let outputChannel;
let serverManager;
let statusProvider;
let dashboardPanel;
/**
 * Extension activation function
 * Called when the extension is first activated
 */
function activate(context) {
    console.log('AutoGen Agile Assistant is now active');
    // Create output channel for logging
    outputChannel = vscode.window.createOutputChannel('AutoGen Agile');
    outputChannel.appendLine('AutoGen Agile Assistant activated');
    // Initialize server manager
    serverManager = new server_manager_1.ServerManager();
    // Initialize status provider
    statusProvider = new server_status_1.ServerStatusProvider(serverManager);
    // Add to disposables
    context.subscriptions.push(serverManager, statusProvider);
    // Register commands
    registerCommands(context);
    // Initialize extension state
    initializeExtension(context);
    // Show welcome message for first activation
    showWelcomeMessage(context);
    // Auto-connect if configured
    autoConnectToServer();
}
/**
 * Extension deactivation function
 * Called when the extension is deactivated
 */
function deactivate() {
    console.log('AutoGen Agile Assistant is now deactivated');
    if (dashboardPanel) {
        dashboardPanel.dispose();
    }
    if (outputChannel) {
        outputChannel.dispose();
    }
}
/**
 * Register all extension commands
 */
function registerCommands(context) {
    // Open Dashboard command
    const openDashboardCommand = vscode.commands.registerCommand('autoGenAgile.openDashboard', () => {
        createDashboardPanel(context);
    });
    // Refresh Sidebar command
    const refreshSidebarCommand = vscode.commands.registerCommand('autoGenAgile.refreshSidebar', () => {
        outputChannel.appendLine('Refreshing AutoGen Sidebar...');
        vscode.window.showInformationMessage('AutoGen Sidebar refresh requested');
    });
    // Server management commands
    const connectServerCommand = vscode.commands.registerCommand('autoGenAgile.connectServer', async () => {
        try {
            await serverManager.connect();
            outputChannel.appendLine('Server connection initiated');
        }
        catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            outputChannel.appendLine(`Server connection failed: ${message}`);
            vscode.window.showErrorMessage(`Failed to connect to AutoGen server: ${message}`);
        }
    });
    const disconnectServerCommand = vscode.commands.registerCommand('autoGenAgile.disconnectServer', async () => {
        try {
            await serverManager.disconnect();
            outputChannel.appendLine('Server disconnected');
        }
        catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            outputChannel.appendLine(`Server disconnect failed: ${message}`);
        }
    });
    const startServerCommand = vscode.commands.registerCommand('autoGenAgile.startServer', async () => {
        try {
            await serverManager.startServer();
            outputChannel.appendLine('Server start initiated');
        }
        catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            outputChannel.appendLine(`Server start failed: ${message}`);
            vscode.window.showErrorMessage(`Failed to start AutoGen server: ${message}`);
        }
    });
    const stopServerCommand = vscode.commands.registerCommand('autoGenAgile.stopServer', async () => {
        try {
            await serverManager.stopServer();
            outputChannel.appendLine('Server stop initiated');
        }
        catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            outputChannel.appendLine(`Server stop failed: ${message}`);
            vscode.window.showErrorMessage(`Failed to stop AutoGen server: ${message}`);
        }
    });
    const showServerStatusCommand = vscode.commands.registerCommand('autogen.showServerStatus', () => {
        createDashboardPanel(context);
    });
    context.subscriptions.push(openDashboardCommand, refreshSidebarCommand, connectServerCommand, disconnectServerCommand, startServerCommand, stopServerCommand, showServerStatusCommand);
}
/**
 * Create and show the dashboard panel
 */
function createDashboardPanel(context) {
    // If panel already exists, show it
    if (dashboardPanel) {
        dashboardPanel.reveal();
        return;
    }
    // Create new panel
    dashboardPanel = vscode.window.createWebviewPanel('autoGenDashboard', 'AutoGen Dashboard', vscode.ViewColumn.One, {
        enableScripts: true,
        retainContextWhenHidden: true,
        localResourceRoots: [
            vscode.Uri.file(path.join(context.extensionPath, 'out', 'webview'))
        ]
    });
    // Set initial HTML content
    dashboardPanel.webview.html = getWebviewContent(dashboardPanel.webview, context.extensionPath);
    // Handle panel disposal
    dashboardPanel.onDidDispose(() => {
        dashboardPanel = undefined;
    });
    // Handle messages from webview
    dashboardPanel.webview.onDidReceiveMessage(async (message) => {
        switch (message.type) {
            case 'getServerStatus':
                sendServerStatusToWebview();
                break;
            case 'executeServerAction':
                await handleServerAction(message.actionId);
                break;
            case 'refreshServerStatus':
                await statusProvider.refresh();
                sendServerStatusToWebview();
                break;
            case 'openSettings':
                vscode.commands.executeCommand('workbench.action.openSettings', 'autogen.server');
                break;
            case 'viewLogs':
                outputChannel.show();
                break;
            default:
                outputChannel.appendLine(`Unknown message type: ${message.type}`);
        }
    }, undefined, context.subscriptions);
    // Send initial server status
    sendServerStatusToWebview();
    // Listen for server status changes
    const statusSubscription = statusProvider.onDidChangeServerStatus((status) => {
        if (dashboardPanel) {
            dashboardPanel.webview.postMessage({
                type: 'serverStatusUpdate',
                status
            });
        }
    });
    context.subscriptions.push(statusSubscription);
    outputChannel.appendLine('Dashboard panel created');
}
/**
 * Handle server actions from webview
 */
async function handleServerAction(actionId) {
    let success = true;
    let error;
    try {
        switch (actionId) {
            case 'connect':
                await serverManager.connect();
                outputChannel.appendLine('Server connection initiated from dashboard');
                break;
            case 'disconnect':
                await serverManager.disconnect();
                outputChannel.appendLine('Server disconnected from dashboard');
                break;
            case 'start':
                await serverManager.startServer();
                outputChannel.appendLine('Server start initiated from dashboard');
                break;
            case 'stop':
                await serverManager.stopServer();
                outputChannel.appendLine('Server stop initiated from dashboard');
                break;
            case 'restart':
                await serverManager.restart();
                outputChannel.appendLine('Server restart initiated from dashboard');
                break;
            case 'refresh':
                await statusProvider.refresh();
                outputChannel.appendLine('Server status refreshed from dashboard');
                break;
            case 'configure':
                vscode.commands.executeCommand('workbench.action.openSettings', 'autogen.server');
                break;
            default:
                throw new Error(`Unknown server action: ${actionId}`);
        }
    }
    catch (err) {
        success = false;
        error = err instanceof Error ? err.message : String(err);
        outputChannel.appendLine(`Server action '${actionId}' failed: ${error}`);
    }
    // Send result back to webview
    if (dashboardPanel) {
        dashboardPanel.webview.postMessage({
            type: 'serverActionResult',
            actionId,
            success,
            error
        });
    }
}
/**
 * Send current server status to webview
 */
function sendServerStatusToWebview() {
    if (dashboardPanel) {
        const status = statusProvider.getStatus();
        dashboardPanel.webview.postMessage({
            type: 'serverStatusUpdate',
            status
        });
    }
}
/**
 * Generate webview HTML content
 */
function getWebviewContent(webview, extensionPath) {
    const scriptUri = webview.asWebviewUri(vscode.Uri.file(path.join(extensionPath, 'out', 'webview', 'dashboard.js')));
    const nonce = getNonce();
    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource} 'unsafe-inline'; script-src 'nonce-${nonce}';">
    <title>AutoGen Dashboard</title>
    <style>
        body {
            padding: 0;
            margin: 0;
            font-family: var(--vscode-font-family);
            font-size: var(--vscode-font-size);
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
        }
        
        autogen-dashboard {
            display: block;
            width: 100%;
            min-height: 100vh;
        }
    </style>
</head>
<body>
    <autogen-dashboard id="dashboard"></autogen-dashboard>
    
    <script nonce="${nonce}">
        // Set up VS Code API
        const vscode = acquireVsCodeApi();
        window.vscode = vscode;
        
        // Log to console for debugging
        console.log('Dashboard webview loaded');
    </script>
    
    <script nonce="${nonce}" type="module" src="${scriptUri}"></script>
</body>
</html>`;
}
/**
 * Generate a nonce for CSP
 */
function getNonce() {
    let text = '';
    const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    for (let i = 0; i < 32; i++) {
        text += possible.charAt(Math.floor(Math.random() * possible.length));
    }
    return text;
}
/**
 * Initialize extension with server management
 */
function initializeExtension(context) {
    // Set context for conditional view visibility
    vscode.commands.executeCommand('setContext', 'workspaceHasAutoGenConfig', true);
    // Log configuration
    const config = vscode.workspace.getConfiguration('autogen.server');
    const serverUrl = config.get('url', 'http://localhost:9000');
    const autoStart = config.get('autoStart', true);
    const healthCheckInterval = config.get('healthCheckInterval', 30000);
    outputChannel.appendLine(`Server configuration loaded:`);
    outputChannel.appendLine(`  - Server URL: ${serverUrl}`);
    outputChannel.appendLine(`  - Auto Start: ${autoStart}`);
    outputChannel.appendLine(`  - Health Check Interval: ${healthCheckInterval}ms`);
    // Listen for server events
    serverManager.on(server_1.ServerEventType.STATUS_CHANGED, (event) => {
        outputChannel.appendLine(`Server status changed: ${JSON.stringify(event.data)}`);
    });
    serverManager.on(server_1.ServerEventType.ERROR, (event) => {
        outputChannel.appendLine(`Server error: ${JSON.stringify(event.data)}`);
    });
}
/**
 * Auto-connect to server if configured
 */
async function autoConnectToServer() {
    const config = vscode.workspace.getConfiguration('autogen.server');
    const autoStart = config.get('autoStart', true);
    if (autoStart) {
        try {
            outputChannel.appendLine('Auto-connecting to AutoGen server...');
            await serverManager.connect();
        }
        catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            outputChannel.appendLine(`Auto-connect failed: ${message}`);
        }
    }
}
/**
 * Show welcome message for new users
 */
function showWelcomeMessage(context) {
    const hasShownWelcome = context.globalState.get('hasShownWelcome', false);
    if (!hasShownWelcome) {
        vscode.window.showInformationMessage('Welcome to AutoGen Agile Assistant! 🚀', 'Open Dashboard', 'Learn More').then((selection) => {
            switch (selection) {
                case 'Open Dashboard':
                    vscode.commands.executeCommand('autoGenAgile.openDashboard');
                    break;
                case 'Learn More':
                    vscode.env.openExternal(vscode.Uri.parse('https://github.com/hannesnortje/autogen'));
                    break;
            }
        });
        context.globalState.update('hasShownWelcome', true);
    }
}
//# sourceMappingURL=extension.js.map
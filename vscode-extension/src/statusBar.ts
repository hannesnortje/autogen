import * as vscode from 'vscode';
import { McpClient } from './mcpClient';
import { ServerManager } from './services/server-manager';

export class AutoGenStatusBar {
    private statusBarItem: vscode.StatusBarItem;
    private agentCountItem: vscode.StatusBarItem;
    private serverStatusItem: vscode.StatusBarItem;
    private quickActionItem: vscode.StatusBarItem;
    private refreshTimer: NodeJS.Timeout | undefined;

    constructor(
        private context: vscode.ExtensionContext,
        private mcpClient: McpClient,
        private serverManager?: ServerManager
    ) {
        // Create status bar items with different priorities (higher priority = left position)
        this.serverStatusItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 104);
        this.statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 103);
        this.agentCountItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 102);
        this.quickActionItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 101);

        this.setupStatusBarItems();
        this.startPeriodicUpdate();

        // Register for disposal
        context.subscriptions.push(
            this.statusBarItem,
            this.agentCountItem,
            this.serverStatusItem,
            this.quickActionItem
        );
    }

    private setupStatusBarItems(): void {
        // Server Status Item
        this.serverStatusItem.command = 'autogen.serverStatusAction';
        this.serverStatusItem.tooltip = 'Click to check AutoGen MCP server status';

        // Main Status Item
        this.statusBarItem.command = 'autogen.showDashboard';
        this.statusBarItem.tooltip = 'AutoGen MCP - Click to open dashboard';

        // Agent Count Item
        this.agentCountItem.command = 'autogen.showDashboard';
        this.agentCountItem.tooltip = 'Active agents - Click to view dashboard';

        // Quick Action Item
        this.quickActionItem.command = 'autogen.quickActions';
        this.quickActionItem.text = '$(gear) AutoGen';
        this.quickActionItem.tooltip = 'AutoGen quick actions';

        this.showAll();
        this.updateStatusBar();
    }

    private showAll(): void {
        this.serverStatusItem.show();
        this.statusBarItem.show();
        this.agentCountItem.show();
        this.quickActionItem.show();
    }

    private hideAll(): void {
        this.serverStatusItem.hide();
        this.statusBarItem.hide();
        this.agentCountItem.hide();
        this.quickActionItem.hide();
    }

    public async updateStatusBar(): Promise<void> {
        try {
            const isConnected = await this.checkServerConnection();
            const currentWorkspace = vscode.workspace.workspaceFolders?.[0]?.name;

            // Update server status
            if (isConnected) {
                this.serverStatusItem.text = '$(check) Server';
                this.serverStatusItem.tooltip = `AutoGen MCP Server - Connected to ${this.mcpClient.serverUrl}\nClick to check status`;
                this.serverStatusItem.backgroundColor = undefined;
            } else {
                this.serverStatusItem.text = '$(x) Server';
                this.serverStatusItem.tooltip = `AutoGen MCP Server - Disconnected from ${this.mcpClient.serverUrl}\n🚀 Click to start server automatically`;
                this.serverStatusItem.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
            }

            // Update main status
            if (isConnected) {
                this.statusBarItem.text = '$(robot) Ready';
                this.statusBarItem.tooltip = `AutoGen MCP - Ready${currentWorkspace ? ` (${currentWorkspace})` : ''}`;
                this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.prominentBackground');
            } else {
                this.statusBarItem.text = '$(robot) Offline';
                this.statusBarItem.tooltip = `AutoGen MCP - Server disconnected${currentWorkspace ? ` (${currentWorkspace})` : ''}`;
                this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
            }

            // Update agent count (mock data for now, can be expanded later)
            if (isConnected) {
                this.agentCountItem.text = '$(person) 3 agents';
                this.agentCountItem.tooltip = 'Agents: 3 available agents ready to help';
                this.agentCountItem.backgroundColor = new vscode.ThemeColor('statusBarItem.prominentBackground');
            } else {
                this.agentCountItem.text = '$(person) No agents';
                this.agentCountItem.tooltip = 'No agents available - server offline';
                this.agentCountItem.backgroundColor = undefined;
            }

        } catch (error) {
            console.error('Failed to update status bar:', error);
            this.setErrorState();
        }
    }

    private setErrorState(): void {
        this.serverStatusItem.text = '$(warning) Error';
        this.serverStatusItem.tooltip = 'AutoGen MCP - Status update failed';
        this.serverStatusItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');

        this.statusBarItem.text = '$(robot) Error';
        this.statusBarItem.tooltip = 'AutoGen MCP - Status update failed';
        this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');

        this.agentCountItem.text = '$(person) Unknown';
        this.agentCountItem.tooltip = 'Agent count unavailable';
        this.agentCountItem.backgroundColor = undefined;
    }

    private async checkServerConnection(): Promise<boolean> {
        try {
            // Add timeout to prevent hanging calls
            const timeoutPromise = new Promise<boolean>((_, reject) =>
                setTimeout(() => reject(new Error('Health check timeout')), 5000)
            );

            if (this.serverManager) {
                const healthPromise = this.serverManager.healthCheck();
                const health = await Promise.race([healthPromise, timeoutPromise.then(() => ({ status: 'timeout' }))]);
                return typeof health === 'object' && health.status === 'healthy';
            } else if (this.mcpClient) {
                const availablePromise = this.mcpClient.isServerAvailable();
                return await Promise.race([availablePromise, timeoutPromise]);
            }
            return false;
        } catch (error) {
            console.log('Health check failed:', error);
            return false;
        }
    }

    private startPeriodicUpdate(): void {
        // Clear any existing timer first
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }

        // Update status every 30 seconds, but prevent overlapping calls
        let isUpdating = false;
        this.refreshTimer = setInterval(async () => {
            if (!isUpdating) {
                isUpdating = true;
                try {
                    await this.updateStatusBar();
                } catch (error) {
                    console.error('Periodic status update failed:', error);
                } finally {
                    isUpdating = false;
                }
            }
        }, 30000);
    }

    public dispose(): void {
        // Clean up timer
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = undefined;
        }

        // Hide all status bar items
        this.hideAll();

        // Dispose status bar items properly
        try {
            this.serverStatusItem.dispose();
            this.statusBarItem.dispose();
            this.agentCountItem.dispose();
            this.quickActionItem.dispose();
        } catch (error) {
            console.error('Error disposing status bar items:', error);
        }
    }

    // Public method to trigger immediate update
    public async refresh(): Promise<void> {
        try {
            await this.updateStatusBar();
        } catch (error) {
            console.error('Status bar refresh failed:', error);
        }
    }
}

// Register quick actions command
export function registerStatusBarCommands(context: vscode.ExtensionContext, mcpClient?: McpClient, statusBar?: AutoGenStatusBar): void {
    const serverStatusActionCommand = vscode.commands.registerCommand('autogen.serverStatusAction', async () => {
        try {
            // Check if server is available
            if (!mcpClient) {
                vscode.window.showErrorMessage('MCP Client not initialized');
                return;
            }

            const isAvailable = await mcpClient.isServerAvailable();

            if (isAvailable) {
                vscode.window.showInformationMessage(`✅ AutoGen MCP server is available at ${mcpClient.serverUrl}`);
            } else {
                const choice = await vscode.window.showErrorMessage(
                    `❌ AutoGen MCP server is not available at ${mcpClient.serverUrl}`,
                    'Start Server',
                    'Check Again',
                    'Open Settings'
                );

                if (choice === 'Start Server') {
                    await vscode.commands.executeCommand('autogen.startServer');
                } else if (choice === 'Check Again') {
                    // Re-run this command after a delay (prevent immediate recursion)
                    setTimeout(() => vscode.commands.executeCommand('autogen.serverStatusAction'), 1000);
                } else if (choice === 'Open Settings') {
                    await vscode.commands.executeCommand('workbench.action.openSettings', 'autogen');
                }
            }

            // Refresh status bar safely
            if (statusBar) {
                statusBar.refresh();
            }
        } catch (error) {
            console.error('Server status action failed:', error);
            vscode.window.showErrorMessage(`Server status check failed: ${error}`);
        }
    });

    const quickActionsCommand = vscode.commands.registerCommand('autogen.quickActions', async () => {
        try {
            const actions = [
                {
                    label: '$(play) Start Session',
                    description: 'Start a new AutoGen session',
                    command: 'autogen.connect'
                },
                {
                    label: '$(stop) Stop Session',
                    description: 'Stop the current AutoGen session',
                    command: 'autogen.disconnect'
                },
                {
                    label: '$(dashboard) Dashboard',
                    description: 'Open AutoGen dashboard',
                    command: 'autogen.showDashboard'
                },
                {
                    label: '$(play) Start Server',
                    description: 'Start AutoGen MCP server',
                    command: 'autogen.startServer'
                },
                {
                    label: '$(stop) Stop Server',
                    description: 'Stop AutoGen MCP server',
                    command: 'autogen.stopServer'
                },
                {
                    label: '$(gear) Configure Workspace',
                    description: 'Configure current workspace for AutoGen',
                    command: 'autogen.configureWorkspace'
                },
                {
                    label: '$(refresh) Refresh Status',
                    description: 'Refresh server status',
                    command: 'autogen.refreshStatus'
                }
            ];

            const selected = await vscode.window.showQuickPick(actions, {
                placeHolder: 'Select an AutoGen action',
                matchOnDescription: true
            });

            if (selected) {
                await vscode.commands.executeCommand(selected.command);
            }
        } catch (error) {
            console.error('Quick actions failed:', error);
            vscode.window.showErrorMessage(`Quick actions failed: ${error}`);
        }
    });

    const refreshStatusCommand = vscode.commands.registerCommand('autogen.refreshStatus', async () => {
        try {
            if (statusBar) {
                await statusBar.refresh();
                vscode.window.showInformationMessage('AutoGen status refreshed');
            } else {
                vscode.window.showWarningMessage('Status bar not available');
            }
        } catch (error) {
            console.error('Refresh status failed:', error);
            vscode.window.showErrorMessage(`Refresh failed: ${error}`);
        }
    });

    context.subscriptions.push(serverStatusActionCommand, quickActionsCommand, refreshStatusCommand);
}

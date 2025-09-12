import * as vscode from 'vscode';
import { McpClient } from './mcpClient';
import { SessionTreeProvider } from './sessionTreeProvider';

export class AutoGenStatusBar {
    private statusBarItem: vscode.StatusBarItem;
    private agentCountItem: vscode.StatusBarItem;
    private serverStatusItem: vscode.StatusBarItem;
    private quickActionItem: vscode.StatusBarItem;
    private refreshTimer: NodeJS.Timer | undefined;

    constructor(
        private context: vscode.ExtensionContext,
        private mcpClient: McpClient,
        private sessionTreeProvider: SessionTreeProvider
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
        this.serverStatusItem.command = 'autogen.checkServerStatus';
        this.serverStatusItem.tooltip = 'Click to check AutoGen MCP server status';

        // Main Status Item
        this.statusBarItem.command = 'autogen.showDashboard';
        this.statusBarItem.tooltip = 'AutoGen MCP - Click to open dashboard';

        // Agent Count Item
        this.agentCountItem.command = 'autogen.sessionView.focus';
        this.agentCountItem.tooltip = 'Active agents - Click to view sessions';

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
            const sessionId = this.mcpClient.getCurrentSessionId();
            const allSessions = this.sessionTreeProvider.getAllSessions();
            const activeSessions = allSessions.filter(s => s.status === 'active');
            const totalAgents = allSessions.reduce((sum, session) => sum + session.agents.length, 0);
            const activeAgents = activeSessions.reduce((sum, session) => sum + session.agents.length, 0);

            // Update server status
            if (isConnected) {
                this.serverStatusItem.text = '$(check) Server';
                this.serverStatusItem.tooltip = `AutoGen MCP Server - Connected to ${this.mcpClient.serverUrl}`;
                this.serverStatusItem.backgroundColor = undefined;
            } else {
                this.serverStatusItem.text = '$(x) Server';
                this.serverStatusItem.tooltip = `AutoGen MCP Server - Disconnected from ${this.mcpClient.serverUrl}`;
                this.serverStatusItem.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
            }

            // Update main status
            if (sessionId && isConnected) {
                this.statusBarItem.text = '$(robot) Active Session';
                this.statusBarItem.tooltip = `AutoGen MCP - Active Session: ${sessionId.substring(0, 8)}...`;
                this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.prominentBackground');
            } else if (isConnected) {
                this.statusBarItem.text = '$(robot) Ready';
                this.statusBarItem.tooltip = 'AutoGen MCP - Ready to start session';
                this.statusBarItem.backgroundColor = undefined;
            } else {
                this.statusBarItem.text = '$(robot) Offline';
                this.statusBarItem.tooltip = 'AutoGen MCP - Server disconnected';
                this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
            }

            // Update agent count
            if (totalAgents > 0) {
                const activeText = activeAgents > 0 ? `${activeAgents} active, ` : '';
                this.agentCountItem.text = `$(person) ${activeText}${totalAgents} total`;
                this.agentCountItem.tooltip = `Agents: ${activeAgents} active, ${totalAgents} total across ${allSessions.length} session(s)`;
                this.agentCountItem.backgroundColor = activeAgents > 0 ?
                    new vscode.ThemeColor('statusBarItem.prominentBackground') : undefined;
            } else {
                this.agentCountItem.text = '$(person) No agents';
                this.agentCountItem.tooltip = 'No agents configured';
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
            return await this.mcpClient.isServerAvailable();
        } catch (error) {
            return false;
        }
    }

    private startPeriodicUpdate(): void {
        // Update status every 30 seconds
        this.refreshTimer = setInterval(() => {
            this.updateStatusBar();
        }, 30000);

        // Also update when sessions change
        this.sessionTreeProvider.onDidChangeTreeData(() => {
            // Debounce updates
            setTimeout(() => this.updateStatusBar(), 1000);
        });
    }

    public dispose(): void {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = undefined;
        }
        this.hideAll();
    }

    // Public method to trigger immediate update
    public refresh(): void {
        this.updateStatusBar();
    }
}

// Register quick actions command
export function registerStatusBarCommands(context: vscode.ExtensionContext): void {
    const quickActionsCommand = vscode.commands.registerCommand('autogen.quickActions', async () => {
        const actions = [
            {
                label: '$(play) Start Session',
                description: 'Start a new AutoGen session',
                command: 'autogen.startSession'
            },
            {
                label: '$(stop) Stop Session',
                description: 'Stop the current AutoGen session',
                command: 'autogen.stopSession'
            },
            {
                label: '$(search) Search Memory',
                description: 'Search through project memory',
                command: 'autogen.searchMemory'
            },
            {
                label: '$(brain) Memory Explorer',
                description: 'Open advanced memory explorer',
                command: 'autogen.openMemoryExplorer'
            },
            {
                label: '$(dashboard) Dashboard',
                description: 'Open AutoGen dashboard',
                command: 'autogen.showDashboard'
            },
            {
                label: '$(refresh) Refresh All',
                description: 'Refresh sessions and memory views',
                command: 'autogen.refreshAll'
            },
            {
                label: '$(gear) Check Server',
                description: 'Check MCP server status',
                command: 'autogen.checkServerStatus'
            }
        ];

        const selected = await vscode.window.showQuickPick(actions, {
            placeHolder: 'Select an AutoGen action',
            matchOnDescription: true
        });

        if (selected) {
            await vscode.commands.executeCommand(selected.command);
        }
    });

    const refreshAllCommand = vscode.commands.registerCommand('autogen.refreshAll', async () => {
        await vscode.commands.executeCommand('autogen.refreshSessions');
        await vscode.commands.executeCommand('autogen.refreshMemory');
        vscode.window.showInformationMessage('AutoGen views refreshed');
    });

    context.subscriptions.push(quickActionsCommand, refreshAllCommand);
}

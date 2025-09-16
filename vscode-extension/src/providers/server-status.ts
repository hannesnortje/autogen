import * as vscode from 'vscode';
import { ServerManager } from '../services/server-manager';
import {
    ServerStatus,
    ServerConnection,
    ServerEvent,
    ServerEventType,
    HealthCheckResponse,
    ServerMetrics
} from '../types/server';

/**
 * Server status information for webviews and other components
 */
export interface ServerStatusInfo {
    /** Current server status */
    status: ServerStatus;
    /** Whether server is healthy */
    isHealthy: boolean;
    /** Server connection information */
    connection: ServerConnection | null;
    /** Last health check response */
    lastHealthCheck: HealthCheckResponse | null;
    /** Server metrics */
    metrics: ServerMetrics;
    /** Status display text */
    statusText: string;
    /** Status icon name */
    statusIcon: string;
    /** Status color */
    statusColor: string;
    /** Available actions */
    availableActions: ServerAction[];
}

/**
 * Server action that can be performed
 */
export interface ServerAction {
    /** Action ID */
    id: string;
    /** Action label */
    label: string;
    /** Action icon */
    icon: string;
    /** Whether action is enabled */
    enabled: boolean;
    /** Action tooltip */
    tooltip?: string;
    /** Action command */
    command?: string;
}

/**
 * Provides server status information to webviews and other VS Code components
 */
export class ServerStatusProvider implements vscode.Disposable {
    private serverManager: ServerManager;
    private statusBarItem: vscode.StatusBarItem;
    private disposables: vscode.Disposable[] = [];
    private onDidChangeStatus = new vscode.EventEmitter<ServerStatusInfo>();
    private currentStatus: ServerStatusInfo;

    public readonly onDidChangeServerStatus = this.onDidChangeStatus.event;

    constructor(serverManager: ServerManager) {
        this.serverManager = serverManager;

        // Create status bar item
        this.statusBarItem = vscode.window.createStatusBarItem(
            vscode.StatusBarAlignment.Left,
            100
        );

        this.disposables.push(this.statusBarItem);

        // Initialize current status
        this.currentStatus = this.buildStatusInfo();
        this.updateStatusBar();

        // Listen for server events
        this.serverManager.on(ServerEventType.STATUS_CHANGED, this.handleServerEvent.bind(this));
        this.serverManager.on(ServerEventType.CONNECTION_ESTABLISHED, this.handleServerEvent.bind(this));
        this.serverManager.on(ServerEventType.CONNECTION_LOST, this.handleServerEvent.bind(this));
        this.serverManager.on(ServerEventType.HEALTH_CHECK, this.handleServerEvent.bind(this));
        this.serverManager.on(ServerEventType.ERROR, this.handleServerEvent.bind(this));

        // Show status bar item
        this.statusBarItem.show();
    }

    /**
     * Get current server status information
     */
    getStatus(): ServerStatusInfo {
        return { ...this.currentStatus };
    }

    /**
     * Refresh server status
     */
    async refresh(): Promise<void> {
        try {
            if (this.serverManager.getConnection()) {
                await this.serverManager.healthCheck();
            }
        } catch (error) {
            // Health check failure will be handled by the server manager
        }

        this.updateStatus();
    }

    /**
     * Execute server action
     */
    async executeAction(actionId: string): Promise<void> {
        const action = this.currentStatus.availableActions.find(a => a.id === actionId);
        if (!action || !action.enabled) {
            return;
        }

        try {
            switch (actionId) {
                case 'connect':
                    await this.serverManager.connect();
                    break;
                case 'disconnect':
                    await this.serverManager.disconnect();
                    break;
                case 'start':
                    await this.serverManager.startServer();
                    break;
                case 'stop':
                    await this.serverManager.stopServer();
                    break;
                case 'restart':
                    await this.serverManager.restart();
                    break;
                case 'refresh':
                    await this.refresh();
                    break;
                case 'configure':
                    this.openServerConfiguration();
                    break;
                default:
                    if (action.command) {
                        await vscode.commands.executeCommand(action.command);
                    }
                    break;
            }
        } catch (error) {
            vscode.window.showErrorMessage(`Server action failed: ${error}`);
        }
    }

    /**
     * Handle server events and update status
     */
    private handleServerEvent(event: ServerEvent): void {
        this.updateStatus();
    }

    /**
     * Update server status information
     */
    private updateStatus(): void {
        const newStatus = this.buildStatusInfo();
        const statusChanged = this.hasStatusChanged(this.currentStatus, newStatus);

        this.currentStatus = newStatus;
        this.updateStatusBar();

        if (statusChanged) {
            this.onDidChangeStatus.fire(this.currentStatus);
        }
    }

    /**
     * Build server status information
     */
    private buildStatusInfo(): ServerStatusInfo {
        const connection = this.serverManager.getConnection();
        const status = this.serverManager.getStatus();
        const isHealthy = this.serverManager.isHealthy();
        const metrics = this.serverManager.getMetrics();

        return {
            status,
            isHealthy,
            connection,
            lastHealthCheck: null, // Would need to be exposed by ServerManager
            metrics,
            statusText: this.getStatusText(status, isHealthy),
            statusIcon: this.getStatusIcon(status, isHealthy),
            statusColor: this.getStatusColor(status, isHealthy),
            availableActions: this.getAvailableActions(status, connection)
        };
    }

    /**
     * Get status display text
     */
    private getStatusText(status: ServerStatus, isHealthy: boolean): string {
        switch (status) {
            case ServerStatus.CONNECTED:
                return isHealthy ? 'AutoGen Connected' : 'AutoGen Connected (Degraded)';
            case ServerStatus.CONNECTING:
                return 'AutoGen Connecting...';
            case ServerStatus.RECONNECTING:
                return 'AutoGen Reconnecting...';
            case ServerStatus.STARTING:
                return 'AutoGen Starting...';
            case ServerStatus.STOPPING:
                return 'AutoGen Stopping...';
            case ServerStatus.ERROR:
                return 'AutoGen Error';
            case ServerStatus.DISCONNECTED:
            default:
                return 'AutoGen Disconnected';
        }
    }

    /**
     * Get status icon
     */
    private getStatusIcon(status: ServerStatus, isHealthy: boolean): string {
        switch (status) {
            case ServerStatus.CONNECTED:
                return isHealthy ? '$(check)' : '$(warning)';
            case ServerStatus.CONNECTING:
            case ServerStatus.RECONNECTING:
            case ServerStatus.STARTING:
                return '$(loading~spin)';
            case ServerStatus.STOPPING:
                return '$(loading~spin)';
            case ServerStatus.ERROR:
                return '$(error)';
            case ServerStatus.DISCONNECTED:
            default:
                return '$(circle-slash)';
        }
    }

    /**
     * Get status color
     */
    private getStatusColor(status: ServerStatus, isHealthy: boolean): string {
        switch (status) {
            case ServerStatus.CONNECTED:
                return isHealthy ? '#00ff00' : '#ffaa00';
            case ServerStatus.CONNECTING:
            case ServerStatus.RECONNECTING:
            case ServerStatus.STARTING:
            case ServerStatus.STOPPING:
                return '#0099ff';
            case ServerStatus.ERROR:
                return '#ff0000';
            case ServerStatus.DISCONNECTED:
            default:
                return '#888888';
        }
    }

    /**
     * Get available server actions
     */
    private getAvailableActions(status: ServerStatus, connection: ServerConnection | null): ServerAction[] {
        const actions: ServerAction[] = [];

        // Always available actions
        actions.push({
            id: 'refresh',
            label: 'Refresh',
            icon: '$(refresh)',
            enabled: true,
            tooltip: 'Refresh server status'
        });

        actions.push({
            id: 'configure',
            label: 'Configure',
            icon: '$(settings)',
            enabled: true,
            tooltip: 'Configure server settings'
        });

        // Status-dependent actions
        switch (status) {
            case ServerStatus.DISCONNECTED:
            case ServerStatus.ERROR:
                actions.push({
                    id: 'connect',
                    label: 'Connect',
                    icon: '$(plug)',
                    enabled: true,
                    tooltip: 'Connect to AutoGen server'
                });

                if (!connection || connection.config.type === 'local') {
                    actions.push({
                        id: 'start',
                        label: 'Start Server',
                        icon: '$(play)',
                        enabled: true,
                        tooltip: 'Start local AutoGen server'
                    });
                }
                break;

            case ServerStatus.CONNECTED:
                actions.push({
                    id: 'disconnect',
                    label: 'Disconnect',
                    icon: '$(debug-disconnect)',
                    enabled: true,
                    tooltip: 'Disconnect from server'
                });

                actions.push({
                    id: 'restart',
                    label: 'Restart',
                    icon: '$(debug-restart)',
                    enabled: true,
                    tooltip: 'Restart server connection'
                });

                if (connection && connection.config.type === 'local') {
                    actions.push({
                        id: 'stop',
                        label: 'Stop Server',
                        icon: '$(stop)',
                        enabled: true,
                        tooltip: 'Stop local AutoGen server'
                    });
                }
                break;

            case ServerStatus.CONNECTING:
            case ServerStatus.RECONNECTING:
                actions.push({
                    id: 'disconnect',
                    label: 'Cancel',
                    icon: '$(close)',
                    enabled: true,
                    tooltip: 'Cancel connection attempt'
                });
                break;

            case ServerStatus.STARTING:
                actions.push({
                    id: 'stop',
                    label: 'Stop',
                    icon: '$(stop)',
                    enabled: true,
                    tooltip: 'Stop server startup'
                });
                break;

            case ServerStatus.STOPPING:
                // No actions available during stopping
                break;
        }

        return actions;
    }

    /**
     * Update status bar item
     */
    private updateStatusBar(): void {
        const status = this.currentStatus;

        this.statusBarItem.text = `${status.statusIcon} ${status.statusText}`;
        this.statusBarItem.tooltip = this.buildStatusTooltip(status);
        this.statusBarItem.command = 'autogen.showServerStatus';

        // Set background color for critical states
        if (status.status === ServerStatus.ERROR) {
            this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
        } else {
            this.statusBarItem.backgroundColor = undefined;
        }
    }

    /**
     * Build status bar tooltip
     */
    private buildStatusTooltip(status: ServerStatusInfo): string {
        const lines: string[] = [];

        lines.push(`AutoGen Server: ${status.statusText}`);

        if (status.connection) {
            lines.push(`URL: ${status.connection.config.url}`);

            if (status.connection.connectedAt) {
                const uptime = Date.now() - status.connection.connectedAt.getTime();
                lines.push(`Uptime: ${this.formatDuration(uptime)}`);
            }

            if (status.connection.lastHealthCheck) {
                const lastCheck = Date.now() - status.connection.lastHealthCheck.getTime();
                lines.push(`Last Health Check: ${this.formatDuration(lastCheck)} ago`);
            }
        }

        lines.push('');
        lines.push('Click to view server status');

        return lines.join('\n');
    }

    /**
     * Check if status has meaningfully changed
     */
    private hasStatusChanged(oldStatus: ServerStatusInfo, newStatus: ServerStatusInfo): boolean {
        return oldStatus.status !== newStatus.status ||
               oldStatus.isHealthy !== newStatus.isHealthy ||
               oldStatus.statusText !== newStatus.statusText;
    }

    /**
     * Open server configuration
     */
    private openServerConfiguration(): void {
        vscode.commands.executeCommand('workbench.action.openSettings', 'autogen.server');
    }

    /**
     * Format duration in human readable format
     */
    private formatDuration(ms: number): string {
        const seconds = Math.floor(ms / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);

        if (hours > 0) {
            return `${hours}h ${minutes % 60}m`;
        } else if (minutes > 0) {
            return `${minutes}m ${seconds % 60}s`;
        } else {
            return `${seconds}s`;
        }
    }

    /**
     * Dispose of the provider
     */
    dispose(): void {
        this.onDidChangeStatus.dispose();
        this.disposables.forEach(d => d.dispose());
    }
}

import * as vscode from 'vscode';
import { McpClient, MemoryAnalyticsReport, MemoryHealthStatus, MemoryOptimizationRequest, MemoryMetrics } from './mcpClient';
import { RealtimeDataManager, RealtimeDataUpdate } from './realtimeDataService';

export interface IMemoryAnalyticsDashboard {
    readonly panel: vscode.WebviewPanel;
    dispose(): void;
}

export class MemoryAnalyticsDashboardProvider {
    public static currentPanel: IMemoryAnalyticsDashboard | undefined;
    private static readonly viewType = 'memoryAnalyticsDashboard';

    constructor(
        private readonly context: vscode.ExtensionContext,
        private readonly mcpClient: McpClient
    ) {}

    public static createOrShow(context: vscode.ExtensionContext, mcpClient: McpClient): void {
        const column = vscode.window.activeTextEditor
            ? vscode.window.activeTextEditor.viewColumn
            : undefined;

        // If we already have a panel, show it
        if (MemoryAnalyticsDashboardProvider.currentPanel) {
            MemoryAnalyticsDashboardProvider.currentPanel.panel.reveal(column);
            return;
        }

        // Otherwise, create a new panel
        const panel = vscode.window.createWebviewPanel(
            MemoryAnalyticsDashboardProvider.viewType,
            'Memory Analytics Dashboard',
            column || vscode.ViewColumn.One,
            {
                enableScripts: true,
                retainContextWhenHidden: true,
                localResourceRoots: [
                    vscode.Uri.joinPath(context.extensionUri, 'resources')
                ]
            }
        );

        MemoryAnalyticsDashboardProvider.currentPanel = new MemoryAnalyticsDashboard(panel, context, mcpClient);
    }

    public static revive(panel: vscode.WebviewPanel, context: vscode.ExtensionContext, mcpClient: McpClient): void {
        MemoryAnalyticsDashboardProvider.currentPanel = new MemoryAnalyticsDashboard(panel, context, mcpClient);
    }
}

class MemoryAnalyticsDashboard implements IMemoryAnalyticsDashboard {
    public readonly panel: vscode.WebviewPanel;
    private readonly disposables: vscode.Disposable[] = [];
    private analyticsData: MemoryAnalyticsReport | null = null;
    private healthData: MemoryHealthStatus | null = null;
    private metricsData: MemoryMetrics | null = null;
    private isOfflineMode: boolean = false;
    private lastDataRefresh: Date | null = null;
    private retryAttempts: number = 0;
    private maxRetries: number = 3;
    private realtimeDataManager: RealtimeDataManager;

    constructor(
        panel: vscode.WebviewPanel,
        private readonly context: vscode.ExtensionContext,
        private readonly mcpClient: McpClient
    ) {
        this.panel = panel;

        // Initialize real-time data manager
        const outputChannel = vscode.window.createOutputChannel('AutoGen Real-time Data');
        this.realtimeDataManager = new RealtimeDataManager(outputChannel, {
            url: vscode.workspace.getConfiguration('autogen').get('websocketUrl', 'ws://localhost:9001/ws')
        });

        // Setup real-time data handlers
        this.setupRealtimeDataHandlers();

        // Set the webview's initial html content
        this.update();

        // Listen for when the panel is disposed
        this.panel.onDidDispose(() => this.dispose(), null, this.disposables);

        // Update the content based on view changes
        this.panel.onDidChangeViewState(
            () => {
                if (this.panel.visible) {
                    this.update();
                }
            },
            null,
            this.disposables
        );

        // Handle messages from the webview
        this.panel.webview.onDidReceiveMessage(
            async message => {
                switch (message.type) {
                    case 'loadAnalytics':
                        await this.loadAnalyticsData();
                        break;
                    case 'loadHealth':
                        await this.loadHealthData();
                        break;
                    case 'loadMetrics':
                        await this.loadMetricsData();
                        break;
                    case 'optimizeMemory':
                        await this.handleOptimizeMemory(message.strategy, message.scope, message.dryRun);
                        break;
                    case 'refreshAll':
                        await this.refreshAllData();
                        break;
                    case 'retryConnection':
                        await this.retryConnection();
                        break;
                    case 'clearCache':
                        this.clearCachedData();
                        break;
                    case 'forceRefresh':
                        this.isOfflineMode = false;
                        this.retryAttempts = 0;
                        await this.refreshAllData();
                        break;
                    case 'enableRealtime':
                        this.enableRealtimeUpdates();
                        break;
                    case 'disableRealtime':
                        this.disableRealtimeUpdates();
                        break;
                }
            },
            null,
            this.disposables
        );
    }

    public dispose(): void {
        MemoryAnalyticsDashboardProvider.currentPanel = undefined;

        // Dispose real-time data manager
        this.realtimeDataManager.dispose();

        // Clean up our resources
        this.panel.dispose();

        while (this.disposables.length) {
            const x = this.disposables.pop();
            if (x) {
                x.dispose();
            }
        }
    }

    private setupRealtimeDataHandlers(): void {
        // Handle real-time data updates
        this.realtimeDataManager.onDataUpdate((update: RealtimeDataUpdate) => {
            this.handleRealtimeUpdate(update);
        });

        // Handle connection status changes
        this.realtimeDataManager.onConnectionStatusChange((status: 'connected' | 'disconnected' | 'error') => {
            this.panel.webview.postMessage({
                type: 'realtimeConnectionStatus',
                status: status,
                timestamp: new Date().toISOString()
            });
        });
    }

    private handleRealtimeUpdate(update: RealtimeDataUpdate): void {
        // Send real-time update to webview
        this.panel.webview.postMessage({
            type: 'realtimeUpdate',
            updateType: update.type,
            data: update.data,
            timestamp: update.timestamp
        });

        // Update cached data
        switch (update.type) {
            case 'memory_metrics':
                this.metricsData = update.data;
                break;
            case 'health_status':
                this.healthData = update.data;
                break;
            case 'analytics_report':
                this.analyticsData = update.data;
                break;
        }
    }

    private enableRealtimeUpdates(): void {
        this.realtimeDataManager.start();
        this.panel.webview.postMessage({
            type: 'realtimeEnabled',
            message: 'Real-time updates enabled'
        });
    }

    private disableRealtimeUpdates(): void {
        this.realtimeDataManager.stop();
        this.panel.webview.postMessage({
            type: 'realtimeDisabled',
            message: 'Real-time updates disabled'
        });
    }

    private async update(): Promise<void> {
        const webview = this.panel.webview;
        this.panel.title = 'Memory Analytics Dashboard';
        this.panel.webview.html = await this.getHtmlForWebview(webview);

        // Load initial data
        await this.refreshAllData();
    }

    private async refreshAllData(): Promise<void> {
        try {
            // Check if server is available
            const isConnected = await this.mcpClient.isServerAvailable();

            if (!isConnected) {
                this.enterOfflineMode();
                return;
            }

            // If we were in offline mode and now connected, exit offline mode
            if (this.isOfflineMode) {
                this.exitOfflineMode();
            }

            this.retryAttempts = 0; // Reset retry counter on successful connection

            // Load all data concurrently with error handling for each
            const results = await Promise.allSettled([
                this.loadAnalyticsData(),
                this.loadHealthData(),
                this.loadMetricsData()
            ]);

            // Check if any requests failed
            const failedRequests = results.filter(result => result.status === 'rejected').length;
            if (failedRequests > 0) {
                this.panel.webview.postMessage({
                    type: 'partialFailure',
                    message: `${failedRequests} out of 3 data sources failed to load. Some information may be outdated.`
                });
            }

            this.lastDataRefresh = new Date();
            this.panel.webview.postMessage({
                type: 'dataRefreshComplete',
                timestamp: this.lastDataRefresh.toISOString()
            });

        } catch (error) {
            this.handleConnectionError(error);
        }
    }

    private enterOfflineMode(): void {
        this.isOfflineMode = true;
        this.panel.webview.postMessage({
            type: 'offlineMode',
            message: 'Connection to MCP server lost. Working in offline mode with cached data.',
            lastRefresh: this.lastDataRefresh?.toISOString() || null
        });
    }

    private exitOfflineMode(): void {
        this.isOfflineMode = false;
        this.panel.webview.postMessage({
            type: 'onlineMode',
            message: 'Connection to MCP server restored. Live data is now available.'
        });
    }

    private handleConnectionError(error: any): void {
        this.retryAttempts++;

        if (this.retryAttempts >= this.maxRetries) {
            this.enterOfflineMode();
        } else {
            this.panel.webview.postMessage({
                type: 'connectionError',
                message: `Connection error (attempt ${this.retryAttempts}/${this.maxRetries}). Retrying...`,
                error: error instanceof Error ? error.message : 'Unknown connection error'
            });

            // Retry after a delay
            setTimeout(() => {
                this.refreshAllData();
            }, 2000 * this.retryAttempts); // Exponential backoff
        }
    }

    private async loadAnalyticsData(): Promise<void> {
        try {
            // In offline mode, only use cached data
            if (this.isOfflineMode && this.analyticsData) {
                this.panel.webview.postMessage({
                    type: 'analyticsData',
                    data: this.analyticsData,
                    cached: true
                });
                return;
            }

            const isConnected = await this.mcpClient.isServerAvailable();
            if (!isConnected) {
                throw new Error('MCP server is not available');
            }

            this.analyticsData = await this.mcpClient.getMemoryAnalyticsReport();
            this.panel.webview.postMessage({
                type: 'analyticsData',
                data: this.analyticsData,
                cached: false
            });

        } catch (error) {
            // If we have cached data, use it with a warning
            if (this.analyticsData) {
                this.panel.webview.postMessage({
                    type: 'analyticsData',
                    data: this.analyticsData,
                    cached: true,
                    warning: 'Using cached data due to connection issues'
                });
            }

            this.panel.webview.postMessage({
                type: 'analyticsError',
                error: this.getErrorMessage(error),
                severity: this.getErrorSeverity(error),
                hasCache: !!this.analyticsData
            });
        }
    }

    private async loadHealthData(): Promise<void> {
        try {
            // In offline mode, only use cached data
            if (this.isOfflineMode && this.healthData) {
                this.panel.webview.postMessage({
                    type: 'healthData',
                    data: this.healthData,
                    cached: true
                });
                return;
            }

            const isConnected = await this.mcpClient.isServerAvailable();
            if (!isConnected) {
                throw new Error('MCP server is not available');
            }

            this.healthData = await this.mcpClient.getMemoryHealth();
            this.panel.webview.postMessage({
                type: 'healthData',
                data: this.healthData,
                cached: false
            });

        } catch (error) {
            // If we have cached data, use it with a warning
            if (this.healthData) {
                this.panel.webview.postMessage({
                    type: 'healthData',
                    data: this.healthData,
                    cached: true,
                    warning: 'Using cached data due to connection issues'
                });
            }

            this.panel.webview.postMessage({
                type: 'healthError',
                error: this.getErrorMessage(error),
                severity: this.getErrorSeverity(error),
                hasCache: !!this.healthData
            });
        }
    }

    private async loadMetricsData(): Promise<void> {
        try {
            // In offline mode, only use cached data
            if (this.isOfflineMode && this.metricsData) {
                this.panel.webview.postMessage({
                    type: 'metricsData',
                    data: this.metricsData,
                    cached: true
                });
                return;
            }

            const isConnected = await this.mcpClient.isServerAvailable();
            if (!isConnected) {
                throw new Error('MCP server is not available');
            }

            this.metricsData = await this.mcpClient.getMemoryMetrics();
            this.panel.webview.postMessage({
                type: 'metricsData',
                data: this.metricsData,
                cached: false
            });

        } catch (error) {
            // If we have cached data, use it with a warning
            if (this.metricsData) {
                this.panel.webview.postMessage({
                    type: 'metricsData',
                    data: this.metricsData,
                    cached: true,
                    warning: 'Using cached data due to connection issues'
                });
            }

            this.panel.webview.postMessage({
                type: 'metricsError',
                error: this.getErrorMessage(error),
                severity: this.getErrorSeverity(error),
                hasCache: !!this.metricsData
            });
        }
    }

    private getErrorMessage(error: any): string {
        if (error instanceof Error) {
            // Provide user-friendly messages for common errors
            if (error.message.includes('ECONNREFUSED')) {
                return 'Cannot connect to MCP server. Please check if the server is running.';
            }
            if (error.message.includes('timeout')) {
                return 'Request timed out. The server may be overloaded.';
            }
            if (error.message.includes('404')) {
                return 'Endpoint not found. The server may not support this feature.';
            }
            if (error.message.includes('500')) {
                return 'Server error occurred. Please try again later.';
            }
            return error.message;
        }
        return 'An unknown error occurred';
    }

    private getErrorSeverity(error: any): 'low' | 'medium' | 'high' {
        if (error instanceof Error) {
            if (error.message.includes('ECONNREFUSED') || error.message.includes('not available')) {
                return 'high'; // Complete connection failure
            }
            if (error.message.includes('timeout') || error.message.includes('500')) {
                return 'medium'; // Temporary server issues
            }
            if (error.message.includes('404') || error.message.includes('400')) {
                return 'low'; // Client-side or configuration issues
            }
        }
        return 'medium';
    }

    private async handleOptimizeMemory(strategy: string, scope?: string, dryRun?: boolean): Promise<void> {
        try {
            const request: MemoryOptimizationRequest = {
                strategy: strategy as any,
                scope,
                dry_run: dryRun ?? true
            };

            const result = await this.mcpClient.optimizeMemory(request);
            this.panel.webview.postMessage({
                type: 'optimizationResult',
                data: result
            });

            // Refresh data after optimization
            if (!result.dry_run) {
                await this.refreshAllData();
            }

        } catch (error) {
            this.panel.webview.postMessage({
                type: 'optimizationError',
                error: error instanceof Error ? error.message : 'Failed to optimize memory'
            });
        }
    }

    private async retryConnection(): Promise<void> {
        this.panel.webview.postMessage({
            type: 'retryAttempt',
            message: 'Attempting to reconnect...'
        });

        this.retryAttempts = 0; // Reset retry counter
        this.isOfflineMode = false; // Exit offline mode

        try {
            await this.refreshAllData();
            this.panel.webview.postMessage({
                type: 'connectionRestored',
                message: 'Connection restored successfully!'
            });
        } catch (error) {
            this.panel.webview.postMessage({
                type: 'retryFailed',
                message: 'Retry failed. Still in offline mode.',
                error: this.getErrorMessage(error)
            });
            this.enterOfflineMode();
        }
    }

    private clearCachedData(): void {
        this.analyticsData = null;
        this.healthData = null;
        this.metricsData = null;
        this.lastDataRefresh = null;

        this.panel.webview.postMessage({
            type: 'cacheCleared',
            message: 'Cached data cleared. Fresh data will be loaded on next refresh.'
        });

        // Clear MCP client cache as well
        this.mcpClient.clearCache();
    }

    private async getHtmlForWebview(webview: vscode.Webview): Promise<string> {
        return `
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Memory Analytics Dashboard</title>
                <!-- Chart.js CDN -->
                <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js"></script>
                <style>
                    :root {
                        --primary-color: #007ACC;
                        --success-color: #28a745;
                        --warning-color: #ffc107;
                        --danger-color: #dc3545;
                        --info-color: #17a2b8;
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

                    .action-button {
                        padding: 8px 16px;
                        border: 1px solid var(--vscode-button-border);
                        border-radius: var(--border-radius);
                        background: var(--vscode-button-background);
                        color: var(--vscode-button-foreground);
                        cursor: pointer;
                        font-size: 0.9em;
                        transition: all var(--animation-duration);
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

                    .full-width {
                        grid-column: 1 / -1;
                    }

                    .health-status {
                        display: flex;
                        align-items: center;
                        gap: 12px;
                        padding: 16px;
                        border-radius: var(--border-radius);
                        margin-bottom: 16px;
                    }

                    .health-status.healthy {
                        background: rgba(40, 167, 69, 0.1);
                        border: 1px solid var(--success-color);
                    }

                    .health-status.warning {
                        background: rgba(255, 193, 7, 0.1);
                        border: 1px solid var(--warning-color);
                    }

                    .health-status.critical {
                        background: rgba(220, 53, 69, 0.1);
                        border: 1px solid var(--danger-color);
                    }

                    .health-indicator {
                        font-size: 1.5em;
                    }

                    .metrics-grid {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                        gap: 16px;
                        margin-top: 16px;
                    }

                    .metric-card {
                        background: var(--vscode-button-background);
                        border: 1px solid var(--vscode-panel-border);
                        border-radius: var(--border-radius);
                        padding: 16px;
                        text-align: center;
                        transition: background-color var(--animation-duration);
                    }

                    .metric-card:hover {
                        background: var(--vscode-button-hoverBackground);
                    }

                    .metric-value {
                        font-size: 2em;
                        font-weight: bold;
                        color: var(--primary-color);
                        display: block;
                        margin-bottom: 4px;
                    }

                    .metric-label {
                        font-size: 0.9em;
                        color: var(--vscode-descriptionForeground);
                    }

                    .optimization-controls {
                        display: flex;
                        gap: 12px;
                        flex-wrap: wrap;
                        margin-top: 16px;
                    }

                    .optimization-button {
                        padding: 10px 16px;
                        border: 1px solid var(--vscode-button-border);
                        border-radius: var(--border-radius);
                        background: var(--vscode-button-background);
                        color: var(--vscode-button-foreground);
                        cursor: pointer;
                        font-size: 0.9em;
                        transition: all var(--animation-duration);
                    }

                    .optimization-button:hover {
                        background: var(--vscode-button-hoverBackground);
                    }

                    .optimization-button.danger {
                        background: var(--danger-color);
                        color: white;
                        border-color: var(--danger-color);
                    }

                    .loading {
                        text-align: center;
                        padding: 40px;
                        color: var(--vscode-descriptionForeground);
                    }

                    .error {
                        color: var(--danger-color);
                        background: rgba(220, 53, 69, 0.1);
                        border: 1px solid var(--danger-color);
                        border-radius: var(--border-radius);
                        padding: 16px;
                        margin: 16px 0;
                    }

                    .recommendations {
                        margin-top: 16px;
                    }

                    .recommendation-item {
                        background: var(--vscode-list-inactiveSelectionBackground);
                        border-left: 4px solid var(--info-color);
                        padding: 12px;
                        margin-bottom: 8px;
                        border-radius: 0 var(--border-radius) var(--border-radius) 0;
                    }

                    @keyframes pulse {
                        0% { opacity: 1; }
                        50% { opacity: 0.7; }
                        100% { opacity: 1; }
                    }

                    .pulsing {
                        animation: pulse 2s infinite;
                    }

                    /* Chart.js Styles */
                    .chart-container {
                        margin-top: 16px;
                        padding: 16px;
                        background: var(--vscode-editor-background);
                        border: 1px solid var(--vscode-panel-border);
                        border-radius: var(--border-radius);
                        position: relative;
                        height: 250px;
                    }

                    .chart-container canvas {
                        max-width: 100%;
                        max-height: 100%;
                    }

                    .chart-title {
                        text-align: center;
                        margin-bottom: 12px;
                        font-weight: 600;
                        color: var(--vscode-editor-foreground);
                    }

                    .chart-loading {
                        position: absolute;
                        top: 50%;
                        left: 50%;
                        transform: translate(-50%, -50%);
                        color: var(--vscode-descriptionForeground);
                    }

                    @media (max-width: 768px) {
                        .dashboard-grid {
                            grid-template-columns: 1fr;
                        }

                        .metrics-grid {
                            grid-template-columns: 1fr;
                        }

                        .optimization-controls {
                            flex-direction: column;
                        }

                        .chart-container {
                            height: 200px;
                        }
                    }

                    /* Error Handling and Status Styles */
                    .status-bar {
                        position: fixed;
                        top: 0;
                        left: 0;
                        right: 0;
                        z-index: 1000;
                        padding: 8px 16px;
                        font-size: 0.9em;
                        display: none;
                        animation: slideDown 0.3s ease-out;
                    }

                    .status-bar.online {
                        background: var(--success-color);
                        color: white;
                    }

                    .status-bar.offline {
                        background: var(--warning-color);
                        color: black;
                    }

                    .status-bar.error {
                        background: var(--danger-color);
                        color: white;
                    }

                    .status-bar.info {
                        background: var(--info-color);
                        color: white;
                    }

                    @keyframes slideDown {
                        from { transform: translateY(-100%); }
                        to { transform: translateY(0); }
                    }

                    .error-container {
                        background: rgba(220, 53, 69, 0.1);
                        border: 1px solid var(--danger-color);
                        border-radius: var(--border-radius);
                        padding: 16px;
                        margin: 16px 0;
                    }

                    .error-message {
                        display: flex;
                        align-items: center;
                        gap: 8px;
                        margin-bottom: 12px;
                    }

                    .error-icon {
                        font-size: 1.2em;
                        color: var(--danger-color);
                    }

                    .error-actions {
                        display: flex;
                        gap: 8px;
                        flex-wrap: wrap;
                    }

                    .cached-data-warning {
                        background: rgba(255, 193, 7, 0.1);
                        border: 1px solid var(--warning-color);
                        border-radius: var(--border-radius);
                        padding: 12px;
                        margin: 12px 0;
                        display: flex;
                        align-items: center;
                        gap: 8px;
                        font-size: 0.9em;
                    }

                    .cached-icon {
                        color: var(--warning-color);
                    }

                    .connection-status {
                        display: flex;
                        align-items: center;
                        gap: 8px;
                        font-size: 0.9em;
                        padding: 4px 8px;
                        border-radius: 12px;
                        margin-left: auto;
                    }

                    .connection-status.connected {
                        background: rgba(40, 167, 69, 0.1);
                        color: var(--success-color);
                    }

                    .connection-status.disconnected {
                        background: rgba(220, 53, 69, 0.1);
                        color: var(--danger-color);
                    }

                    .connection-status.reconnecting {
                        background: rgba(255, 193, 7, 0.1);
                        color: var(--warning-color);
                    }

                    .pulse {
                        animation: pulse 1.5s ease-in-out infinite;
                    }

                    @keyframes pulse {
                        0% { opacity: 1; }
                        50% { opacity: 0.5; }
                        100% { opacity: 1; }
                    }

                    .retry-button {
                        background: var(--primary-color);
                        color: white;
                        border: none;
                        padding: 8px 12px;
                        border-radius: var(--border-radius);
                        cursor: pointer;
                        font-size: 0.8em;
                        transition: background-color var(--animation-duration);
                    }

                    .retry-button:hover {
                        background: #005a9c;
                    }

                    .clear-cache-button {
                        background: var(--warning-color);
                        color: black;
                        border: none;
                        padding: 8px 12px;
                        border-radius: var(--border-radius);
                        cursor: pointer;
                        font-size: 0.8em;
                        transition: background-color var(--animation-duration);
                    }

                    .clear-cache-button:hover {
                        background: #e0a800;
                    }
                </style>
            </head>
            <body>
                <!-- Status Bar for notifications -->
                <div id="status-bar" class="status-bar"></div>

                <div class="dashboard-header">
                    <h1 class="dashboard-title">🧠 Memory Analytics Dashboard</h1>
                    <div class="header-actions">
                        <div id="connection-status" class="connection-status connected">
                            <span id="connection-icon">🟢</span>
                            <span id="connection-text">Connected</span>
                        </div>
                        <div id="realtime-status" class="connection-status disconnected">
                            <span id="realtime-icon">🔴</span>
                            <span id="realtime-text">Real-time Off</span>
                        </div>
                        <button onclick="toggleRealtime()" id="realtime-toggle" class="action-button">🔄 Enable Real-time</button>
                        <button onclick="refreshAll()" class="action-button">🔄 Refresh All</button>
                        <button onclick="loadAnalytics()" class="action-button">📊 Analytics</button>
                        <button onclick="loadHealth()" class="action-button">🏥 Health</button>
                        <button onclick="loadMetrics()" class="action-button">📈 Metrics</button>
                        <button onclick="forceRefresh()" class="action-button primary">⚡ Force Refresh</button>
                    </div>
                </div>

                <div id="health-section" class="dashboard-section full-width">
                    <h3 class="section-title">🏥 Memory System Health</h3>
                    <div id="health-content" class="loading">Loading health data...</div>
                </div>

                <div class="dashboard-grid">
                    <div id="analytics-section" class="dashboard-section">
                        <h3 class="section-title">📊 Analytics Report</h3>
                        <div id="analytics-content" class="loading">Loading analytics data...</div>
                        <div class="chart-container">
                            <canvas id="analytics-chart" width="400" height="200"></canvas>
                        </div>
                    </div>

                    <div id="metrics-section" class="dashboard-section">
                        <h3 class="section-title">📈 Real-time Metrics</h3>
                        <div id="metrics-content" class="loading">Loading metrics data...</div>
                        <div class="chart-container">
                            <canvas id="metrics-chart" width="400" height="200"></canvas>
                        </div>
                    </div>
                </div>

                <div class="dashboard-grid">
                    <div id="performance-chart-section" class="dashboard-section">
                        <h3 class="section-title">🎯 Performance Trends</h3>
                        <div class="chart-container">
                            <canvas id="performance-chart" width="400" height="200"></canvas>
                        </div>
                    </div>

                    <div id="memory-usage-section" class="dashboard-section">
                        <h3 class="section-title">💾 Memory Usage Distribution</h3>
                        <div class="chart-container">
                            <canvas id="memory-chart" width="400" height="200"></canvas>
                        </div>
                    </div>
                </div>

                <div id="optimization-section" class="dashboard-section full-width">
                    <h3 class="section-title">⚡ Memory Optimization</h3>
                    <div id="optimization-content">
                        <div class="optimization-controls">
                            <button onclick="optimizeMemory('lru', null, true)" class="optimization-button">🧹 LRU Cleanup (Dry Run)</button>
                            <button onclick="optimizeMemory('importance', null, true)" class="optimization-button">⭐ Importance-based (Dry Run)</button>
                            <button onclick="optimizeMemory('frequency', null, true)" class="optimization-button">📊 Frequency-based (Dry Run)</button>
                            <button onclick="optimizeMemory('hybrid', null, true)" class="optimization-button">🎯 Hybrid Strategy (Dry Run)</button>
                            <button onclick="optimizeMemory('hybrid', null, false)" class="optimization-button danger">🚀 Execute Optimization</button>
                        </div>
                        <div id="optimization-results"></div>
                    </div>
                </div>

                <script>
                    const vscode = acquireVsCodeApi();

                    // Chart.js instances
                    let analyticsChart = null;
                    let metricsChart = null;
                    let performanceChart = null;
                    let memoryChart = null;

                    // Initialize charts when DOM is ready
                    document.addEventListener('DOMContentLoaded', function() {
                        initializeCharts();
                    });

                    function initializeCharts() {
                        // Analytics Chart (Line chart for trends)
                        const analyticsCtx = document.getElementById('analytics-chart').getContext('2d');
                        analyticsChart = new Chart(analyticsCtx, {
                            type: 'line',
                            data: {
                                labels: ['1h ago', '45m ago', '30m ago', '15m ago', 'Now'],
                                datasets: [{
                                    label: 'Analytics Score',
                                    data: [65, 72, 68, 75, 82],
                                    borderColor: '#007ACC',
                                    backgroundColor: 'rgba(0, 122, 204, 0.1)',
                                    tension: 0.4,
                                    fill: true
                                }]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: {
                                    legend: {
                                        labels: { color: 'var(--vscode-editor-foreground)' }
                                    }
                                },
                                scales: {
                                    y: {
                                        beginAtZero: true,
                                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                                        ticks: { color: 'var(--vscode-editor-foreground)' }
                                    },
                                    x: {
                                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                                        ticks: { color: 'var(--vscode-editor-foreground)' }
                                    }
                                }
                            }
                        });

                        // Metrics Chart (Bar chart)
                        const metricsCtx = document.getElementById('metrics-chart').getContext('2d');
                        metricsChart = new Chart(metricsCtx, {
                            type: 'bar',
                            data: {
                                labels: ['Response Time', 'Memory Efficiency', 'Cache Hit Rate', 'Throughput'],
                                datasets: [{
                                    label: 'Performance Metrics',
                                    data: [250, 85, 92, 76],
                                    backgroundColor: [
                                        'rgba(40, 167, 69, 0.8)',
                                        'rgba(0, 122, 204, 0.8)',
                                        'rgba(255, 193, 7, 0.8)',
                                        'rgba(220, 53, 69, 0.8)'
                                    ],
                                    borderWidth: 1
                                }]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: {
                                    legend: {
                                        labels: { color: 'var(--vscode-editor-foreground)' }
                                    }
                                },
                                scales: {
                                    y: {
                                        beginAtZero: true,
                                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                                        ticks: { color: 'var(--vscode-editor-foreground)' }
                                    },
                                    x: {
                                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                                        ticks: { color: 'var(--vscode-editor-foreground)' }
                                    }
                                }
                            }
                        });

                        // Performance Chart (Area chart)
                        const performanceCtx = document.getElementById('performance-chart').getContext('2d');
                        performanceChart = new Chart(performanceCtx, {
                            type: 'line',
                            data: {
                                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                                datasets: [
                                    {
                                        label: 'Memory Usage',
                                        data: [65, 59, 80, 81, 56, 55, 40],
                                        borderColor: '#28a745',
                                        backgroundColor: 'rgba(40, 167, 69, 0.2)',
                                        fill: true
                                    },
                                    {
                                        label: 'CPU Usage',
                                        data: [28, 48, 40, 19, 86, 27, 90],
                                        borderColor: '#ffc107',
                                        backgroundColor: 'rgba(255, 193, 7, 0.2)',
                                        fill: true
                                    }
                                ]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: {
                                    legend: {
                                        labels: { color: 'var(--vscode-editor-foreground)' }
                                    }
                                },
                                scales: {
                                    y: {
                                        beginAtZero: true,
                                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                                        ticks: { color: 'var(--vscode-editor-foreground)' }
                                    },
                                    x: {
                                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                                        ticks: { color: 'var(--vscode-editor-foreground)' }
                                    }
                                }
                            }
                        });

                        // Memory Usage Chart (Doughnut chart)
                        const memoryCtx = document.getElementById('memory-chart').getContext('2d');
                        memoryChart = new Chart(memoryCtx, {
                            type: 'doughnut',
                            data: {
                                labels: ['Used Memory', 'Cached', 'Available', 'System Reserved'],
                                datasets: [{
                                    data: [45, 25, 25, 5],
                                    backgroundColor: [
                                        'rgba(220, 53, 69, 0.8)',
                                        'rgba(255, 193, 7, 0.8)',
                                        'rgba(40, 167, 69, 0.8)',
                                        'rgba(108, 117, 125, 0.8)'
                                    ],
                                    borderWidth: 2,
                                    borderColor: 'var(--vscode-panel-border)'
                                }]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: {
                                    legend: {
                                        position: 'bottom',
                                        labels: { color: 'var(--vscode-editor-foreground)' }
                                    }
                                }
                            }
                        });
                    }

                    function updateChartsWithData(data) {
                        // Update charts when new data arrives
                        if (data.analytics && analyticsChart) {
                            // Update analytics chart with real data
                            if (data.analytics.trend_data) {
                                analyticsChart.data.labels = data.analytics.trend_data.labels || analyticsChart.data.labels;
                                analyticsChart.data.datasets[0].data = data.analytics.trend_data.values || analyticsChart.data.datasets[0].data;
                                analyticsChart.update();
                            }
                        }

                        if (data.metrics && metricsChart) {
                            // Update metrics chart with real data
                            const metrics = data.metrics;
                            const values = [
                                metrics.response_times?.average || 250,
                                metrics.memory_efficiency || 85,
                                metrics.cache_hit_rate || 92,
                                metrics.throughput || 76
                            ];
                            metricsChart.data.datasets[0].data = values;
                            metricsChart.update();
                        }

                        if (data.performance && performanceChart) {
                            // Update performance chart with real data
                            if (data.performance.memory_trend) {
                                performanceChart.data.datasets[0].data = data.performance.memory_trend;
                            }
                            if (data.performance.cpu_trend) {
                                performanceChart.data.datasets[1].data = data.performance.cpu_trend;
                            }
                            performanceChart.update();
                        }

                        if (data.memory_usage && memoryChart) {
                            // Update memory chart with real data
                            const usage = data.memory_usage;
                            memoryChart.data.datasets[0].data = [
                                usage.used || 45,
                                usage.cached || 25,
                                usage.available || 25,
                                usage.reserved || 5
                            ];
                            memoryChart.update();
                        }
                    }

                    function loadAnalytics() {
                        document.getElementById('analytics-content').innerHTML = '<div class="loading pulsing">Loading analytics data...</div>';
                        vscode.postMessage({ type: 'loadAnalytics' });
                    }

                    function loadHealth() {
                        document.getElementById('health-content').innerHTML = '<div class="loading pulsing">Loading health data...</div>';
                        vscode.postMessage({ type: 'loadHealth' });
                    }

                    function loadMetrics() {
                        document.getElementById('metrics-content').innerHTML = '<div class="loading pulsing">Loading metrics data...</div>';
                        vscode.postMessage({ type: 'loadMetrics' });
                    }

                    function optimizeMemory(strategy, scope, dryRun) {
                        const resultsDiv = document.getElementById('optimization-results');
                        resultsDiv.innerHTML = '<div class="loading pulsing">Running optimization...</div>';
                        vscode.postMessage({
                            type: 'optimizeMemory',
                            strategy: strategy,
                            scope: scope,
                            dryRun: dryRun
                        });
                    }

                    function refreshAll() {
                        vscode.postMessage({ type: 'refreshAll' });
                        loadAnalytics();
                        loadHealth();
                        loadMetrics();
                    }

                    // Handle messages from the extension
                    window.addEventListener('message', event => {
                        const message = event.data;

                        switch (message.type) {
                            case 'analyticsData':
                                displayAnalyticsData(message.data);
                                if (message.cached) {
                                    showCachedDataWarning('analytics-section', message.warning);
                                }
                                break;
                            case 'analyticsError':
                                showError('analytics-section', message.error, message.severity, message.hasCache);
                                break;
                            case 'healthData':
                                displayHealthData(message.data);
                                if (message.cached) {
                                    showCachedDataWarning('health-section', message.warning);
                                }
                                break;
                            case 'healthError':
                                showError('health-section', message.error, message.severity, message.hasCache);
                                break;
                            case 'metricsData':
                                displayMetricsData(message.data);
                                if (message.cached) {
                                    showCachedDataWarning('metrics-section', message.warning);
                                }
                                break;
                            case 'metricsError':
                                showError('metrics-section', message.error, message.severity, message.hasCache);
                                break;
                            case 'optimizationResult':
                                displayOptimizationResult(message.data);
                                break;
                            case 'optimizationError':
                                showError('optimization-section', message.error, message.severity, false);
                                break;
                            case 'offlineMode':
                                enterOfflineMode(message.message, message.lastRefresh);
                                break;
                            case 'onlineMode':
                                exitOfflineMode(message.message);
                                break;
                            case 'connectionError':
                                showStatusMessage(message.message, 'error', 5000);
                                break;
                            case 'partialFailure':
                                showStatusMessage(message.message, 'info', 8000);
                                break;
                            case 'dataRefreshComplete':
                                updateLastRefreshTime(message.timestamp);
                                break;
                            case 'retryAttempt':
                                showStatusMessage(message.message, 'info');
                                updateConnectionStatus('reconnecting');
                                break;
                            case 'connectionRestored':
                                showStatusMessage(message.message, 'online', 3000);
                                updateConnectionStatus('connected');
                                break;
                            case 'retryFailed':
                                showStatusMessage(message.message, 'error', 8000);
                                updateConnectionStatus('disconnected');
                                break;
                            case 'cacheCleared':
                                showStatusMessage(message.message, 'info', 3000);
                                break;
                            case 'realtimeUpdate':
                                handleRealtimeUpdate(message.updateType, message.data, message.timestamp);
                                break;
                            case 'realtimeConnectionStatus':
                                updateRealtimeStatus(message.status);
                                break;
                            case 'realtimeEnabled':
                                showStatusMessage(message.message, 'online', 3000);
                                updateRealtimeToggle(true);
                                break;
                            case 'realtimeDisabled':
                                showStatusMessage(message.message, 'info', 3000);
                                updateRealtimeToggle(false);
                                break;
                        }
                    });

                    function displayAnalyticsData(data) {
                        const content = document.getElementById('analytics-content');
                        content.innerHTML = '<div class="metrics-grid">' +
                            '<div class="metric-card">' +
                                '<span class="metric-value">' + data.system_overview.total_entries.toLocaleString() + '</span>' +
                                '<span class="metric-label">Total Entries</span>' +
                            '</div>' +
                            '<div class="metric-card">' +
                                '<span class="metric-value">' + formatBytes(data.system_overview.total_size_bytes) + '</span>' +
                                '<span class="metric-label">Total Size</span>' +
                            '</div>' +
                            '<div class="metric-card">' +
                                '<span class="metric-value">' + data.system_overview.collections_count + '</span>' +
                                '<span class="metric-label">Collections</span>' +
                            '</div>' +
                            '<div class="metric-card">' +
                                '<span class="metric-value">' + formatBytes(data.system_overview.average_entry_size) + '</span>' +
                                '<span class="metric-label">Avg Entry Size</span>' +
                            '</div>' +
                        '</div>' +
                        '<h4>📈 Usage Patterns</h4>' +
                        '<div class="metrics-grid">' +
                            '<div class="metric-card">' +
                                '<span class="metric-value">' + data.usage_patterns.read_operations.toLocaleString() + '</span>' +
                                '<span class="metric-label">Read Operations</span>' +
                            '</div>' +
                            '<div class="metric-card">' +
                                '<span class="metric-value">' + data.usage_patterns.write_operations.toLocaleString() + '</span>' +
                                '<span class="metric-label">Write Operations</span>' +
                            '</div>' +
                            '<div class="metric-card">' +
                                '<span class="metric-value">' + data.usage_patterns.search_operations.toLocaleString() + '</span>' +
                                '<span class="metric-label">Search Operations</span>' +
                            '</div>' +
                            '<div class="metric-card">' +
                                '<span class="metric-value">' + (data.usage_patterns.cache_hit_ratio * 100).toFixed(1) + '%</span>' +
                                '<span class="metric-label">Cache Hit Ratio</span>' +
                            '</div>' +
                        '</div>';

                        // Update analytics chart with real data
                        updateChartsWithData({ analytics: data });
                    }

                    function displayHealthData(data) {
                        const content = document.getElementById('health-content');
                        const statusClass = data.status;
                        const statusIcon = getHealthIcon(data.status);

                        let indicatorsHtml = '';
                        for (const [key, indicator] of Object.entries(data.indicators)) {
                            indicatorsHtml += \`
                                <div class="metric-card">
                                    <span class="metric-value \${getStatusColor(indicator.status)}">\${indicator.value.toFixed(2)}</span>
                                    <span class="metric-label">\${formatIndicatorName(key)}</span>
                                    <div style="font-size: 0.8em; margin-top: 4px;">\${indicator.message}</div>
                                </div>
                            \`;
                        }

                        let recommendationsHtml = '';
                        if (data.recommendations && data.recommendations.length > 0) {
                            recommendationsHtml = \`
                                <h4>💡 Recommendations</h4>
                                <div class="recommendations">
                                    \${data.recommendations.map(rec => \`<div class="recommendation-item">\${rec}</div>\`).join('')}
                                </div>
                            \`;
                        }

                        content.innerHTML = \`
                            <div class="health-status \${statusClass}">
                                <span class="health-indicator">\${statusIcon}</span>
                                <div>
                                    <strong>System Status: \${data.status.toUpperCase()}</strong>
                                    <div>Overall Score: \${(data.overall_score * 100).toFixed(1)}%</div>
                                </div>
                            </div>
                            <div class="metrics-grid">
                                \${indicatorsHtml}
                            </div>
                            \${recommendationsHtml}
                        \`;
                    }

                    function displayMetricsData(data) {
                        const content = document.getElementById('metrics-content');
                        content.innerHTML = '<div style="margin-bottom: 16px;">' +
                            '<strong>📅 Last Updated:</strong> ' + new Date(data.timestamp).toLocaleString() +
                        '</div>' +
                        '<div class="metrics-grid">' +
                            '<div class="metric-card">' +
                                '<span class="metric-value">' + data.performance.operations_per_minute.toFixed(1) + '</span>' +
                                '<span class="metric-label">Ops/Min</span>' +
                            '</div>' +
                            '<div class="metric-card">' +
                                '<span class="metric-value">' + data.performance.average_response_time.toFixed(2) + 'ms</span>' +
                                '<span class="metric-label">Avg Response</span>' +
                            '</div>' +
                            '<div class="metric-card">' +
                                '<span class="metric-value">' + (data.performance.cache_hit_ratio * 100).toFixed(1) + '%</span>' +
                                '<span class="metric-label">Cache Hit Rate</span>' +
                            '</div>' +
                            '<div class="metric-card">' +
                                '<span class="metric-value">' + (data.performance.error_rate * 100).toFixed(2) + '%</span>' +
                                '<span class="metric-label">Error Rate</span>' +
                            '</div>' +
                            '<div class="metric-card">' +
                                '<span class="metric-value">' + data.health.memory_usage_percentage.toFixed(1) + '%</span>' +
                                '<span class="metric-label">Memory Usage</span>' +
                            '</div>' +
                            '<div class="metric-card">' +
                                '<span class="metric-value">' + data.health.optimization_score.toFixed(1) + '</span>' +
                                '<span class="metric-label">Optimization</span>' +
                            '</div>' +
                        '</div>';

                        // Update charts with real metrics data
                        updateChartsWithData({
                            metrics: {
                                response_times: { average: data.performance.average_response_time },
                                memory_efficiency: data.health.memory_usage_percentage,
                                cache_hit_rate: data.performance.cache_hit_ratio * 100,
                                throughput: data.performance.operations_per_minute
                            },
                            memory_usage: {
                                used: data.health.memory_usage_percentage,
                                cached: 25, // Mock data - would come from actual metrics
                                available: 100 - data.health.memory_usage_percentage - 25,
                                reserved: 5
                            }
                        });
                    }
                            </div>
                        \`;
                    }

                    function displayOptimizationResult(data) {
                        const content = document.getElementById('optimization-results');
                        const dryRunText = data.dry_run ? ' (Dry Run)' : '';

                        let removedEntriesHtml = '';
                        if (data.removed_entries && data.removed_entries.length > 0) {
                            removedEntriesHtml = \`
                                <h4>🗑️ Removed Entries</h4>
                                \${data.removed_entries.map(entry => \`
                                    <div class="recommendation-item">
                                        <strong>\${entry.removal_reason}</strong><br>
                                        <em>\${entry.content_preview}</em><br>
                                        <small>Last accessed: \${new Date(entry.last_accessed).toLocaleString()}</small>
                                    </div>
                                \`).join('')}
                            \`;
                        }

                        content.innerHTML = \`
                            <div class="metric-card" style="margin: 16px 0;">
                                <h4>✨ Optimization Results\${dryRunText}</h4>
                                <div class="metrics-grid">
                                    <div class="metric-card">
                                        <span class="metric-value">\${data.entries_removed}</span>
                                        <span class="metric-label">Entries Removed</span>
                                    </div>
                                    <div class="metric-card">
                                        <span class="metric-value">\${formatBytes(data.space_freed_bytes)}</span>
                                        <span class="metric-label">Space Freed</span>
                                    </div>
                                    <div class="metric-card">
                                        <span class="metric-value">\${data.optimization_time.toFixed(2)}s</span>
                                        <span class="metric-label">Time Taken</span>
                                    </div>
                                    <div class="metric-card">
                                        <span class="metric-value">\${data.strategy_used}</span>
                                        <span class="metric-label">Strategy Used</span>
                                    </div>
                                </div>
                                \${removedEntriesHtml}
                            </div>
                        \`;
                    }

                    function getHealthIcon(status) {
                        switch (status) {
                            case 'healthy': return '🟢';
                            case 'warning': return '🟡';
                            case 'critical': return '🔴';
                            case 'error': return '❌';
                            default: return '❓';
                        }
                    }

                    function getStatusColor(status) {
                        switch (status) {
                            case 'healthy': return 'color: var(--success-color)';
                            case 'warning': return 'color: var(--warning-color)';
                            case 'critical': return 'color: var(--danger-color)';
                            case 'error': return 'color: var(--danger-color)';
                            default: return '';
                        }
                    }

                    function formatIndicatorName(name) {
                        return name.split('_').map(word =>
                            word.charAt(0).toUpperCase() + word.slice(1)
                        ).join(' ');
                    }

                    function formatBytes(bytes) {
                        if (bytes === 0) return '0 Bytes';
                        const k = 1024;
                        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
                        const i = Math.floor(Math.log(bytes) / Math.log(k));
                        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
                    }

                    // Load initial data when page loads
                    document.addEventListener('DOMContentLoaded', function() {
                        refreshAll();
                    });

                    // Enhanced Error Handling Functions
                    function showError(sectionId, errorMessage, severity = 'medium', hasCache = false) {
                        const section = document.getElementById(sectionId);
                        const contentDiv = section.querySelector('div[id$="-content"]') || section.querySelector('.loading');

                        const severityIcon = {
                            'low': '⚠️',
                            'medium': '❌',
                            'high': '🚨'
                        };

                        const errorHtml = \`
                            <div class="error-container">
                                <div class="error-message">
                                    <span class="error-icon">\${severityIcon[severity] || '❌'}</span>
                                    <span>\${errorMessage}</span>
                                </div>
                                <div class="error-actions">
                                    <button onclick="retryLoad('\${sectionId}')" class="retry-button">🔄 Retry</button>
                                    \${hasCache ? '<button onclick="clearCache()" class="clear-cache-button">🗑️ Clear Cache</button>' : ''}
                                    <button onclick="forceRefresh()" class="retry-button">⚡ Force Refresh</button>
                                </div>
                            </div>
                        \`;

                        if (contentDiv) {
                            contentDiv.innerHTML = errorHtml;
                        }
                    }

                    function showCachedDataWarning(sectionId, warningMessage) {
                        const section = document.getElementById(sectionId);
                        let warningDiv = section.querySelector('.cached-data-warning');

                        if (!warningDiv) {
                            warningDiv = document.createElement('div');
                            warningDiv.className = 'cached-data-warning';
                            section.appendChild(warningDiv);
                        }

                        warningDiv.innerHTML = \`
                            <span class="cached-icon">📦</span>
                            <span>\${warningMessage || 'Showing cached data'}</span>
                        \`;
                    }

                    function showStatusMessage(message, type = 'info', duration = 0) {
                        const statusBar = document.getElementById('status-bar');
                        statusBar.className = 'status-bar ' + type;
                        statusBar.textContent = message;
                        statusBar.style.display = 'block';

                        if (duration > 0) {
                            setTimeout(() => {
                                statusBar.style.display = 'none';
                            }, duration);
                        }
                    }

                    function updateConnectionStatus(status) {
                        const connectionStatus = document.getElementById('connection-status');
                        const connectionIcon = document.getElementById('connection-icon');
                        const connectionText = document.getElementById('connection-text');

                        if (connectionStatus && connectionIcon && connectionText) {
                            connectionStatus.className = 'connection-status ' + status;

                            switch (status) {
                                case 'connected':
                                    connectionIcon.textContent = '🟢';
                                    connectionText.textContent = 'Connected';
                                    connectionStatus.classList.remove('pulse');
                                    break;
                                case 'disconnected':
                                    connectionIcon.textContent = '🔴';
                                    connectionText.textContent = 'Offline';
                                    connectionStatus.classList.remove('pulse');
                                    break;
                                case 'reconnecting':
                                    connectionIcon.textContent = '🟡';
                                    connectionText.textContent = 'Reconnecting...';
                                    connectionStatus.classList.add('pulse');
                                    break;
                            }
                        }
                    }

                    function enterOfflineMode(message, lastRefresh) {
                        updateConnectionStatus('disconnected');
                        showStatusMessage(message, 'offline');

                        if (lastRefresh) {
                            const refreshTime = new Date(lastRefresh).toLocaleTimeString();
                            showStatusMessage(\`\${message} Last refresh: \${refreshTime}\`, 'offline');
                        }
                    }

                    function exitOfflineMode(message) {
                        updateConnectionStatus('connected');
                        showStatusMessage(message, 'online', 3000);

                        // Remove cached data warnings
                        document.querySelectorAll('.cached-data-warning').forEach(warning => {
                            warning.remove();
                        });
                    }

                    function updateLastRefreshTime(timestamp) {
                        const refreshTime = new Date(timestamp).toLocaleTimeString();
                        // Could add a "Last updated" indicator in the UI if desired
                    }

                    function retryLoad(sectionId) {
                        const actionMap = {
                            'analytics-section': loadAnalytics,
                            'health-section': loadHealth,
                            'metrics-section': loadMetrics
                        };

                        const action = actionMap[sectionId];
                        if (action) {
                            action();
                        }
                    }

                    function retryConnection() {
                        vscode.postMessage({ type: 'retryConnection' });
                    }

                    function clearCache() {
                        vscode.postMessage({ type: 'clearCache' });
                    }

                    function forceRefresh() {
                        vscode.postMessage({ type: 'forceRefresh' });
                    }

                    // Real-time functionality
                    let realtimeEnabled = false;

                    function toggleRealtime() {
                        if (realtimeEnabled) {
                            vscode.postMessage({ type: 'disableRealtime' });
                        } else {
                            vscode.postMessage({ type: 'enableRealtime' });
                        }
                    }

                    function updateRealtimeToggle(enabled) {
                        realtimeEnabled = enabled;
                        const button = document.getElementById('realtime-toggle');
                        if (button) {
                            button.textContent = enabled ? '⏸️ Disable Real-time' : '▶️ Enable Real-time';
                            button.className = enabled ? 'action-button primary' : 'action-button';
                        }
                    }

                    function updateRealtimeStatus(status) {
                        const realtimeStatus = document.getElementById('realtime-status');
                        const realtimeIcon = document.getElementById('realtime-icon');
                        const realtimeText = document.getElementById('realtime-text');

                        if (realtimeStatus && realtimeIcon && realtimeText) {
                            realtimeStatus.className = 'connection-status ' + status;

                            switch (status) {
                                case 'connected':
                                    realtimeIcon.textContent = '🟢';
                                    realtimeText.textContent = 'Real-time On';
                                    realtimeStatus.classList.remove('pulse');
                                    break;
                                case 'disconnected':
                                    realtimeIcon.textContent = '🔴';
                                    realtimeText.textContent = 'Real-time Off';
                                    realtimeStatus.classList.remove('pulse');
                                    break;
                                case 'error':
                                    realtimeIcon.textContent = '⚠️';
                                    realtimeText.textContent = 'Real-time Error';
                                    realtimeStatus.classList.remove('pulse');
                                    break;
                            }
                        }
                    }

                    function handleRealtimeUpdate(updateType, data, timestamp) {
                        // Show real-time indicator
                        showStatusMessage(\`Real-time update: \${updateType}\`, 'info', 2000);

                        // Update the appropriate section with new data
                        switch (updateType) {
                            case 'memory_metrics':
                                displayMetricsData(data);
                                addRealtimeIndicator('metrics-section');
                                break;
                            case 'health_status':
                                displayHealthData(data);
                                addRealtimeIndicator('health-section');
                                break;
                            case 'analytics_report':
                                displayAnalyticsData(data);
                                addRealtimeIndicator('analytics-section');
                                break;
                            case 'optimization_complete':
                                showStatusMessage('Memory optimization completed', 'online', 5000);
                                // Refresh all data to show optimization results
                                refreshAll();
                                break;
                        }
                    }

                    function addRealtimeIndicator(sectionId) {
                        const section = document.getElementById(sectionId);
                        if (section) {
                            // Remove existing indicator
                            const existingIndicator = section.querySelector('.realtime-indicator');
                            if (existingIndicator) {
                                existingIndicator.remove();
                            }

                            // Add new indicator
                            const indicator = document.createElement('div');
                            indicator.className = 'realtime-indicator';
                            indicator.innerHTML = '🔴 Live';
                            indicator.style.cssText = \`
                                position: absolute;
                                top: 8px;
                                right: 8px;
                                background: var(--danger-color);
                                color: white;
                                padding: 2px 6px;
                                border-radius: 10px;
                                font-size: 0.7em;
                                animation: pulse 1s ease-in-out infinite;
                            \`;

                            section.style.position = 'relative';
                            section.appendChild(indicator);

                            // Remove indicator after 3 seconds
                            setTimeout(() => {
                                indicator.remove();
                            }, 3000);
                        }
                    }
                </script>
            </body>
            </html>
        `;
    }
}

export function registerMemoryAnalyticsDashboard(context: vscode.ExtensionContext, mcpClient: McpClient): void {
    const command = vscode.commands.registerCommand('autogen.openMemoryAnalyticsDashboard', () => {
        MemoryAnalyticsDashboardProvider.createOrShow(context, mcpClient);
    });

    context.subscriptions.push(command);
}

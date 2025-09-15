import * as vscode from 'vscode';
import { McpClient, MemoryHealthStatus, MemoryMetrics, ProjectRecommendationsRequest, ProjectRecommendationsResponse } from './mcpClient';

export interface IMemoryExplorerPanel {
    readonly panel: vscode.WebviewPanel;
    dispose(): void;
}

export interface MemoryItem {
    id: string;
    content: string;
    scope: string;
    type: 'conversation' | 'objective' | 'knowledge' | 'error' | 'insight';
    timestamp: string;
    metadata: Record<string, any>;
    score?: number;
}

export interface MemorySearchResult {
    results: MemoryItem[];
    total: number;
    query: string;
    scope: string;
}

export class MemoryExplorerPanelProvider {
    public static currentPanel: IMemoryExplorerPanel | undefined;
    private static readonly viewType = 'memoryExplorer';

    constructor(
        private readonly context: vscode.ExtensionContext,
        private readonly mcpClient: McpClient
    ) {}

    public static createOrShow(context: vscode.ExtensionContext, mcpClient: McpClient): void {
        const column = vscode.window.activeTextEditor
            ? vscode.window.activeTextEditor.viewColumn
            : undefined;

        // If we already have a panel, show it
        if (MemoryExplorerPanelProvider.currentPanel) {
            MemoryExplorerPanelProvider.currentPanel.panel.reveal(column);
            return;
        }

        // Otherwise, create a new panel
        const panel = vscode.window.createWebviewPanel(
            MemoryExplorerPanelProvider.viewType,
            'Memory Explorer',
            column || vscode.ViewColumn.One,
            {
                enableScripts: true,
                retainContextWhenHidden: true,
                localResourceRoots: [
                    vscode.Uri.joinPath(context.extensionUri, 'resources')
                ]
            }
        );

        MemoryExplorerPanelProvider.currentPanel = new MemoryExplorerPanel(panel, context, mcpClient);
    }

    public static revive(panel: vscode.WebviewPanel, context: vscode.ExtensionContext, mcpClient: McpClient): void {
        MemoryExplorerPanelProvider.currentPanel = new MemoryExplorerPanel(panel, context, mcpClient);
    }
}

class MemoryExplorerPanel implements IMemoryExplorerPanel {
    public readonly panel: vscode.WebviewPanel;
    private readonly disposables: vscode.Disposable[] = [];
    private healthData: MemoryHealthStatus | null = null;
    private metricsData: MemoryMetrics | null = null;
    private recommendationsData: ProjectRecommendationsResponse | null = null;

    constructor(
        panel: vscode.WebviewPanel,
        private readonly context: vscode.ExtensionContext,
        private readonly mcpClient: McpClient
    ) {
        this.panel = panel;

        // Set the webview's initial html content
        this.update();

        // Listen for when the panel is disposed
        // This happens when the user closes the panel or when the panel is closed programmatically
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
                    case 'searchMemory':
                        await this.handleSearchMemory(message.query, message.scope, message.filters);
                        break;
                    case 'loadMemories':
                        await this.handleLoadMemories();
                        break;
                    case 'exportMemories':
                        await this.handleExportMemories(message.memories);
                        break;
                    case 'deleteMemory':
                        await this.handleDeleteMemory(message.memoryId);
                        break;
                    case 'loadHealthData':
                        await this.handleLoadHealthData();
                        break;
                    case 'loadMetricsData':
                        await this.handleLoadMetricsData();
                        break;
                    case 'getCrossProjectSuggestions':
                        await this.handleGetCrossProjectSuggestions(message.projectData);
                        break;
                    case 'refreshAnalytics':
                        await this.handleRefreshAnalytics();
                        break;
                }
            },
            null,
            this.disposables
        );
    }

    public dispose(): void {
        MemoryExplorerPanelProvider.currentPanel = undefined;

        // Clean up our resources
        this.panel.dispose();

        while (this.disposables.length) {
            const x = this.disposables.pop();
            if (x) {
                x.dispose();
            }
        }
    }

    private async update(): Promise<void> {
        const webview = this.panel.webview;
        this.panel.title = 'Memory Explorer';
        this.panel.webview.html = await this.getHtmlForWebview(webview);
    }

    private async handleSearchMemory(query: string, scope: string, filters: any): Promise<void> {
        try {
            const isConnected = await this.mcpClient.isServerAvailable();
            if (!isConnected) {
                this.panel.webview.postMessage({
                    type: 'searchResults',
                    error: 'MCP server is not available'
                });
                return;
            }

            const results = await this.mcpClient.searchMemory({
                query,
                scope,
                k: filters.limit || 50
            });

            // Transform results to include additional metadata
            const memoryItems: MemoryItem[] = results.results.map((result, index) => ({
                id: `memory-${Date.now()}-${index}`,
                content: result.content,
                scope: scope,
                type: this.inferMemoryType(result.content),
                timestamp: new Date().toISOString(),
                metadata: result.metadata || {},
                score: result.score
            }));

            const searchResult: MemorySearchResult = {
                results: memoryItems,
                total: memoryItems.length,
                query,
                scope
            };

            this.panel.webview.postMessage({
                type: 'searchResults',
                data: searchResult
            });

        } catch (error) {
            this.panel.webview.postMessage({
                type: 'searchResults',
                error: error instanceof Error ? error.message : 'Search failed'
            });
        }
    }

    private async handleLoadMemories(): Promise<void> {
        try {
            // Load recent memories from all scopes
            const scopes = ['project', 'session', 'global'];
            const allMemories: MemoryItem[] = [];

            for (const scope of scopes) {
                try {
                    const results = await this.mcpClient.searchMemory({
                        query: '*',
                        scope,
                        k: 20
                    });

                    const memories: MemoryItem[] = results.results.map((result, index) => ({
                        id: `${scope}-${Date.now()}-${index}`,
                        content: result.content,
                        scope: scope,
                        type: this.inferMemoryType(result.content),
                        timestamp: new Date().toISOString(),
                        metadata: result.metadata || {},
                        score: result.score
                    }));

                    allMemories.push(...memories);
                } catch (error) {
                    console.warn(`Failed to load memories from scope ${scope}:`, error);
                }
            }

            this.panel.webview.postMessage({
                type: 'memoriesLoaded',
                data: allMemories
            });

        } catch (error) {
            this.panel.webview.postMessage({
                type: 'memoriesLoaded',
                error: error instanceof Error ? error.message : 'Failed to load memories'
            });
        }
    }

    private async handleExportMemories(memories: MemoryItem[]): Promise<void> {
        try {
            const content = this.formatMemoriesForExport(memories);
            const document = await vscode.workspace.openTextDocument({
                content,
                language: 'markdown'
            });
            await vscode.window.showTextDocument(document);

            vscode.window.showInformationMessage('Memories exported to new document');
        } catch (error) {
            vscode.window.showErrorMessage(`Export failed: ${error}`);
        }
    }

    private async handleDeleteMemory(memoryId: string): Promise<void> {
        // This would require an API endpoint to delete memories
        // For now, just show a notification
        vscode.window.showInformationMessage('Memory deletion would be implemented with server API');
    }

    private async handleLoadHealthData(): Promise<void> {
        try {
            const isConnected = await this.mcpClient.isServerAvailable();
            if (!isConnected) {
                this.panel.webview.postMessage({
                    type: 'healthError',
                    error: 'MCP server is not available'
                });
                return;
            }

            this.healthData = await this.mcpClient.getMemoryHealth();
            this.panel.webview.postMessage({
                type: 'healthData',
                data: this.healthData
            });

        } catch (error) {
            this.panel.webview.postMessage({
                type: 'healthError',
                error: error instanceof Error ? error.message : 'Failed to load health data'
            });
        }
    }

    private async handleLoadMetricsData(): Promise<void> {
        try {
            const isConnected = await this.mcpClient.isServerAvailable();
            if (!isConnected) {
                this.panel.webview.postMessage({
                    type: 'metricsError',
                    error: 'MCP server is not available'
                });
                return;
            }

            this.metricsData = await this.mcpClient.getMemoryMetrics();
            this.panel.webview.postMessage({
                type: 'metricsData',
                data: this.metricsData
            });

        } catch (error) {
            this.panel.webview.postMessage({
                type: 'metricsError',
                error: error instanceof Error ? error.message : 'Failed to load metrics data'
            });
        }
    }

    private async handleGetCrossProjectSuggestions(projectData: any): Promise<void> {
        try {
            const isConnected = await this.mcpClient.isServerAvailable();
            if (!isConnected) {
                this.panel.webview.postMessage({
                    type: 'suggestionsError',
                    error: 'MCP server is not available'
                });
                return;
            }

            const request: ProjectRecommendationsRequest = {
                current_project: projectData,
                recommendation_types: ['solution', 'pattern', 'best_practice'],
                max_recommendations: 5
            };

            this.recommendationsData = await this.mcpClient.getProjectRecommendations(request);
            this.panel.webview.postMessage({
                type: 'suggestionsData',
                data: this.recommendationsData
            });

        } catch (error) {
            this.panel.webview.postMessage({
                type: 'suggestionsError',
                error: error instanceof Error ? error.message : 'Failed to get cross-project suggestions'
            });
        }
    }

    private async handleRefreshAnalytics(): Promise<void> {
        await Promise.all([
            this.handleLoadHealthData(),
            this.handleLoadMetricsData()
        ]);
    }

    private inferMemoryType(content: string): MemoryItem['type'] {
        const lower = content.toLowerCase();
        if (lower.includes('error') || lower.includes('failed') || lower.includes('exception')) {
            return 'error';
        }
        if (lower.includes('objective') || lower.includes('goal') || lower.includes('task')) {
            return 'objective';
        }
        if (lower.includes('conversation') || lower.includes('chat') || lower.includes('message')) {
            return 'conversation';
        }
        if (lower.includes('insight') || lower.includes('learned') || lower.includes('discovered')) {
            return 'insight';
        }
        return 'knowledge';
    }

    private formatMemoriesForExport(memories: MemoryItem[]): string {
        let content = `# Memory Export\n\n`;
        content += `**Generated:** ${new Date().toLocaleString()}\n`;
        content += `**Total Memories:** ${memories.length}\n\n`;

        const groupedMemories = memories.reduce((groups, memory) => {
            if (!groups[memory.type]) {
                groups[memory.type] = [];
            }
            groups[memory.type].push(memory);
            return groups;
        }, {} as Record<string, MemoryItem[]>);

        for (const [type, typeMemories] of Object.entries(groupedMemories)) {
            content += `## ${type.charAt(0).toUpperCase() + type.slice(1)} (${typeMemories.length})\n\n`;

            typeMemories.forEach((memory, index) => {
                content += `### Memory ${index + 1}\n`;
                content += `**Scope:** ${memory.scope}\n`;
                content += `**Timestamp:** ${new Date(memory.timestamp).toLocaleString()}\n`;
                if (memory.score !== undefined) {
                    content += `**Score:** ${memory.score.toFixed(3)}\n`;
                }
                content += `\n${memory.content}\n\n`;
                if (Object.keys(memory.metadata).length > 0) {
                    content += `**Metadata:**\n\`\`\`json\n${JSON.stringify(memory.metadata, null, 2)}\n\`\`\`\n\n`;
                }
                content += '---\n\n';
            });
        }

        return content;
    }

    private async getHtmlForWebview(webview: vscode.Webview): Promise<string> {
        return `
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Memory Explorer</title>
                <style>
                    :root {
                        --vscode-font-family: var(--vscode-font-family);
                        --container-padding: 20px;
                        --border-radius: 6px;
                        --spacing-xs: 4px;
                        --spacing-sm: 8px;
                        --spacing-md: 16px;
                        --spacing-lg: 24px;
                    }

                    * {
                        box-sizing: border-box;
                    }

                    body {
                        font-family: var(--vscode-font-family);
                        padding: var(--container-padding);
                        margin: 0;
                        background-color: var(--vscode-editor-background);
                        color: var(--vscode-editor-foreground);
                        line-height: 1.5;
                    }

                    .header {
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-bottom: var(--spacing-lg);
                        padding-bottom: var(--spacing-md);
                        border-bottom: 1px solid var(--vscode-panel-border);
                    }

                    .search-container {
                        display: grid;
                        grid-template-columns: 1fr auto auto;
                        gap: var(--spacing-sm);
                        margin-bottom: var(--spacing-lg);
                        padding: var(--spacing-md);
                        background: var(--vscode-editor-inactiveSelectionBackground);
                        border-radius: var(--border-radius);
                        border: 1px solid var(--vscode-panel-border);
                    }

                    .search-row {
                        display: grid;
                        grid-template-columns: 2fr 1fr;
                        gap: var(--spacing-sm);
                        grid-column: 1 / -1;
                    }

                    .filters-row {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                        gap: var(--spacing-sm);
                        grid-column: 1 / -1;
                        margin-top: var(--spacing-sm);
                    }

                    input, select, button {
                        padding: var(--spacing-sm) var(--spacing-sm);
                        border: 1px solid var(--vscode-input-border);
                        border-radius: var(--border-radius);
                        background: var(--vscode-input-background);
                        color: var(--vscode-input-foreground);
                        font-family: inherit;
                    }

                    input:focus, select:focus {
                        outline: 1px solid var(--vscode-focusBorder);
                        outline-offset: -1px;
                    }

                    button {
                        background: var(--vscode-button-background);
                        color: var(--vscode-button-foreground);
                        border: 1px solid var(--vscode-button-border);
                        cursor: pointer;
                        transition: background-color 0.2s;
                    }

                    button:hover {
                        background: var(--vscode-button-hoverBackground);
                    }

                    button:disabled {
                        opacity: 0.6;
                        cursor: not-allowed;
                    }

                    .button-secondary {
                        background: var(--vscode-button-secondaryBackground);
                        color: var(--vscode-button-secondaryForeground);
                    }

                    .button-secondary:hover {
                        background: var(--vscode-button-secondaryHoverBackground);
                    }

                    .results-container {
                        margin-top: var(--spacing-lg);
                    }

                    .results-header {
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-bottom: var(--spacing-md);
                        padding: var(--spacing-sm) 0;
                        border-bottom: 1px solid var(--vscode-panel-border);
                    }

                    .results-stats {
                        font-size: 0.9em;
                        color: var(--vscode-descriptionForeground);
                    }

                    .memory-list {
                        display: grid;
                        gap: var(--spacing-md);
                    }

                    .memory-item {
                        padding: var(--spacing-md);
                        border: 1px solid var(--vscode-panel-border);
                        border-radius: var(--border-radius);
                        background: var(--vscode-editor-inactiveSelectionBackground);
                        transition: border-color 0.2s;
                    }

                    .memory-item:hover {
                        border-color: var(--vscode-focusBorder);
                    }

                    .memory-header {
                        display: flex;
                        justify-content: space-between;
                        align-items: flex-start;
                        margin-bottom: var(--spacing-sm);
                    }

                    .memory-meta {
                        display: flex;
                        gap: var(--spacing-md);
                        align-items: center;
                    }

                    .memory-type {
                        font-size: 0.8em;
                        padding: 2px 6px;
                        border-radius: 12px;
                        font-weight: 500;
                    }

                    .memory-type.conversation { background: #0e7490; color: white; }
                    .memory-type.objective { background: #059669; color: white; }
                    .memory-type.knowledge { background: #7c3aed; color: white; }
                    .memory-type.error { background: #dc2626; color: white; }
                    .memory-type.insight { background: #ea580c; color: white; }

                    .memory-scope {
                        font-size: 0.8em;
                        padding: 2px 6px;
                        background: var(--vscode-badge-background);
                        color: var(--vscode-badge-foreground);
                        border-radius: 4px;
                    }

                    .memory-score {
                        font-size: 0.8em;
                        color: var(--vscode-descriptionForeground);
                        font-family: var(--vscode-editor-font-family);
                    }

                    .memory-content {
                        line-height: 1.6;
                        margin-bottom: var(--spacing-sm);
                    }

                    .memory-timestamp {
                        font-size: 0.8em;
                        color: var(--vscode-descriptionForeground);
                    }

                    .loading {
                        text-align: center;
                        padding: var(--spacing-lg);
                        color: var(--vscode-descriptionForeground);
                    }

                    .error {
                        color: var(--vscode-errorForeground);
                        background: var(--vscode-inputValidation-errorBackground);
                        border: 1px solid var(--vscode-inputValidation-errorBorder);
                        padding: var(--spacing-md);
                        border-radius: var(--border-radius);
                        margin: var(--spacing-md) 0;
                    }

                    .empty-state {
                        text-align: center;
                        padding: var(--spacing-lg);
                        color: var(--vscode-descriptionForeground);
                    }

                    .empty-state h3 {
                        margin-bottom: var(--spacing-sm);
                    }

                    .actions {
                        display: flex;
                        gap: var(--spacing-sm);
                        margin-top: var(--spacing-md);
                    }

                    /* Analytics Styles */
                    .analytics-container, .cross-project-container {
                        margin: var(--spacing-lg) 0;
                        padding: var(--spacing-md);
                        border: 1px solid var(--vscode-panel-border);
                        border-radius: var(--border-radius);
                        background: var(--vscode-editor-inactiveSelectionBackground);
                    }

                    .analytics-header, .cross-project-header {
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-bottom: var(--spacing-md);
                        padding-bottom: var(--spacing-sm);
                        border-bottom: 1px solid var(--vscode-panel-border);
                    }

                    .analytics-actions {
                        display: flex;
                        gap: var(--spacing-sm);
                    }

                    .analytics-grid {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                        gap: var(--spacing-md);
                        margin-top: var(--spacing-md);
                    }

                    .analytics-card {
                        padding: var(--spacing-md);
                        border: 1px solid var(--vscode-panel-border);
                        border-radius: var(--border-radius);
                        background: var(--vscode-editor-background);
                    }

                    .analytics-card h3 {
                        margin: 0 0 var(--spacing-sm) 0;
                        color: var(--vscode-editor-foreground);
                    }

                    .analytics-content {
                        font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                        font-size: 0.9em;
                        line-height: 1.4;
                        white-space: pre-wrap;
                        color: var(--vscode-editor-foreground);
                    }

                    .health-status {
                        padding: var(--spacing-xs) var(--spacing-sm);
                        border-radius: var(--border-radius);
                        font-weight: bold;
                        margin: var(--spacing-xs) 0;
                    }

                    .health-good {
                        background: var(--vscode-charts-green);
                        color: white;
                    }

                    .health-warning {
                        background: var(--vscode-charts-yellow);
                        color: black;
                    }

                    .health-error {
                        background: var(--vscode-charts-red);
                        color: white;
                    }

                    .metric-item {
                        margin: var(--spacing-sm) 0;
                        padding: var(--spacing-sm);
                        border-left: 3px solid var(--vscode-focusBorder);
                        background: var(--vscode-editor-inactiveSelectionBackground);
                    }

                    .suggestion-item {
                        margin: var(--spacing-sm) 0;
                        padding: var(--spacing-md);
                        border: 1px solid var(--vscode-panel-border);
                        border-radius: var(--border-radius);
                        background: var(--vscode-editor-background);
                    }

                    .suggestion-title {
                        font-weight: bold;
                        margin-bottom: var(--spacing-xs);
                        color: var(--vscode-textLink-foreground);
                    }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🧠 Memory Explorer</h1>
                    <div class="actions">
                        <button onclick="loadRecentMemories()" class="button-secondary">Load Recent</button>
                        <button onclick="exportMemories()" class="button-secondary" id="exportBtn" disabled>Export</button>
                    </div>
                </div>

                <div class="search-container">
                    <div class="search-row">
                        <input
                            type="text"
                            id="searchQuery"
                            placeholder="Search memories..."
                            onkeypress="handleSearchKeyPress(event)"
                        />
                        <select id="searchScope">
                            <option value="project">Project</option>
                            <option value="session">Session</option>
                            <option value="global">Global</option>
                        </select>
                    </div>
                    <div class="filters-row">
                        <select id="typeFilter">
                            <option value="">All Types</option>
                            <option value="conversation">Conversation</option>
                            <option value="objective">Objective</option>
                            <option value="knowledge">Knowledge</option>
                            <option value="error">Error</option>
                            <option value="insight">Insight</option>
                        </select>
                        <input type="number" id="limitFilter" placeholder="Limit" value="50" min="1" max="200" />
                        <button onclick="searchMemories()">🔍 Search</button>
                        <button onclick="clearResults()" class="button-secondary">Clear</button>
                    </div>
                </div>

                <!-- Memory Analytics Section -->
                <div class="analytics-container" id="analyticsContainer" style="margin: var(--spacing-lg) 0; display: none;">
                    <div class="analytics-header">
                        <h2>📊 Memory Analytics</h2>
                        <div class="analytics-actions">
                            <button onclick="loadHealthData()" class="button-secondary">Health Check</button>
                            <button onclick="loadMetricsData()" class="button-secondary">Load Metrics</button>
                            <button onclick="refreshAnalytics()" class="button-secondary">Refresh</button>
                        </div>
                    </div>

                    <div class="analytics-grid">
                        <div class="analytics-card" id="healthCard" style="display: none;">
                            <h3>🏥 System Health</h3>
                            <div id="healthData" class="analytics-content"></div>
                        </div>

                        <div class="analytics-card" id="metricsCard" style="display: none;">
                            <h3>📈 Performance Metrics</h3>
                            <div id="metricsData" class="analytics-content"></div>
                        </div>
                    </div>
                </div>

                <!-- Cross-Project Intelligence Section -->
                <div class="cross-project-container" id="crossProjectContainer" style="margin: var(--spacing-lg) 0; display: none;">
                    <div class="cross-project-header">
                        <h2>🌐 Cross-Project Intelligence</h2>
                        <button onclick="getCrossProjectSuggestions()" class="button-secondary">Get Suggestions</button>
                    </div>

                    <div class="cross-project-content">
                        <div id="suggestionsData" class="analytics-content">
                            <p>Load cross-project suggestions to see relevant patterns and insights.</p>
                        </div>
                    </div>
                </div>

                <div class="results-container" id="resultsContainer" style="display: none;">
                    <div class="results-header">
                        <div class="results-stats" id="resultsStats"></div>
                    </div>
                    <div class="memory-list" id="memoryList"></div>
                </div>

                <div class="empty-state" id="emptyState">
                    <h3>No memories loaded</h3>
                    <p>Search for memories or load recent ones to get started.</p>
                </div>

                <script>
                    const vscode = acquireVsCodeApi();
                    let currentMemories = [];

                    // Handle messages from the extension
                    window.addEventListener('message', event => {
                        const message = event.data;
                        switch (message.type) {
                            case 'searchResults':
                                handleSearchResults(message);
                                break;
                            case 'memoriesLoaded':
                                handleMemoriesLoaded(message);
                                break;
                            case 'healthData':
                                handleHealthData(message);
                                break;
                            case 'metricsData':
                                handleMetricsData(message);
                                break;
                            case 'crossProjectSuggestions':
                                handleCrossProjectSuggestions(message);
                                break;
                            case 'analyticsRefreshed':
                                handleAnalyticsRefreshed(message);
                                break;
                        }
                    });

                    function searchMemories() {
                        const query = document.getElementById('searchQuery').value.trim();
                        const scope = document.getElementById('searchScope').value;
                        const typeFilter = document.getElementById('typeFilter').value;
                        const limit = parseInt(document.getElementById('limitFilter').value) || 50;

                        if (!query) {
                            showError('Please enter a search query');
                            return;
                        }

                        showLoading('Searching memories...');

                        vscode.postMessage({
                            type: 'searchMemory',
                            query,
                            scope,
                            filters: { type: typeFilter, limit }
                        });
                    }

                    function loadRecentMemories() {
                        showLoading('Loading recent memories...');
                        vscode.postMessage({ type: 'loadMemories' });
                    }

                    function exportMemories() {
                        if (currentMemories.length === 0) {
                            showError('No memories to export');
                            return;
                        }

                        vscode.postMessage({
                            type: 'exportMemories',
                            memories: currentMemories
                        });
                    }

                    function clearResults() {
                        currentMemories = [];
                        document.getElementById('resultsContainer').style.display = 'none';
                        document.getElementById('emptyState').style.display = 'block';
                        document.getElementById('exportBtn').disabled = true;
                    }

                    function handleSearchKeyPress(event) {
                        if (event.key === 'Enter') {
                            searchMemories();
                        }
                    }

                    function handleSearchResults(message) {
                        hideLoading();

                        if (message.error) {
                            showError(message.error);
                            return;
                        }

                        const searchResult = message.data;
                        currentMemories = searchResult.results;
                        displayMemories(searchResult);
                    }

                    function handleMemoriesLoaded(message) {
                        hideLoading();

                        if (message.error) {
                            showError(message.error);
                            return;
                        }

                        currentMemories = message.data;
                        displayMemories({
                            results: currentMemories,
                            total: currentMemories.length,
                            query: 'Recent memories',
                            scope: 'all'
                        });
                    }

                    function displayMemories(searchResult) {
                        const resultsContainer = document.getElementById('resultsContainer');
                        const emptyState = document.getElementById('emptyState');
                        const memoryList = document.getElementById('memoryList');
                        const resultsStats = document.getElementById('resultsStats');
                        const exportBtn = document.getElementById('exportBtn');

                        if (searchResult.results.length === 0) {
                            resultsContainer.style.display = 'none';
                            emptyState.style.display = 'block';
                            exportBtn.disabled = true;
                            return;
                        }

                        // Update stats
                        resultsStats.textContent = \`\${searchResult.total} memories found for "\${searchResult.query}" in \${searchResult.scope} scope\`;

                        // Clear previous results
                        memoryList.innerHTML = '';

                        // Add memory items
                        searchResult.results.forEach(memory => {
                            const memoryElement = createMemoryElement(memory);
                            memoryList.appendChild(memoryElement);
                        });

                        resultsContainer.style.display = 'block';
                        emptyState.style.display = 'none';
                        exportBtn.disabled = false;
                    }

                    function createMemoryElement(memory) {
                        const element = document.createElement('div');
                        element.className = 'memory-item';

                        const scoreDisplay = memory.score !== undefined ?
                            \`<span class="memory-score">Score: \${memory.score.toFixed(3)}</span>\` : '';

                        element.innerHTML = \`
                            <div class="memory-header">
                                <div class="memory-meta">
                                    <span class="memory-type \${memory.type}">\${memory.type}</span>
                                    <span class="memory-scope">\${memory.scope}</span>
                                    \${scoreDisplay}
                                </div>
                            </div>
                            <div class="memory-content">\${escapeHtml(memory.content)}</div>
                            <div class="memory-timestamp">\${new Date(memory.timestamp).toLocaleString()}</div>
                        \`;

                        return element;
                    }

                    function showLoading(message) {
                        const resultsContainer = document.getElementById('resultsContainer');
                        const emptyState = document.getElementById('emptyState');

                        resultsContainer.style.display = 'none';
                        emptyState.innerHTML = \`<div class="loading">\${message}</div>\`;
                        emptyState.style.display = 'block';
                    }

                    function hideLoading() {
                        // Loading will be hidden when results are displayed
                    }

                    function showError(message) {
                        const resultsContainer = document.getElementById('resultsContainer');
                        const emptyState = document.getElementById('emptyState');

                        resultsContainer.style.display = 'none';
                        emptyState.innerHTML = \`<div class="error">Error: \${escapeHtml(message)}</div>\`;
                        emptyState.style.display = 'block';
                    }

                    function escapeHtml(text) {
                        const div = document.createElement('div');
                        div.textContent = text;
                        return div.innerHTML;
                    }

                    // Load recent memories on startup
                    document.addEventListener('DOMContentLoaded', () => {
                        loadRecentMemories();
                    });

                    // Analytics Functions
                    function loadHealthData() {
                        vscode.postMessage({ type: 'loadHealthData' });
                    }

                    function loadMetricsData() {
                        vscode.postMessage({ type: 'loadMetricsData' });
                    }

                    function getCrossProjectSuggestions() {
                        vscode.postMessage({ type: 'getCrossProjectSuggestions' });
                    }

                    function refreshAnalytics() {
                        vscode.postMessage({ type: 'refreshAnalytics' });
                    }

                    function handleHealthData(message) {
                        const healthCard = document.getElementById('healthCard');
                        const healthData = document.getElementById('healthData');
                        const analyticsContainer = document.getElementById('analyticsContainer');

                        if (message.data) {
                            const health = message.data;
                            let healthHtml = '';

                            if (health.overall_status) {
                                const statusClass = health.overall_status.toLowerCase().replace(' ', '-');
                                healthHtml += '<div class="health-status health-' + statusClass + '">' + health.overall_status + '</div>';
                            }

                            if (health.memory_usage) {
                                healthHtml += '<div class="metric-item">Memory Usage: ' + health.memory_usage.used + '/' + health.memory_usage.total + '</div>';
                            }

                            if (health.performance_score) {
                                healthHtml += '<div class="metric-item">Performance Score: ' + health.performance_score + '</div>';
                            }

                            if (health.issues && health.issues.length > 0) {
                                healthHtml += '<div class="metric-item"><strong>Issues:</strong><ul>';
                                health.issues.forEach(issue => {
                                    healthHtml += '<li>' + escapeHtml(issue) + '</li>';
                                });
                                healthHtml += '</ul></div>';
                            }

                            healthData.innerHTML = healthHtml;
                            healthCard.style.display = 'block';
                            analyticsContainer.style.display = 'block';
                        } else {
                            showError('Failed to load health data');
                        }
                    }

                    function handleMetricsData(message) {
                        const metricsCard = document.getElementById('metricsCard');
                        const metricsData = document.getElementById('metricsData');
                        const analyticsContainer = document.getElementById('analyticsContainer');

                        if (message.data) {
                            const metrics = message.data;
                            let metricsHtml = '';

                            if (metrics.response_times) {
                                metricsHtml += '<div class="metric-item">Average Response Time: ' + metrics.response_times.average + 'ms</div>';
                                metricsHtml += '<div class="metric-item">95th Percentile: ' + metrics.response_times.p95 + 'ms</div>';
                            }

                            if (metrics.memory_efficiency) {
                                metricsHtml += '<div class="metric-item">Memory Efficiency: ' + metrics.memory_efficiency + '%</div>';
                            }

                            if (metrics.cache_hit_rate) {
                                metricsHtml += '<div class="metric-item">Cache Hit Rate: ' + metrics.cache_hit_rate + '%</div>';
                            }

                            if (metrics.total_memories) {
                                metricsHtml += '<div class="metric-item">Total Memories: ' + metrics.total_memories + '</div>';
                            }

                            if (metrics.recent_activity && metrics.recent_activity.length > 0) {
                                metricsHtml += '<div class="metric-item"><strong>Recent Activity:</strong><ul>';
                                metrics.recent_activity.slice(0, 5).forEach(activity => {
                                    metricsHtml += '<li>' + escapeHtml(activity) + '</li>';
                                });
                                metricsHtml += '</ul></div>';
                            }

                            metricsData.innerHTML = metricsHtml;
                            metricsCard.style.display = 'block';
                            analyticsContainer.style.display = 'block';
                        } else {
                            showError('Failed to load metrics data');
                        }
                    }

                    function handleCrossProjectSuggestions(message) {
                        const suggestionsData = document.getElementById('suggestionsData');
                        const crossProjectContainer = document.getElementById('crossProjectContainer');

                        if (message.data && message.data.length > 0) {
                            let suggestionsHtml = '';
                            message.data.forEach(suggestion => {
                                const title = escapeHtml(suggestion.title || 'Suggestion');
                                const content = escapeHtml(suggestion.description || suggestion.content || '');
                                const similarity = suggestion.similarity_score ? '<div><small>Similarity: ' + suggestion.similarity_score + '%</small></div>' : '';

                                suggestionsHtml += '<div class="suggestion-item">' +
                                    '<div class="suggestion-title">' + title + '</div>' +
                                    '<div>' + content + '</div>' +
                                    similarity +
                                    '</div>';
                            });
                            suggestionsData.innerHTML = suggestionsHtml;
                        } else {
                            suggestionsData.innerHTML = '<p>No cross-project suggestions found.</p>';
                        }

                        crossProjectContainer.style.display = 'block';
                    }

                    function handleAnalyticsRefreshed(message) {
                        if (message.success) {
                            // Reload any visible analytics sections
                            const healthCard = document.getElementById('healthCard');
                            const metricsCard = document.getElementById('metricsCard');

                            if (healthCard.style.display !== 'none') {
                                loadHealthData();
                            }
                            if (metricsCard.style.display !== 'none') {
                                loadMetricsData();
                            }
                        } else {
                            showError('Failed to refresh analytics data');
                        }
                    }
                </script>
            </body>
            </html>
        `;
    }
}

// Register command to open memory explorer
export function registerMemoryExplorerCommand(context: vscode.ExtensionContext, mcpClient: McpClient): void {
    const command = vscode.commands.registerCommand('autogen.openMemoryExplorer', () => {
        MemoryExplorerPanelProvider.createOrShow(context, mcpClient);
    });

    context.subscriptions.push(command);
}

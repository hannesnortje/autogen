import * as vscode from 'vscode';
import { McpClient, ProjectRegistration, ProjectRecommendationsRequest, ProjectRecommendationsResponse, CrossProjectAnalysis } from './mcpClient';

export interface ICrossProjectPanel {
    readonly panel: vscode.WebviewPanel;
    dispose(): void;
}

export class CrossProjectPanelProvider {
    public static currentPanel: ICrossProjectPanel | undefined;
    private static readonly viewType = 'crossProjectPanel';

    constructor(
        private readonly context: vscode.ExtensionContext,
        private readonly mcpClient: McpClient
    ) {}

    public static createOrShow(context: vscode.ExtensionContext, mcpClient: McpClient): void {
        const column = vscode.window.activeTextEditor
            ? vscode.window.activeTextEditor.viewColumn
            : undefined;

        // If we already have a panel, show it
        if (CrossProjectPanelProvider.currentPanel) {
            CrossProjectPanelProvider.currentPanel.panel.reveal(column);
            return;
        }

        // Otherwise, create a new panel
        const panel = vscode.window.createWebviewPanel(
            CrossProjectPanelProvider.viewType,
            'Cross-Project Intelligence',
            column || vscode.ViewColumn.One,
            {
                enableScripts: true,
                retainContextWhenHidden: true,
                localResourceRoots: [
                    vscode.Uri.joinPath(context.extensionUri, 'resources')
                ]
            }
        );

        CrossProjectPanelProvider.currentPanel = new CrossProjectPanel(panel, context, mcpClient);
    }

    public static revive(panel: vscode.WebviewPanel, context: vscode.ExtensionContext, mcpClient: McpClient): void {
        CrossProjectPanelProvider.currentPanel = new CrossProjectPanel(panel, context, mcpClient);
    }
}

class CrossProjectPanel implements ICrossProjectPanel {
    public readonly panel: vscode.WebviewPanel;
    private readonly disposables: vscode.Disposable[] = [];
    private recommendationsData: ProjectRecommendationsResponse | null = null;
    private analysisData: CrossProjectAnalysis | null = null;

    constructor(
        panel: vscode.WebviewPanel,
        private readonly context: vscode.ExtensionContext,
        private readonly mcpClient: McpClient
    ) {
        this.panel = panel;

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
                    case 'registerProject':
                        await this.handleRegisterProject(message.data);
                        break;
                    case 'getRecommendations':
                        await this.handleGetRecommendations(message.data);
                        break;
                    case 'loadAnalysis':
                        await this.loadAnalysisData();
                        break;
                    case 'refreshAll':
                        await this.refreshAllData();
                        break;
                }
            },
            null,
            this.disposables
        );
    }

    public dispose(): void {
        CrossProjectPanelProvider.currentPanel = undefined;

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
        this.panel.title = 'Cross-Project Intelligence';
        this.panel.webview.html = await this.getHtmlForWebview(webview);

        // Load initial analysis data
        await this.loadAnalysisData();
    }

    private async refreshAllData(): Promise<void> {
        await this.loadAnalysisData();
    }

    private async handleRegisterProject(data: ProjectRegistration): Promise<void> {
        try {
            const isConnected = await this.mcpClient.isServerAvailable();
            if (!isConnected) {
                this.panel.webview.postMessage({
                    type: 'registrationError',
                    error: 'MCP server is not available'
                });
                return;
            }

            const result = await this.mcpClient.registerProject(data);
            this.panel.webview.postMessage({
                type: 'registrationSuccess',
                data: result
            });

            // Refresh analysis data after registration
            await this.loadAnalysisData();

        } catch (error) {
            this.panel.webview.postMessage({
                type: 'registrationError',
                error: error instanceof Error ? error.message : 'Failed to register project'
            });
        }
    }

    private async handleGetRecommendations(data: ProjectRecommendationsRequest): Promise<void> {
        try {
            const isConnected = await this.mcpClient.isServerAvailable();
            if (!isConnected) {
                this.panel.webview.postMessage({
                    type: 'recommendationsError',
                    error: 'MCP server is not available'
                });
                return;
            }

            this.recommendationsData = await this.mcpClient.getProjectRecommendations(data);
            this.panel.webview.postMessage({
                type: 'recommendationsData',
                data: this.recommendationsData
            });

        } catch (error) {
            this.panel.webview.postMessage({
                type: 'recommendationsError',
                error: error instanceof Error ? error.message : 'Failed to get recommendations'
            });
        }
    }

    private async loadAnalysisData(): Promise<void> {
        try {
            const isConnected = await this.mcpClient.isServerAvailable();
            if (!isConnected) {
                this.panel.webview.postMessage({
                    type: 'analysisError',
                    error: 'MCP server is not available'
                });
                return;
            }

            this.analysisData = await this.mcpClient.getCrossProjectAnalysis();
            this.panel.webview.postMessage({
                type: 'analysisData',
                data: this.analysisData
            });

        } catch (error) {
            this.panel.webview.postMessage({
                type: 'analysisError',
                error: error instanceof Error ? error.message : 'Failed to load analysis data'
            });
        }
    }

    private async getHtmlForWebview(webview: vscode.Webview): Promise<string> {
        return `
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Cross-Project Intelligence</title>
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
                        background: linear-gradient(45deg, var(--primary-color), #ff6b6b);
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

                    .tab-container {
                        margin-bottom: 24px;
                    }

                    .tab-buttons {
                        display: flex;
                        gap: 2px;
                        margin-bottom: 16px;
                        border-bottom: 1px solid var(--vscode-panel-border);
                    }

                    .tab-button {
                        padding: 12px 24px;
                        border: none;
                        background: var(--vscode-tab-inactiveBackground);
                        color: var(--vscode-tab-inactiveForeground);
                        cursor: pointer;
                        border-top-left-radius: var(--border-radius);
                        border-top-right-radius: var(--border-radius);
                        transition: all var(--animation-duration);
                    }

                    .tab-button:hover {
                        background: var(--vscode-tab-hoverBackground);
                    }

                    .tab-button.active {
                        background: var(--vscode-tab-activeBackground);
                        color: var(--vscode-tab-activeForeground);
                        border-bottom: 2px solid var(--primary-color);
                    }

                    .tab-content {
                        display: none;
                        background: var(--vscode-editor-inactiveSelectionBackground);
                        border: 1px solid var(--vscode-panel-border);
                        border-radius: var(--border-radius);
                        padding: 24px;
                    }

                    .tab-content.active {
                        display: block;
                    }

                    .form-group {
                        margin-bottom: 16px;
                    }

                    .form-label {
                        display: block;
                        margin-bottom: 8px;
                        font-weight: 600;
                        color: var(--vscode-foreground);
                    }

                    .form-input {
                        width: 100%;
                        padding: 8px 12px;
                        border: 1px solid var(--vscode-input-border);
                        border-radius: var(--border-radius);
                        background: var(--vscode-input-background);
                        color: var(--vscode-input-foreground);
                        font-family: inherit;
                    }

                    .form-input:focus {
                        outline: none;
                        border-color: var(--primary-color);
                        box-shadow: 0 0 0 2px rgba(0, 122, 204, 0.2);
                    }

                    .form-textarea {
                        min-height: 80px;
                        resize: vertical;
                    }

                    .form-select {
                        width: 100%;
                        padding: 8px 12px;
                        border: 1px solid var(--vscode-input-border);
                        border-radius: var(--border-radius);
                        background: var(--vscode-dropdown-background);
                        color: var(--vscode-dropdown-foreground);
                        font-family: inherit;
                    }

                    .tags-input {
                        display: flex;
                        flex-wrap: wrap;
                        gap: 8px;
                        margin-top: 8px;
                    }

                    .tag {
                        background: var(--primary-color);
                        color: white;
                        padding: 4px 8px;
                        border-radius: 12px;
                        font-size: 0.8em;
                        display: flex;
                        align-items: center;
                        gap: 4px;
                    }

                    .tag-remove {
                        cursor: pointer;
                        font-weight: bold;
                    }

                    .recommendations-grid {
                        display: grid;
                        gap: 16px;
                        margin-top: 16px;
                    }

                    .recommendation-card {
                        background: var(--vscode-button-background);
                        border: 1px solid var(--vscode-panel-border);
                        border-radius: var(--border-radius);
                        padding: 16px;
                        transition: transform var(--animation-duration), box-shadow var(--animation-duration);
                    }

                    .recommendation-card:hover {
                        transform: translateY(-2px);
                        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                    }

                    .recommendation-header {
                        display: flex;
                        justify-content: space-between;
                        align-items: flex-start;
                        margin-bottom: 12px;
                    }

                    .recommendation-title {
                        font-size: 1.1em;
                        font-weight: 600;
                        margin: 0;
                    }

                    .recommendation-type {
                        padding: 4px 8px;
                        border-radius: 12px;
                        font-size: 0.8em;
                        font-weight: 600;
                        text-transform: uppercase;
                    }

                    .recommendation-type.solution {
                        background: var(--success-color);
                        color: white;
                    }

                    .recommendation-type.pattern {
                        background: var(--info-color);
                        color: white;
                    }

                    .recommendation-type.best_practice {
                        background: var(--warning-color);
                        color: black;
                    }

                    .recommendation-type.similar_project {
                        background: var(--primary-color);
                        color: white;
                    }

                    .relevance-score {
                        font-size: 1.2em;
                        font-weight: bold;
                        color: var(--primary-color);
                    }

                    .recommendation-description {
                        margin-bottom: 12px;
                        color: var(--vscode-descriptionForeground);
                    }

                    .recommendation-tags {
                        display: flex;
                        flex-wrap: wrap;
                        gap: 4px;
                        margin-bottom: 12px;
                    }

                    .recommendation-tag {
                        background: var(--vscode-badge-background);
                        color: var(--vscode-badge-foreground);
                        padding: 2px 6px;
                        border-radius: 8px;
                        font-size: 0.7em;
                    }

                    .stats-grid {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                        gap: 16px;
                        margin-top: 16px;
                    }

                    .stat-card {
                        background: var(--vscode-button-background);
                        border: 1px solid var(--vscode-panel-border);
                        border-radius: var(--border-radius);
                        padding: 16px;
                        text-align: center;
                        transition: background-color var(--animation-duration);
                    }

                    .stat-card:hover {
                        background: var(--vscode-button-hoverBackground);
                    }

                    .stat-value {
                        font-size: 2em;
                        font-weight: bold;
                        color: var(--primary-color);
                        display: block;
                        margin-bottom: 4px;
                    }

                    .stat-label {
                        font-size: 0.9em;
                        color: var(--vscode-descriptionForeground);
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

                    .success {
                        color: var(--success-color);
                        background: rgba(40, 167, 69, 0.1);
                        border: 1px solid var(--success-color);
                        border-radius: var(--border-radius);
                        padding: 16px;
                        margin: 16px 0;
                    }

                    .similar-projects {
                        margin-top: 16px;
                    }

                    .similar-project {
                        background: var(--vscode-list-inactiveSelectionBackground);
                        border-left: 4px solid var(--primary-color);
                        padding: 12px;
                        margin-bottom: 8px;
                        border-radius: 0 var(--border-radius) var(--border-radius) 0;
                    }

                    .similar-project-name {
                        font-weight: 600;
                        margin-bottom: 4px;
                    }

                    .similar-project-details {
                        font-size: 0.9em;
                        color: var(--vscode-descriptionForeground);
                    }

                    @keyframes pulse {
                        0% { opacity: 1; }
                        50% { opacity: 0.7; }
                        100% { opacity: 1; }
                    }

                    .pulsing {
                        animation: pulse 2s infinite;
                    }

                    @media (max-width: 768px) {
                        .stats-grid {
                            grid-template-columns: 1fr;
                        }

                        .recommendations-grid {
                            grid-template-columns: 1fr;
                        }

                        .tab-buttons {
                            flex-direction: column;
                        }
                    }
                </style>
            </head>
            <body>
                <div class="dashboard-header">
                    <h1 class="dashboard-title">🌐 Cross-Project Intelligence</h1>
                    <div class="header-actions">
                        <button onclick="refreshAll()" class="action-button">🔄 Refresh</button>
                        <button onclick="loadAnalysis()" class="action-button">📊 Analysis</button>
                    </div>
                </div>

                <div class="tab-container">
                    <div class="tab-buttons">
                        <button class="tab-button active" onclick="showTab('register')">🏗️ Register Project</button>
                        <button class="tab-button" onclick="showTab('recommendations')">💡 Get Recommendations</button>
                        <button class="tab-button" onclick="showTab('analysis')">📊 Global Analysis</button>
                    </div>

                    <div id="register-tab" class="tab-content active">
                        <h3>🏗️ Register New Project</h3>
                        <form id="project-registration-form">
                            <div class="form-group">
                                <label class="form-label" for="project-name">Project Name *</label>
                                <input type="text" id="project-name" class="form-input" required>
                            </div>

                            <div class="form-group">
                                <label class="form-label" for="project-description">Description *</label>
                                <textarea id="project-description" class="form-input form-textarea" required></textarea>
                            </div>

                            <div class="form-group">
                                <label class="form-label" for="project-domain">Domain *</label>
                                <select id="project-domain" class="form-select" required>
                                    <option value="">Select domain...</option>
                                    <option value="web">Web Development</option>
                                    <option value="mobile">Mobile Development</option>
                                    <option value="data-science">Data Science</option>
                                    <option value="devops">DevOps/Infrastructure</option>
                                    <option value="ml">Machine Learning</option>
                                    <option value="backend">Backend Services</option>
                                    <option value="frontend">Frontend Applications</option>
                                    <option value="fullstack">Full Stack</option>
                                    <option value="embedded">Embedded Systems</option>
                                    <option value="desktop">Desktop Applications</option>
                                </select>
                            </div>

                            <div class="form-group">
                                <label class="form-label" for="tech-stack-input">Technology Stack *</label>
                                <input type="text" id="tech-stack-input" class="form-input"
                                       placeholder="Enter technology and press Enter (e.g., Python, React, Docker)">
                                <div id="tech-stack-tags" class="tags-input"></div>
                            </div>

                            <div class="form-group">
                                <label class="form-label" for="patterns-input">Design Patterns (Optional)</label>
                                <input type="text" id="patterns-input" class="form-input"
                                       placeholder="Enter pattern and press Enter (e.g., MVC, Observer, Factory)">
                                <div id="patterns-tags" class="tags-input"></div>
                            </div>

                            <button type="submit" class="action-button primary">🚀 Register Project</button>
                        </form>
                        <div id="registration-result"></div>
                    </div>

                    <div id="recommendations-tab" class="tab-content">
                        <h3>💡 Get Project Recommendations</h3>
                        <form id="recommendations-form">
                            <div class="form-group">
                                <label class="form-label" for="current-project-name">Current Project Name *</label>
                                <input type="text" id="current-project-name" class="form-input" required>
                            </div>

                            <div class="form-group">
                                <label class="form-label" for="current-project-description">Project Description</label>
                                <textarea id="current-project-description" class="form-input form-textarea"></textarea>
                            </div>

                            <div class="form-group">
                                <label class="form-label" for="current-project-domain">Project Domain *</label>
                                <select id="current-project-domain" class="form-select" required>
                                    <option value="">Select domain...</option>
                                    <option value="web">Web Development</option>
                                    <option value="mobile">Mobile Development</option>
                                    <option value="data-science">Data Science</option>
                                    <option value="devops">DevOps/Infrastructure</option>
                                    <option value="ml">Machine Learning</option>
                                    <option value="backend">Backend Services</option>
                                    <option value="frontend">Frontend Applications</option>
                                    <option value="fullstack">Full Stack</option>
                                    <option value="embedded">Embedded Systems</option>
                                    <option value="desktop">Desktop Applications</option>
                                </select>
                            </div>

                            <div class="form-group">
                                <label class="form-label" for="current-tech-stack-input">Current Technology Stack *</label>
                                <input type="text" id="current-tech-stack-input" class="form-input"
                                       placeholder="Enter technology and press Enter">
                                <div id="current-tech-stack-tags" class="tags-input"></div>
                            </div>

                            <div class="form-group">
                                <label class="form-label" for="current-challenge">Current Challenge (Optional)</label>
                                <textarea id="current-challenge" class="form-input form-textarea"
                                          placeholder="Describe any specific challenges you're facing..."></textarea>
                            </div>

                            <button type="submit" class="action-button primary">🔍 Get Recommendations</button>
                        </form>
                        <div id="recommendations-result"></div>
                    </div>

                    <div id="analysis-tab" class="tab-content">
                        <h3>📊 Cross-Project Analysis</h3>
                        <div id="analysis-content" class="loading">Loading analysis data...</div>
                    </div>
                </div>

                <script>
                    const vscode = acquireVsCodeApi();
                    let techStackTags = [];
                    let patternTags = [];
                    let currentTechStackTags = [];

                    function showTab(tabName) {
                        // Hide all tabs
                        document.querySelectorAll('.tab-content').forEach(tab => {
                            tab.classList.remove('active');
                        });
                        document.querySelectorAll('.tab-button').forEach(button => {
                            button.classList.remove('active');
                        });

                        // Show selected tab
                        document.getElementById(tabName + '-tab').classList.add('active');
                        event.target.classList.add('active');

                        // Load data if needed
                        if (tabName === 'analysis') {
                            loadAnalysis();
                        }
                    }

                    function addTag(tagArray, tagContainer, value) {
                        if (value && !tagArray.includes(value)) {
                            tagArray.push(value);
                            renderTags(tagArray, tagContainer);
                        }
                    }

                    function removeTag(tagArray, tagContainer, value) {
                        const index = tagArray.indexOf(value);
                        if (index > -1) {
                            tagArray.splice(index, 1);
                            renderTags(tagArray, tagContainer);
                        }
                    }

                    function renderTags(tagArray, tagContainer) {
                        const container = document.getElementById(tagContainer);
                        container.innerHTML = tagArray.map(tag =>
                            \`<div class="tag">\${tag}<span class="tag-remove" onclick="removeTag(\${tagContainer.includes('tech-stack') ? 'techStackTags' : tagContainer.includes('patterns') ? 'patternTags' : 'currentTechStackTags'}, '\${tagContainer}', '\${tag}')">×</span></div>\`
                        ).join('');
                    }

                    function loadAnalysis() {
                        document.getElementById('analysis-content').innerHTML = '<div class="loading pulsing">Loading analysis data...</div>';
                        vscode.postMessage({ type: 'loadAnalysis' });
                    }

                    function refreshAll() {
                        vscode.postMessage({ type: 'refreshAll' });
                        loadAnalysis();
                    }

                    // Setup form handlers
                    document.addEventListener('DOMContentLoaded', function() {
                        // Tech stack input handler for registration
                        document.getElementById('tech-stack-input').addEventListener('keypress', function(e) {
                            if (e.key === 'Enter') {
                                e.preventDefault();
                                const value = this.value.trim();
                                if (value) {
                                    addTag(techStackTags, 'tech-stack-tags', value);
                                    this.value = '';
                                }
                            }
                        });

                        // Patterns input handler
                        document.getElementById('patterns-input').addEventListener('keypress', function(e) {
                            if (e.key === 'Enter') {
                                e.preventDefault();
                                const value = this.value.trim();
                                if (value) {
                                    addTag(patternTags, 'patterns-tags', value);
                                    this.value = '';
                                }
                            }
                        });

                        // Current tech stack input handler
                        document.getElementById('current-tech-stack-input').addEventListener('keypress', function(e) {
                            if (e.key === 'Enter') {
                                e.preventDefault();
                                const value = this.value.trim();
                                if (value) {
                                    addTag(currentTechStackTags, 'current-tech-stack-tags', value);
                                    this.value = '';
                                }
                            }
                        });

                        // Project registration form
                        document.getElementById('project-registration-form').addEventListener('submit', function(e) {
                            e.preventDefault();
                            const formData = {
                                name: document.getElementById('project-name').value,
                                description: document.getElementById('project-description').value,
                                domain: document.getElementById('project-domain').value,
                                tech_stack: techStackTags,
                                patterns_used: patternTags
                            };

                            vscode.postMessage({
                                type: 'registerProject',
                                data: formData
                            });
                        });

                        // Recommendations form
                        document.getElementById('recommendations-form').addEventListener('submit', function(e) {
                            e.preventDefault();
                            const formData = {
                                current_project: {
                                    name: document.getElementById('current-project-name').value,
                                    description: document.getElementById('current-project-description').value || undefined,
                                    domain: document.getElementById('current-project-domain').value,
                                    tech_stack: currentTechStackTags,
                                    current_challenge: document.getElementById('current-challenge').value || undefined
                                },
                                recommendation_types: ['solution', 'pattern', 'best_practice', 'similar_project'],
                                max_recommendations: 10
                            };

                            document.getElementById('recommendations-result').innerHTML = '<div class="loading pulsing">Getting recommendations...</div>';
                            vscode.postMessage({
                                type: 'getRecommendations',
                                data: formData
                            });
                        });

                        // Load initial analysis
                        loadAnalysis();
                    });

                    // Handle messages from the extension
                    window.addEventListener('message', event => {
                        const message = event.data;

                        switch (message.type) {
                            case 'registrationSuccess':
                                displayRegistrationSuccess(message.data);
                                break;
                            case 'registrationError':
                                document.getElementById('registration-result').innerHTML =
                                    '<div class="error">❌ ' + message.error + '</div>';
                                break;
                            case 'recommendationsData':
                                displayRecommendations(message.data);
                                break;
                            case 'recommendationsError':
                                document.getElementById('recommendations-result').innerHTML =
                                    '<div class="error">❌ ' + message.error + '</div>';
                                break;
                            case 'analysisData':
                                displayAnalysis(message.data);
                                break;
                            case 'analysisError':
                                document.getElementById('analysis-content').innerHTML =
                                    '<div class="error">❌ ' + message.error + '</div>';
                                break;
                        }
                    });

                    function displayRegistrationSuccess(data) {
                        document.getElementById('registration-result').innerHTML =
                            \`<div class="success">✅ Project registered successfully! Project ID: \${data.project_id}</div>\`;

                        // Clear form
                        document.getElementById('project-registration-form').reset();
                        techStackTags = [];
                        patternTags = [];
                        renderTags(techStackTags, 'tech-stack-tags');
                        renderTags(patternTags, 'patterns-tags');
                    }

                    function displayRecommendations(data) {
                        const container = document.getElementById('recommendations-result');

                        let recommendationsHtml = '';
                        if (data.recommendations && data.recommendations.length > 0) {
                            recommendationsHtml = \`
                                <h4>💡 Recommendations (\${data.recommendations.length})</h4>
                                <div class="recommendations-grid">
                                    \${data.recommendations.map(rec => \`
                                        <div class="recommendation-card">
                                            <div class="recommendation-header">
                                                <h5 class="recommendation-title">\${rec.title}</h5>
                                                <div>
                                                    <span class="recommendation-type \${rec.type}">\${rec.type.replace('_', ' ')}</span>
                                                    <div class="relevance-score">\${(rec.relevance_score * 100).toFixed(1)}%</div>
                                                </div>
                                            </div>
                                            <div class="recommendation-description">\${rec.description}</div>
                                            <div class="recommendation-tags">
                                                \${rec.tags.map(tag => \`<span class="recommendation-tag">\${tag}</span>\`).join('')}
                                            </div>
                                            <div><strong>Source:</strong> \${rec.source_project}</div>
                                            <div><strong>Implementation:</strong> \${rec.implementation_guide}</div>
                                        </div>
                                    \`).join('')}
                                </div>
                            \`;
                        } else {
                            recommendationsHtml = '<div class="loading">No recommendations found for your project.</div>';
                        }

                        let similarProjectsHtml = '';
                        if (data.similar_projects && data.similar_projects.length > 0) {
                            similarProjectsHtml = \`
                                <h4>🔗 Similar Projects (\${data.similar_projects.length})</h4>
                                <div class="similar-projects">
                                    \${data.similar_projects.map(proj => \`
                                        <div class="similar-project">
                                            <div class="similar-project-name">\${proj.name} (Similarity: \${(proj.similarity_score * 100).toFixed(1)}%)</div>
                                            <div class="similar-project-details">
                                                <strong>Shared Patterns:</strong> \${proj.shared_patterns.join(', ') || 'None'}<br>
                                                <strong>Tech Overlap:</strong> \${proj.tech_overlap.join(', ') || 'None'}
                                            </div>
                                        </div>
                                    \`).join('')}
                                </div>
                            \`;
                        }

                        container.innerHTML = recommendationsHtml + similarProjectsHtml;
                    }

                    function displayAnalysis(data) {
                        const container = document.getElementById('analysis-content');

                        container.innerHTML = \`
                            <div class="stats-grid">
                                <div class="stat-card">
                                    <span class="stat-value">\${data.total_projects}</span>
                                    <span class="stat-label">Total Projects</span>
                                </div>
                                <div class="stat-card">
                                    <span class="stat-value">\${Object.keys(data.pattern_frequency).length}</span>
                                    <span class="stat-label">Unique Patterns</span>
                                </div>
                                <div class="stat-card">
                                    <span class="stat-value">\${Object.keys(data.tech_stack_distribution).length}</span>
                                    <span class="stat-label">Technologies</span>
                                </div>
                                <div class="stat-card">
                                    <span class="stat-value">\${Object.keys(data.domain_distribution).length}</span>
                                    <span class="stat-label">Domains</span>
                                </div>
                            </div>

                            <h4>🚀 Top Patterns</h4>
                            <div class="recommendations-grid">
                                \${Object.entries(data.pattern_frequency)
                                    .sort(([,a], [,b]) => b - a)
                                    .slice(0, 6)
                                    .map(([pattern, count]) => \`
                                        <div class="recommendation-card">
                                            <div class="recommendation-header">
                                                <h5 class="recommendation-title">\${pattern}</h5>
                                                <div class="relevance-score">\${count}</div>
                                            </div>
                                            <div class="recommendation-description">Used in \${count} project(s)</div>
                                        </div>
                                    \`).join('')}
                            </div>

                            <h4>💼 Domain Distribution</h4>
                            <div class="recommendations-grid">
                                \${Object.entries(data.domain_distribution)
                                    .sort(([,a], [,b]) => b - a)
                                    .map(([domain, count]) => \`
                                        <div class="recommendation-card">
                                            <div class="recommendation-header">
                                                <h5 class="recommendation-title">\${domain}</h5>
                                                <div class="relevance-score">\${count}</div>
                                            </div>
                                            <div class="recommendation-description">\${((count / data.total_projects) * 100).toFixed(1)}% of projects</div>
                                        </div>
                                    \`).join('')}
                            </div>

                            \${data.success_patterns && data.success_patterns.length > 0 ? \`
                                <h4>⭐ Success Patterns</h4>
                                <div class="recommendations-grid">
                                    \${data.success_patterns.slice(0, 4).map(pattern => \`
                                        <div class="recommendation-card">
                                            <div class="recommendation-header">
                                                <h5 class="recommendation-title">\${pattern.pattern}</h5>
                                                <div class="relevance-score">\${(pattern.success_rate * 100).toFixed(1)}%</div>
                                            </div>
                                            <div class="recommendation-description">
                                                Success rate in \${pattern.projects_count} projects
                                            </div>
                                        </div>
                                    \`).join('')}
                                </div>
                            \` : ''}

                            \${data.emerging_trends && data.emerging_trends.length > 0 ? \`
                                <h4>📈 Emerging Trends</h4>
                                <div class="recommendations-grid">
                                    \${data.emerging_trends.slice(0, 4).map(trend => \`
                                        <div class="recommendation-card">
                                            <div class="recommendation-header">
                                                <h5 class="recommendation-title">\${trend.trend}</h5>
                                                <div class="relevance-score">+\${(trend.growth_rate * 100).toFixed(1)}%</div>
                                            </div>
                                            <div class="recommendation-description">
                                                \${trend.description}<br>
                                                <strong>Adoption:</strong> \${trend.adoption_count} projects
                                            </div>
                                        </div>
                                    \`).join('')}
                                </div>
                            \` : ''}
                        \`;
                    }
                </script>
            </body>
            </html>
        `;
    }
}

export function registerCrossProjectPanel(context: vscode.ExtensionContext, mcpClient: McpClient): void {
    const command = vscode.commands.registerCommand('autogen.openCrossProjectPanel', () => {
        CrossProjectPanelProvider.createOrShow(context, mcpClient);
    });

    context.subscriptions.push(command);
}

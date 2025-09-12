import * as vscode from 'vscode';
import { McpClient } from './mcpClient';

export interface AgentConfig {
    name: string;
    type: 'UserProxyAgent' | 'AssistantAgent' | 'ConversableAgent' | 'GroupChatManager';
    role: string;
    systemMessage: string;
    maxConsecutiveAutoReply: number;
    humanInputMode: 'ALWAYS' | 'NEVER' | 'TERMINATE';
    codeExecution: boolean;
    capabilities: string[];
    temperature: number;
    maxTokens: number;
    description: string;
}

export interface AgentTemplate {
    name: string;
    description: string;
    config: Partial<AgentConfig>;
}

export class AgentConfigurationPanel {
    private static currentPanel: AgentConfigurationPanel | undefined;
    private static readonly viewType = 'agentConfiguration';

    private readonly panel: vscode.WebviewPanel;
    private readonly context: vscode.ExtensionContext;
    private readonly mcpClient: McpClient;
    private disposables: vscode.Disposable[] = [];

    public static createOrShow(context: vscode.ExtensionContext, mcpClient: McpClient): void {
        const column = vscode.window.activeTextEditor
            ? vscode.window.activeTextEditor.viewColumn
            : undefined;

        // If we already have a panel, show it
        if (AgentConfigurationPanel.currentPanel) {
            AgentConfigurationPanel.currentPanel.panel.reveal(column);
            return;
        }

        // Otherwise, create a new panel
        const panel = vscode.window.createWebviewPanel(
            AgentConfigurationPanel.viewType,
            'Agent Configuration',
            column || vscode.ViewColumn.One,
            {
                enableScripts: true,
                retainContextWhenHidden: true,
                localResourceRoots: [
                    vscode.Uri.joinPath(context.extensionUri, 'resources')
                ]
            }
        );

        AgentConfigurationPanel.currentPanel = new AgentConfigurationPanel(panel, context, mcpClient);
    }

    private constructor(panel: vscode.WebviewPanel, context: vscode.ExtensionContext, mcpClient: McpClient) {
        this.panel = panel;
        this.context = context;
        this.mcpClient = mcpClient;

        // Set the webview's initial html content
        this.update();

        // Listen for when the panel is disposed
        this.panel.onDidDispose(() => this.dispose(), null, this.disposables);

        // Handle messages from the webview
        this.panel.webview.onDidReceiveMessage(
            async message => {
                switch (message.type) {
                    case 'saveAgent':
                        await this.handleSaveAgent(message.config);
                        break;
                    case 'loadTemplate':
                        await this.handleLoadTemplate(message.templateName);
                        break;
                    case 'validateConfig':
                        await this.handleValidateConfig(message.config);
                        break;
                    case 'exportConfig':
                        await this.handleExportConfig(message.config);
                        break;
                    case 'importConfig':
                        await this.handleImportConfig();
                        break;
                }
            },
            null,
            this.disposables
        );
    }

    private async update(): Promise<void> {
        this.panel.title = 'Agent Configuration';
        this.panel.webview.html = await this.getHtmlForWebview();
    }

    private async handleSaveAgent(config: AgentConfig): Promise<void> {
        try {
            // Validate configuration
            const validation = this.validateAgentConfig(config);
            if (!validation.isValid) {
                this.panel.webview.postMessage({
                    type: 'validationResult',
                    isValid: false,
                    errors: validation.errors
                });
                return;
            }

            // Save to workspace settings or local storage
            await this.saveAgentConfig(config);

            this.panel.webview.postMessage({
                type: 'saveResult',
                success: true,
                message: `Agent "${config.name}" saved successfully`
            });

            vscode.window.showInformationMessage(`Agent "${config.name}" configuration saved`);

        } catch (error) {
            const message = error instanceof Error ? error.message : 'Unknown error';
            this.panel.webview.postMessage({
                type: 'saveResult',
                success: false,
                message: `Failed to save agent: ${message}`
            });
        }
    }

    private async handleLoadTemplate(templateName: string): Promise<void> {
        const template = this.getAgentTemplate(templateName);
        if (template) {
            this.panel.webview.postMessage({
                type: 'templateLoaded',
                config: template.config
            });
        }
    }

    private async handleValidateConfig(config: Partial<AgentConfig>): Promise<void> {
        const validation = this.validateAgentConfig(config as AgentConfig);
        this.panel.webview.postMessage({
            type: 'validationResult',
            isValid: validation.isValid,
            errors: validation.errors,
            warnings: validation.warnings
        });
    }

    private async handleExportConfig(config: AgentConfig): Promise<void> {
        try {
            const configJson = JSON.stringify(config, null, 2);
            const document = await vscode.workspace.openTextDocument({
                content: configJson,
                language: 'json'
            });
            await vscode.window.showTextDocument(document);
            vscode.window.showInformationMessage('Agent configuration exported to new document');
        } catch (error) {
            vscode.window.showErrorMessage(`Export failed: ${error}`);
        }
    }

    private async handleImportConfig(): Promise<void> {
        try {
            const fileUri = await vscode.window.showOpenDialog({
                canSelectFiles: true,
                canSelectFolders: false,
                canSelectMany: false,
                filters: {
                    'JSON Files': ['json'],
                    'All Files': ['*']
                }
            });

            if (fileUri && fileUri[0]) {
                const content = await vscode.workspace.fs.readFile(fileUri[0]);
                const configJson = new TextDecoder().decode(content);
                const config = JSON.parse(configJson);

                this.panel.webview.postMessage({
                    type: 'configImported',
                    config: config
                });

                vscode.window.showInformationMessage('Agent configuration imported');
            }
        } catch (error) {
            vscode.window.showErrorMessage(`Import failed: ${error}`);
        }
    }

    private validateAgentConfig(config: AgentConfig): { isValid: boolean; errors: string[]; warnings: string[] } {
        const errors: string[] = [];
        const warnings: string[] = [];

        // Required fields
        if (!config.name || config.name.trim().length === 0) {
            errors.push('Agent name is required');
        }
        if (!config.type) {
            errors.push('Agent type is required');
        }
        if (!config.role || config.role.trim().length === 0) {
            errors.push('Agent role is required');
        }

        // Value validations
        if (config.name && config.name.length > 50) {
            errors.push('Agent name must be 50 characters or less');
        }
        if (config.maxConsecutiveAutoReply < 0 || config.maxConsecutiveAutoReply > 100) {
            errors.push('Max consecutive auto reply must be between 0 and 100');
        }
        if (config.temperature < 0 || config.temperature > 2) {
            errors.push('Temperature must be between 0 and 2');
        }
        if (config.maxTokens < 1 || config.maxTokens > 32000) {
            errors.push('Max tokens must be between 1 and 32000');
        }

        // Warnings
        if (config.temperature > 1.0) {
            warnings.push('High temperature values may produce unpredictable responses');
        }
        if (config.maxConsecutiveAutoReply > 10) {
            warnings.push('High auto-reply limits may lead to long conversations');
        }
        if (!config.systemMessage || config.systemMessage.trim().length === 0) {
            warnings.push('System message is recommended for better agent behavior');
        }

        return {
            isValid: errors.length === 0,
            errors,
            warnings
        };
    }

    private async saveAgentConfig(config: AgentConfig): Promise<void> {
        const configuration = vscode.workspace.getConfiguration('autogen');
        const existingAgents = configuration.get<AgentConfig[]>('agentConfigurations', []);

        // Replace existing agent with same name or add new one
        const index = existingAgents.findIndex(agent => agent.name === config.name);
        if (index >= 0) {
            existingAgents[index] = config;
        } else {
            existingAgents.push(config);
        }

        await configuration.update('agentConfigurations', existingAgents, vscode.ConfigurationTarget.Workspace);
    }

    private getAgentTemplate(templateName: string): AgentTemplate | undefined {
        const templates: AgentTemplate[] = [
            {
                name: 'Coder',
                description: 'A programming assistant that can write and review code',
                config: {
                    type: 'AssistantAgent',
                    role: 'Software Developer',
                    systemMessage: 'You are a skilled software developer. You write clean, efficient, and well-documented code. Always explain your approach and consider edge cases.',
                    maxConsecutiveAutoReply: 5,
                    humanInputMode: 'NEVER',
                    codeExecution: true,
                    capabilities: ['code_generation', 'code_review', 'debugging', 'testing'],
                    temperature: 0.3,
                    maxTokens: 2000,
                    description: 'Generates and reviews code with focus on quality and best practices'
                }
            },
            {
                name: 'Reviewer',
                description: 'A code reviewer that focuses on quality and best practices',
                config: {
                    type: 'AssistantAgent',
                    role: 'Code Reviewer',
                    systemMessage: 'You are an experienced code reviewer. Focus on code quality, security, performance, and maintainability. Provide constructive feedback.',
                    maxConsecutiveAutoReply: 3,
                    humanInputMode: 'NEVER',
                    codeExecution: false,
                    capabilities: ['code_review', 'security_analysis', 'performance_analysis'],
                    temperature: 0.2,
                    maxTokens: 1500,
                    description: 'Reviews code for quality, security, and best practices'
                }
            },
            {
                name: 'Tester',
                description: 'A testing specialist that creates and runs tests',
                config: {
                    type: 'AssistantAgent',
                    role: 'QA Engineer',
                    systemMessage: 'You are a quality assurance engineer. Create comprehensive test cases, write automated tests, and ensure software reliability.',
                    maxConsecutiveAutoReply: 4,
                    humanInputMode: 'NEVER',
                    codeExecution: true,
                    capabilities: ['test_generation', 'test_execution', 'bug_detection'],
                    temperature: 0.4,
                    maxTokens: 1800,
                    description: 'Creates and executes tests to ensure software quality'
                }
            },
            {
                name: 'User Proxy',
                description: 'A human proxy agent for interaction',
                config: {
                    type: 'UserProxyAgent',
                    role: 'User Representative',
                    systemMessage: 'You represent the user in conversations. Ask clarifying questions and provide human oversight.',
                    maxConsecutiveAutoReply: 0,
                    humanInputMode: 'ALWAYS',
                    codeExecution: true,
                    capabilities: ['human_input', 'oversight', 'decision_making'],
                    temperature: 0.0,
                    maxTokens: 1000,
                    description: 'Represents human user in multi-agent conversations'
                }
            }
        ];

        return templates.find(template => template.name === templateName);
    }

    private async getHtmlForWebview(): Promise<string> {
        const templates = ['Coder', 'Reviewer', 'Tester', 'User Proxy'];
        const templateOptions = templates.map(name => `<option value="${name}">${name}</option>`).join('');

        return `
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Agent Configuration</title>
                <style>
                    :root {
                        --container-padding: 24px;
                        --section-spacing: 24px;
                        --field-spacing: 16px;
                        --border-radius: 6px;
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
                        margin-bottom: var(--section-spacing);
                        padding-bottom: 16px;
                        border-bottom: 1px solid var(--vscode-panel-border);
                    }

                    .header-actions {
                        display: flex;
                        gap: 8px;
                    }

                    .form-container {
                        max-width: 800px;
                        margin: 0 auto;
                    }

                    .form-section {
                        margin-bottom: var(--section-spacing);
                        padding: 20px;
                        border: 1px solid var(--vscode-panel-border);
                        border-radius: var(--border-radius);
                        background: var(--vscode-editor-inactiveSelectionBackground);
                    }

                    .form-section h3 {
                        margin-top: 0;
                        margin-bottom: 16px;
                        color: var(--vscode-foreground);
                        font-size: 1.1em;
                    }

                    .form-row {
                        display: grid;
                        grid-template-columns: 1fr 1fr;
                        gap: 16px;
                        margin-bottom: var(--field-spacing);
                    }

                    .form-field {
                        display: flex;
                        flex-direction: column;
                        margin-bottom: var(--field-spacing);
                    }

                    .form-field.full-width {
                        grid-column: 1 / -1;
                    }

                    label {
                        font-weight: 500;
                        margin-bottom: 4px;
                        color: var(--vscode-foreground);
                    }

                    input, select, textarea {
                        padding: 8px 12px;
                        border: 1px solid var(--vscode-input-border);
                        border-radius: var(--border-radius);
                        background: var(--vscode-input-background);
                        color: var(--vscode-input-foreground);
                        font-family: inherit;
                        font-size: 13px;
                    }

                    input:focus, select:focus, textarea:focus {
                        outline: 1px solid var(--vscode-focusBorder);
                        outline-offset: -1px;
                    }

                    textarea {
                        resize: vertical;
                        min-height: 80px;
                        font-family: var(--vscode-editor-font-family);
                    }

                    .checkbox-container {
                        display: flex;
                        align-items: center;
                        gap: 8px;
                        margin-bottom: var(--field-spacing);
                    }

                    .checkbox-container input[type="checkbox"] {
                        width: auto;
                        margin: 0;
                    }

                    .capabilities-container {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                        gap: 8px;
                        margin-top: 8px;
                    }

                    .capability-item {
                        display: flex;
                        align-items: center;
                        gap: 8px;
                        padding: 4px 0;
                    }

                    .template-section {
                        display: grid;
                        grid-template-columns: 1fr auto;
                        gap: 12px;
                        align-items: end;
                        margin-bottom: var(--section-spacing);
                    }

                    button {
                        padding: 8px 16px;
                        border: 1px solid var(--vscode-button-border);
                        border-radius: var(--border-radius);
                        background: var(--vscode-button-background);
                        color: var(--vscode-button-foreground);
                        cursor: pointer;
                        font-family: inherit;
                        font-size: 13px;
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

                    .button-primary {
                        background: var(--vscode-button-background);
                        color: var(--vscode-button-foreground);
                        font-weight: 500;
                    }

                    .validation-feedback {
                        margin-top: 16px;
                        padding: 12px;
                        border-radius: var(--border-radius);
                        display: none;
                    }

                    .validation-feedback.error {
                        background: var(--vscode-inputValidation-errorBackground);
                        border: 1px solid var(--vscode-inputValidation-errorBorder);
                        color: var(--vscode-errorForeground);
                    }

                    .validation-feedback.warning {
                        background: var(--vscode-inputValidation-warningBackground);
                        border: 1px solid var(--vscode-inputValidation-warningBorder);
                        color: var(--vscode-warningForeground);
                    }

                    .validation-feedback.success {
                        background: var(--vscode-inputValidation-infoBackground);
                        border: 1px solid var(--vscode-inputValidation-infoBorder);
                        color: var(--vscode-infoForeground);
                    }

                    .validation-list {
                        margin: 8px 0 0 0;
                        padding-left: 20px;
                    }

                    .form-actions {
                        display: flex;
                        gap: 12px;
                        justify-content: flex-end;
                        margin-top: var(--section-spacing);
                        padding-top: 16px;
                        border-top: 1px solid var(--vscode-panel-border);
                    }

                    .help-text {
                        font-size: 12px;
                        color: var(--vscode-descriptionForeground);
                        margin-top: 4px;
                    }

                    .range-container {
                        display: flex;
                        align-items: center;
                        gap: 12px;
                    }

                    .range-container input[type="range"] {
                        flex: 1;
                    }

                    .range-value {
                        font-family: var(--vscode-editor-font-family);
                        font-size: 12px;
                        color: var(--vscode-descriptionForeground);
                        min-width: 40px;
                        text-align: center;
                    }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🤖 Agent Configuration</h1>
                    <div class="header-actions">
                        <button onclick="importConfig()" class="button-secondary">Import</button>
                        <button onclick="exportConfig()" class="button-secondary">Export</button>
                    </div>
                </div>

                <div class="form-container">
                    <div class="template-section">
                        <div class="form-field">
                            <label for="templateSelect">Load from Template</label>
                            <select id="templateSelect">
                                <option value="">Select a template...</option>
                                ${templateOptions}
                            </select>
                        </div>
                        <button onclick="loadTemplate()" class="button-secondary">Load Template</button>
                    </div>

                    <form id="agentForm">
                        <div class="form-section">
                            <h3>Basic Information</h3>
                            <div class="form-row">
                                <div class="form-field">
                                    <label for="name">Agent Name *</label>
                                    <input type="text" id="name" required maxlength="50" placeholder="e.g., Senior Developer">
                                    <div class="help-text">Unique identifier for this agent</div>
                                </div>
                                <div class="form-field">
                                    <label for="type">Agent Type *</label>
                                    <select id="type" required>
                                        <option value="">Select type...</option>
                                        <option value="UserProxyAgent">User Proxy Agent</option>
                                        <option value="AssistantAgent">Assistant Agent</option>
                                        <option value="ConversableAgent">Conversable Agent</option>
                                        <option value="GroupChatManager">Group Chat Manager</option>
                                    </select>
                                </div>
                            </div>
                            <div class="form-field">
                                <label for="role">Role *</label>
                                <input type="text" id="role" required placeholder="e.g., Software Developer">
                                <div class="help-text">The agent's role in the conversation</div>
                            </div>
                            <div class="form-field">
                                <label for="description">Description</label>
                                <textarea id="description" placeholder="Brief description of the agent's purpose and capabilities"></textarea>
                            </div>
                        </div>

                        <div class="form-section">
                            <h3>Behavior Configuration</h3>
                            <div class="form-field">
                                <label for="systemMessage">System Message</label>
                                <textarea id="systemMessage" rows="4" placeholder="Instructions that define the agent's behavior and personality"></textarea>
                                <div class="help-text">This message guides the agent's responses and behavior</div>
                            </div>
                            <div class="form-row">
                                <div class="form-field">
                                    <label for="humanInputMode">Human Input Mode</label>
                                    <select id="humanInputMode">
                                        <option value="NEVER">Never</option>
                                        <option value="TERMINATE">On Termination</option>
                                        <option value="ALWAYS">Always</option>
                                    </select>
                                    <div class="help-text">When to request human input</div>
                                </div>
                                <div class="form-field">
                                    <label for="maxConsecutiveAutoReply">Max Auto Replies</label>
                                    <input type="number" id="maxConsecutiveAutoReply" min="0" max="100" value="5">
                                    <div class="help-text">Maximum consecutive automatic replies</div>
                                </div>
                            </div>
                            <div class="checkbox-container">
                                <input type="checkbox" id="codeExecution">
                                <label for="codeExecution">Enable Code Execution</label>
                            </div>
                        </div>

                        <div class="form-section">
                            <h3>AI Model Settings</h3>
                            <div class="form-row">
                                <div class="form-field">
                                    <label for="temperature">Temperature</label>
                                    <div class="range-container">
                                        <input type="range" id="temperature" min="0" max="2" step="0.1" value="0.7"
                                               oninput="updateRangeValue('temperature', this.value)">
                                        <span class="range-value" id="temperatureValue">0.7</span>
                                    </div>
                                    <div class="help-text">Controls response creativity (0=focused, 2=creative)</div>
                                </div>
                                <div class="form-field">
                                    <label for="maxTokens">Max Tokens</label>
                                    <input type="number" id="maxTokens" min="1" max="32000" value="2000">
                                    <div class="help-text">Maximum tokens per response</div>
                                </div>
                            </div>
                        </div>

                        <div class="form-section">
                            <h3>Capabilities</h3>
                            <div class="capabilities-container">
                                <div class="capability-item">
                                    <input type="checkbox" id="cap_code_generation" value="code_generation">
                                    <label for="cap_code_generation">Code Generation</label>
                                </div>
                                <div class="capability-item">
                                    <input type="checkbox" id="cap_code_review" value="code_review">
                                    <label for="cap_code_review">Code Review</label>
                                </div>
                                <div class="capability-item">
                                    <input type="checkbox" id="cap_debugging" value="debugging">
                                    <label for="cap_debugging">Debugging</label>
                                </div>
                                <div class="capability-item">
                                    <input type="checkbox" id="cap_testing" value="testing">
                                    <label for="cap_testing">Testing</label>
                                </div>
                                <div class="capability-item">
                                    <input type="checkbox" id="cap_documentation" value="documentation">
                                    <label for="cap_documentation">Documentation</label>
                                </div>
                                <div class="capability-item">
                                    <input type="checkbox" id="cap_architecture" value="architecture">
                                    <label for="cap_architecture">Architecture</label>
                                </div>
                                <div class="capability-item">
                                    <input type="checkbox" id="cap_security" value="security_analysis">
                                    <label for="cap_security">Security Analysis</label>
                                </div>
                                <div class="capability-item">
                                    <input type="checkbox" id="cap_performance" value="performance_analysis">
                                    <label for="cap_performance">Performance Analysis</label>
                                </div>
                            </div>
                        </div>

                        <div class="validation-feedback" id="validationFeedback"></div>

                        <div class="form-actions">
                            <button type="button" onclick="validateConfig()" class="button-secondary">Validate</button>
                            <button type="button" onclick="resetForm()" class="button-secondary">Reset</button>
                            <button type="submit" class="button-primary">Save Agent</button>
                        </div>
                    </form>
                </div>

                <script>
                    const vscode = acquireVsCodeApi();

                    // Handle messages from the extension
                    window.addEventListener('message', event => {
                        const message = event.data;
                        switch (message.type) {
                            case 'templateLoaded':
                                loadConfigIntoForm(message.config);
                                showFeedback('Template loaded successfully', 'success');
                                break;
                            case 'validationResult':
                                showValidationResult(message);
                                break;
                            case 'saveResult':
                                showFeedback(message.message, message.success ? 'success' : 'error');
                                break;
                            case 'configImported':
                                loadConfigIntoForm(message.config);
                                showFeedback('Configuration imported successfully', 'success');
                                break;
                        }
                    });

                    // Form handling
                    document.getElementById('agentForm').addEventListener('submit', (e) => {
                        e.preventDefault();
                        saveAgent();
                    });

                    function loadTemplate() {
                        const templateSelect = document.getElementById('templateSelect');
                        const templateName = templateSelect.value;
                        if (templateName) {
                            vscode.postMessage({
                                type: 'loadTemplate',
                                templateName: templateName
                            });
                        }
                    }

                    function validateConfig() {
                        const config = getFormData();
                        vscode.postMessage({
                            type: 'validateConfig',
                            config: config
                        });
                    }

                    function saveAgent() {
                        const config = getFormData();
                        vscode.postMessage({
                            type: 'saveAgent',
                            config: config
                        });
                    }

                    function exportConfig() {
                        const config = getFormData();
                        vscode.postMessage({
                            type: 'exportConfig',
                            config: config
                        });
                    }

                    function importConfig() {
                        vscode.postMessage({
                            type: 'importConfig'
                        });
                    }

                    function resetForm() {
                        document.getElementById('agentForm').reset();
                        document.getElementById('temperatureValue').textContent = '0.7';
                        hideFeedback();
                    }

                    function getFormData() {
                        const capabilities = Array.from(document.querySelectorAll('input[id^="cap_"]:checked'))
                            .map(cb => cb.value);

                        return {
                            name: document.getElementById('name').value,
                            type: document.getElementById('type').value,
                            role: document.getElementById('role').value,
                            description: document.getElementById('description').value,
                            systemMessage: document.getElementById('systemMessage').value,
                            maxConsecutiveAutoReply: parseInt(document.getElementById('maxConsecutiveAutoReply').value) || 0,
                            humanInputMode: document.getElementById('humanInputMode').value,
                            codeExecution: document.getElementById('codeExecution').checked,
                            temperature: parseFloat(document.getElementById('temperature').value) || 0.7,
                            maxTokens: parseInt(document.getElementById('maxTokens').value) || 2000,
                            capabilities: capabilities
                        };
                    }

                    function loadConfigIntoForm(config) {
                        if (config.name) document.getElementById('name').value = config.name;
                        if (config.type) document.getElementById('type').value = config.type;
                        if (config.role) document.getElementById('role').value = config.role;
                        if (config.description) document.getElementById('description').value = config.description;
                        if (config.systemMessage) document.getElementById('systemMessage').value = config.systemMessage;
                        if (config.maxConsecutiveAutoReply !== undefined) {
                            document.getElementById('maxConsecutiveAutoReply').value = config.maxConsecutiveAutoReply;
                        }
                        if (config.humanInputMode) document.getElementById('humanInputMode').value = config.humanInputMode;
                        if (config.codeExecution !== undefined) document.getElementById('codeExecution').checked = config.codeExecution;
                        if (config.temperature !== undefined) {
                            document.getElementById('temperature').value = config.temperature;
                            document.getElementById('temperatureValue').textContent = config.temperature;
                        }
                        if (config.maxTokens) document.getElementById('maxTokens').value = config.maxTokens;

                        // Clear all capability checkboxes first
                        document.querySelectorAll('input[id^="cap_"]').forEach(cb => cb.checked = false);

                        // Set capabilities
                        if (config.capabilities) {
                            config.capabilities.forEach(capability => {
                                const checkbox = document.querySelector(\`input[value="\${capability}"]\`);
                                if (checkbox) checkbox.checked = true;
                            });
                        }
                    }

                    function updateRangeValue(id, value) {
                        document.getElementById(id + 'Value').textContent = value;
                    }

                    function showValidationResult(result) {
                        const feedback = document.getElementById('validationFeedback');

                        if (result.isValid) {
                            showFeedback('Configuration is valid!', 'success');
                            if (result.warnings && result.warnings.length > 0) {
                                showFeedback('Valid with warnings:\\n' + result.warnings.join('\\n'), 'warning');
                            }
                        } else {
                            let message = 'Validation failed:\\n' + result.errors.join('\\n');
                            if (result.warnings && result.warnings.length > 0) {
                                message += '\\n\\nWarnings:\\n' + result.warnings.join('\\n');
                            }
                            showFeedback(message, 'error');
                        }
                    }

                    function showFeedback(message, type) {
                        const feedback = document.getElementById('validationFeedback');
                        feedback.className = \`validation-feedback \${type}\`;
                        feedback.innerHTML = message.replace(/\\n/g, '<br>');
                        feedback.style.display = 'block';

                        // Auto-hide success messages
                        if (type === 'success') {
                            setTimeout(() => hideFeedback(), 3000);
                        }
                    }

                    function hideFeedback() {
                        const feedback = document.getElementById('validationFeedback');
                        feedback.style.display = 'none';
                    }
                </script>
            </body>
            </html>
        `;
    }

    public dispose(): void {
        AgentConfigurationPanel.currentPanel = undefined;

        // Clean up our resources
        this.panel.dispose();

        while (this.disposables.length) {
            const x = this.disposables.pop();
            if (x) {
                x.dispose();
            }
        }
    }
}

// Register command to open agent configuration panel
export function registerAgentConfigurationCommand(context: vscode.ExtensionContext, mcpClient: McpClient): void {
    const command = vscode.commands.registerCommand('autogen.configureAgent', () => {
        AgentConfigurationPanel.createOrShow(context, mcpClient);
    });

    context.subscriptions.push(command);
}

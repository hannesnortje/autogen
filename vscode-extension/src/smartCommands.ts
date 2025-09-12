import * as vscode from 'vscode';
import { McpClient } from './mcpClient';
import { SessionTreeProvider } from './sessionTreeProvider';

export interface CommandWithContext {
    command: string;
    title: string;
    description?: string;
    category: string;
    when?: string;
    args?: any[];
}

export interface SmartCommandOptions {
    showInPalette: boolean;
    requiresServer: boolean;
    requiresSession: boolean;
    promptForParams: boolean;
    paramSchema?: ParameterSchema[];
}

export interface ParameterSchema {
    name: string;
    type: 'string' | 'number' | 'boolean' | 'choice' | 'multiChoice';
    label: string;
    description?: string;
    required?: boolean;
    defaultValue?: any;
    choices?: { label: string; value: any; description?: string }[];
    validation?: (value: any) => string | null;
}

export class SmartCommandPalette {
    private smartCommands: Map<string, SmartCommandOptions> = new Map();

    constructor(
        private context: vscode.ExtensionContext,
        private mcpClient: McpClient,
        private sessionTreeProvider: SessionTreeProvider
    ) {
        this.registerSmartCommands();
    }

    private registerSmartCommands(): void {
        // Define smart command configurations
        const smartCommandConfigs: [string, SmartCommandOptions][] = [
            ['autogen.startSessionWithParams', {
                showInPalette: true,
                requiresServer: true,
                requiresSession: false,
                promptForParams: true,
                paramSchema: [
                    {
                        name: 'projectName',
                        type: 'string',
                        label: 'Project Name',
                        description: 'Name of the project for this session',
                        required: true,
                        defaultValue: this.getWorkspaceName()
                    },
                    {
                        name: 'agents',
                        type: 'multiChoice',
                        label: 'Agents',
                        description: 'Select agents for the session',
                        required: true,
                        choices: [
                            { label: 'Coder', value: 'Coder', description: 'Generates and writes code' },
                            { label: 'Reviewer', value: 'Reviewer', description: 'Reviews code for quality' },
                            { label: 'Tester', value: 'Tester', description: 'Creates and runs tests' },
                            { label: 'Architect', value: 'Architect', description: 'Designs system architecture' },
                            { label: 'DevOps', value: 'DevOps', description: 'Handles deployment and infrastructure' },
                            { label: 'Security', value: 'Security', description: 'Focuses on security analysis' },
                            { label: 'Documentation', value: 'Documentation', description: 'Writes documentation' }
                        ]
                    },
                    {
                        name: 'objective',
                        type: 'string',
                        label: 'Session Objective',
                        description: 'What do you want to accomplish in this session?',
                        required: true,
                        validation: (value: string) => {
                            if (!value || value.trim().length < 10) {
                                return 'Objective must be at least 10 characters long';
                            }
                            return null;
                        }
                    }
                ]
            }],
            ['autogen.searchMemoryAdvanced', {
                showInPalette: true,
                requiresServer: true,
                requiresSession: false,
                promptForParams: true,
                paramSchema: [
                    {
                        name: 'query',
                        type: 'string',
                        label: 'Search Query',
                        description: 'What are you looking for?',
                        required: true,
                        validation: (value: string) => {
                            if (!value || value.trim().length < 3) {
                                return 'Query must be at least 3 characters long';
                            }
                            return null;
                        }
                    },
                    {
                        name: 'scope',
                        type: 'choice',
                        label: 'Search Scope',
                        description: 'Where to search',
                        required: true,
                        defaultValue: 'project',
                        choices: [
                            { label: 'Project', value: 'project', description: 'Search in current project' },
                            { label: 'Session', value: 'session', description: 'Search in current session' },
                            { label: 'Global', value: 'global', description: 'Search everywhere' }
                        ]
                    },
                    {
                        name: 'limit',
                        type: 'number',
                        label: 'Result Limit',
                        description: 'Maximum number of results to return',
                        required: false,
                        defaultValue: 10
                    }
                ]
            }],
            ['autogen.addObjectiveAdvanced', {
                showInPalette: true,
                requiresServer: true,
                requiresSession: false,
                promptForParams: true,
                paramSchema: [
                    {
                        name: 'objective',
                        type: 'string',
                        label: 'Objective',
                        description: 'Describe the objective or task',
                        required: true,
                        validation: (value: string) => {
                            if (!value || value.trim().length < 5) {
                                return 'Objective must be at least 5 characters long';
                            }
                            return null;
                        }
                    },
                    {
                        name: 'priority',
                        type: 'choice',
                        label: 'Priority',
                        description: 'How important is this objective?',
                        required: true,
                        defaultValue: 'medium',
                        choices: [
                            { label: 'High', value: 'high', description: 'Critical priority' },
                            { label: 'Medium', value: 'medium', description: 'Normal priority' },
                            { label: 'Low', value: 'low', description: 'Low priority' }
                        ]
                    },
                    {
                        name: 'category',
                        type: 'choice',
                        label: 'Category',
                        description: 'What type of objective is this?',
                        required: false,
                        choices: [
                            { label: 'Feature', value: 'feature', description: 'New feature development' },
                            { label: 'Bug Fix', value: 'bugfix', description: 'Fix existing issues' },
                            { label: 'Refactoring', value: 'refactor', description: 'Code improvement' },
                            { label: 'Testing', value: 'testing', description: 'Add or improve tests' },
                            { label: 'Documentation', value: 'docs', description: 'Documentation updates' },
                            { label: 'Other', value: 'other', description: 'Other tasks' }
                        ]
                    }
                ]
            }],
            ['autogen.stopSessionAdvanced', {
                showInPalette: true,
                requiresServer: true,
                requiresSession: true,
                promptForParams: true,
                paramSchema: [
                    {
                        name: 'saveResults',
                        type: 'boolean',
                        label: 'Save Session Results',
                        description: 'Save conversation and results before stopping?',
                        required: false,
                        defaultValue: true
                    },
                    {
                        name: 'exportMemory',
                        type: 'boolean',
                        label: 'Export Memory',
                        description: 'Export session memory to a file?',
                        required: false,
                        defaultValue: false
                    }
                ]
            }]
        ];

        // Register smart commands
        smartCommandConfigs.forEach(([command, options]) => {
            this.smartCommands.set(command, options);
            this.registerSmartCommand(command, options);
        });
    }

    private registerSmartCommand(command: string, options: SmartCommandOptions): void {
        const commandHandler = vscode.commands.registerCommand(command, async (...args: any[]) => {
            try {
                // Check prerequisites
                if (options.requiresServer) {
                    const isConnected = await this.mcpClient.isServerAvailable();
                    if (!isConnected) {
                        vscode.window.showErrorMessage('AutoGen MCP server is not available. Please check your configuration.');
                        return;
                    }
                }

                if (options.requiresSession) {
                    const sessionId = this.mcpClient.getCurrentSessionId();
                    if (!sessionId) {
                        const shouldStart = await vscode.window.showQuickPick(['Yes', 'No'], {
                            placeHolder: 'No active session found. Start a new session first?'
                        });
                        if (shouldStart === 'Yes') {
                            await vscode.commands.executeCommand('autogen.startSession');
                        }
                        return;
                    }
                }

                // Collect parameters if needed
                let params: any = {};
                if (options.promptForParams && options.paramSchema) {
                    params = await this.collectParameters(options.paramSchema);
                    if (!params) {
                        return; // User cancelled
                    }
                }

                // Execute the command with collected parameters
                await this.executeSmartCommand(command, params, args);

            } catch (error) {
                vscode.window.showErrorMessage(`Command failed: ${error}`);
                console.error(`Smart command ${command} failed:`, error);
            }
        });

        this.context.subscriptions.push(commandHandler);
    }

    private async collectParameters(schema: ParameterSchema[]): Promise<any | null> {
        const params: any = {};

        for (const param of schema) {
            const value = await this.promptForParameter(param);
            if (value === undefined) {
                return null; // User cancelled
            }
            params[param.name] = value;
        }

        return params;
    }

    private async promptForParameter(param: ParameterSchema): Promise<any> {
        const prompt = param.description ? `${param.label}: ${param.description}` : param.label;

        switch (param.type) {
            case 'string':
                const stringValue = await vscode.window.showInputBox({
                    prompt,
                    value: param.defaultValue,
                    validateInput: param.validation ? (value) => param.validation!(value) : undefined
                });
                return stringValue?.trim() || (param.required ? undefined : param.defaultValue);

            case 'number':
                const numberInput = await vscode.window.showInputBox({
                    prompt,
                    value: param.defaultValue?.toString(),
                    validateInput: (value) => {
                        const num = parseFloat(value);
                        if (isNaN(num)) {
                            return 'Must be a valid number';
                        }
                        return param.validation ? param.validation(num) : null;
                    }
                });
                return numberInput !== undefined ? parseFloat(numberInput) :
                       (param.required ? undefined : param.defaultValue);

            case 'boolean':
                const boolChoice = await vscode.window.showQuickPick(['Yes', 'No'], {
                    placeHolder: prompt
                });
                return boolChoice === 'Yes';

            case 'choice':
                if (!param.choices) return param.defaultValue;
                const choiceItems = param.choices.map(choice => ({
                    label: choice.label,
                    description: choice.description,
                    value: choice.value
                }));
                const selected = await vscode.window.showQuickPick(choiceItems, {
                    placeHolder: prompt
                });
                return selected?.value || (param.required ? undefined : param.defaultValue);

            case 'multiChoice':
                if (!param.choices) return [];
                const multiChoiceItems = param.choices.map(choice => ({
                    label: choice.label,
                    description: choice.description,
                    value: choice.value
                }));
                const multiSelected = await vscode.window.showQuickPick(multiChoiceItems, {
                    placeHolder: prompt,
                    canPickMany: true
                });
                return multiSelected?.map(item => item.value) ||
                       (param.required ? undefined : param.defaultValue || []);

            default:
                return param.defaultValue;
        }
    }

    private async executeSmartCommand(command: string, params: any, originalArgs: any[]): Promise<void> {
        switch (command) {
            case 'autogen.startSessionWithParams':
                await this.executeStartSessionWithParams(params);
                break;

            case 'autogen.searchMemoryAdvanced':
                await this.executeSearchMemoryAdvanced(params);
                break;

            case 'autogen.addObjectiveAdvanced':
                await this.executeAddObjectiveAdvanced(params);
                break;

            case 'autogen.stopSessionAdvanced':
                await this.executeStopSessionAdvanced(params);
                break;

            default:
                vscode.window.showWarningMessage(`Smart command ${command} not implemented`);
        }
    }

    private async executeStartSessionWithParams(params: any): Promise<void> {
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Starting AutoGen session...",
            cancellable: false
        }, async (progress) => {
            progress.report({ increment: 0, message: "Initializing..." });

            const response = await this.mcpClient.startOrchestration({
                project: params.projectName,
                agents: params.agents,
                objective: params.objective
            });

            progress.report({ increment: 100, message: "Session started!" });

            vscode.window.showInformationMessage(
                `AutoGen session started successfully! Session ID: ${response.session_id.substring(0, 8)}...`
            );

            this.sessionTreeProvider.refresh();
        });
    }

    private async executeSearchMemoryAdvanced(params: any): Promise<void> {
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Searching memory...",
            cancellable: false
        }, async (progress) => {
            progress.report({ increment: 0, message: "Searching..." });

            const results = await this.mcpClient.searchMemory({
                query: params.query,
                scope: params.scope,
                k: params.limit || 10
            });

            progress.report({ increment: 100, message: "Search complete!" });

            // Format results
            let content = `# Advanced Memory Search Results\n\n`;
            content += `**Query:** ${params.query}\n`;
            content += `**Scope:** ${params.scope}\n`;
            content += `**Limit:** ${params.limit || 10}\n`;
            content += `**Results:** ${results.results.length} found\n\n`;

            if (results.results.length === 0) {
                content += '*No results found.*\n';
            } else {
                results.results.forEach((result, index) => {
                    content += `## Result ${index + 1} (Score: ${result.score.toFixed(3)})\n\n`;
                    content += `${result.content}\n\n`;
                    if (result.metadata && Object.keys(result.metadata).length > 0) {
                        content += `**Metadata:**\n\`\`\`json\n${JSON.stringify(result.metadata, null, 2)}\n\`\`\`\n\n`;
                    }
                    content += '---\n\n';
                });
            }

            const doc = await vscode.workspace.openTextDocument({
                content: content,
                language: 'markdown'
            });

            await vscode.window.showTextDocument(doc);
        });
    }

    private async executeAddObjectiveAdvanced(params: any): Promise<void> {
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Adding objective...",
            cancellable: false
        }, async (progress) => {
            progress.report({ increment: 0, message: "Saving objective..." });

            // Enhance objective with metadata
            const enhancedObjective = `[${params.priority?.toUpperCase() || 'MEDIUM'}]${params.category ? ` [${params.category.toUpperCase()}]` : ''} ${params.objective}`;

            await this.mcpClient.addObjective({
                objective: enhancedObjective,
                project: this.getWorkspaceName()
            });

            progress.report({ increment: 100, message: "Objective added!" });

            const priorityIcon = params.priority === 'high' ? '🔥' : params.priority === 'low' ? '📝' : '⭐';
            vscode.window.showInformationMessage(
                `${priorityIcon} Objective added with ${params.priority || 'medium'} priority`
            );
        });
    }

    private async executeStopSessionAdvanced(params: any): Promise<void> {
        const sessionId = this.mcpClient.getCurrentSessionId();
        if (!sessionId) {
            vscode.window.showWarningMessage('No active session to stop');
            return;
        }

        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Stopping AutoGen session...",
            cancellable: false
        }, async (progress) => {
            progress.report({ increment: 0, message: "Stopping session..." });

            if (params.exportMemory) {
                progress.report({ increment: 25, message: "Exporting memory..." });
                // Export memory before stopping
                try {
                    await vscode.commands.executeCommand('autogen.openMemoryExplorer');
                    // Give user time to export if they want
                    await new Promise(resolve => setTimeout(resolve, 1000));
                } catch (error) {
                    console.warn('Failed to open memory explorer:', error);
                }
            }

            progress.report({ increment: 50, message: "Stopping session..." });
            const response = await this.mcpClient.stopSession();

            progress.report({ increment: 100, message: "Session stopped!" });

            if (params.saveResults) {
                vscode.window.showInformationMessage(
                    `Session stopped and results saved: ${response.message}`
                );
            } else {
                vscode.window.showInformationMessage(`Session stopped: ${response.message}`);
            }

            this.sessionTreeProvider.refresh();
        });
    }

    private getWorkspaceName(): string {
        return vscode.workspace.name ||
               vscode.workspace.workspaceFolders?.[0]?.name ||
               'default-project';
    }

    public getSmartCommands(): Map<string, SmartCommandOptions> {
        return new Map(this.smartCommands);
    }
}

// Register all smart commands
export function registerSmartCommands(
    context: vscode.ExtensionContext,
    mcpClient: McpClient,
    sessionTreeProvider: SessionTreeProvider
): SmartCommandPalette {
    return new SmartCommandPalette(context, mcpClient, sessionTreeProvider);
}

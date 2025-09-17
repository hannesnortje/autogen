import * as vscode from 'vscode';
import { WorkspaceManager, ProjectInfo } from './workspaceManager';
import { FileWatcher, FileWatchConfig } from './fileWatcher';
import { FileOperations, FileOperationsConfig } from './fileOperations';
import { GitIntegration, GitConfig } from './gitIntegration';
// import { RealtimeClient } from '../realtime';

/**
 * Combined workspace configuration
 */
export interface WorkspaceConfig {
    autoInitialize: boolean;
    fileWatching: FileWatchConfig;
    fileOperations: FileOperationsConfig;
    gitIntegration: GitConfig;
    mcpServer: {
        endpoint: string;
        websocket: boolean;
        autoConnect: boolean;
    };
    agents: {
        enabled: boolean;
        memoryCollection: string;
        defaultAgentId: string;
    };
}

/**
 * Project-specific configuration templates
 */
export interface ProjectTemplate {
    type: ProjectInfo['type'];
    config: Partial<WorkspaceConfig>;
    requiredFiles?: string[];
    suggestedStructure?: string[];
}

/**
 * Manages workspace configuration and auto-setup
 */
export class WorkspaceConfiguration {
    private workspaceManager: WorkspaceManager;
    private fileWatcher: FileWatcher;
    private fileOperations: FileOperations;
    private gitIntegration: GitIntegration;
    // private realtimeClient: RealtimeClient;
    private configurations = new Map<string, WorkspaceConfig>();

    constructor(
        workspaceManager: WorkspaceManager,
        fileWatcher: FileWatcher,
        fileOperations: FileOperations,
        gitIntegration: GitIntegration,
        // realtimeClient: RealtimeClient
    ) {
        this.workspaceManager = workspaceManager;
        this.fileWatcher = fileWatcher;
        this.fileOperations = fileOperations;
        this.gitIntegration = gitIntegration;
        // this.realtimeClient = realtimeClient;

        this.initializeWorkspaces();
    }

    /**
     * Initialize all workspaces
     */
    private async initializeWorkspaces() {
        const projects = this.workspaceManager.getAllProjects();

        for (const [workspacePath, projectInfo] of projects) {
            await this.configureWorkspace(workspacePath, projectInfo);
        }
    }

    /**
     * Configure a specific workspace
     */
    async configureWorkspace(workspacePath: string, projectInfo: ProjectInfo): Promise<void> {
        // Get or create configuration
        let config = await this.loadWorkspaceConfig(workspacePath);
        if (!config) {
            config = this.createConfigFromTemplate(projectInfo);
            await this.saveWorkspaceConfig(workspacePath, config);
        }

        // Apply configuration to services
        await this.applyConfiguration(workspacePath, config, projectInfo);

        // Store in memory
        this.configurations.set(workspacePath, config);

        vscode.window.showInformationMessage(
            `AutoGen MCP: Configured workspace - ${projectInfo.type} project`
        );
    }

    /**
     * Create configuration from project template
     */
    private createConfigFromTemplate(projectInfo: ProjectInfo): WorkspaceConfig {
        const baseConfig = this.getDefaultConfig();
        const template = this.getProjectTemplate(projectInfo.type);

        // Apply project-specific overrides based on project type
        const projectSpecificConfig = this.getProjectSpecificConfig(projectInfo.type);

        // Deep merge template config with base config
        const mergedConfig: WorkspaceConfig = {
            ...baseConfig,
            ...template.config,
            fileWatching: {
                ...baseConfig.fileWatching,
                ...(template.config.fileWatching || {}),
                ...(projectSpecificConfig.fileWatching || {})
            },
            fileOperations: {
                ...baseConfig.fileOperations,
                ...(template.config.fileOperations || {}),
                ...(projectSpecificConfig.fileOperations || {})
            },
            gitIntegration: {
                ...baseConfig.gitIntegration,
                ...(template.config.gitIntegration || {})
            },
            mcpServer: {
                ...baseConfig.mcpServer,
                ...(template.config.mcpServer || {})
            },
            agents: {
                ...baseConfig.agents,
                ...(template.config.agents || {}),
                memoryCollection: this.sanitizeCollectionName(projectInfo.rootPath)
            }
        };

        return mergedConfig;
    }

    /**
     * Get project-specific configuration overrides
     */
    private getProjectSpecificConfig(projectType: ProjectInfo['type']): {
        fileWatching?: Partial<FileWatchConfig>;
        fileOperations?: Partial<FileOperationsConfig>;
    } {
        switch (projectType) {
            case 'python':
                return {
                    fileWatching: {
                        watchedExtensions: ['.py', '.md', '.txt', '.yaml', '.yml', '.json'],
                        ignorePatterns: [
                            '**/__pycache__/**',
                            '**/venv/**',
                            '**/env/**',
                            '**/.pytest_cache/**'
                        ],
                        batchDelay: 1500
                    },
                    fileOperations: {
                        allowedExtensions: ['.py', '.md', '.txt', '.yaml', '.yml', '.json'],
                        restrictedPaths: ['__pycache__', 'venv', 'env', '.pytest_cache']
                    }
                };
            case 'typescript':
                return {
                    fileWatching: {
                        watchedExtensions: ['.ts', '.js', '.json', '.md', '.yaml', '.yml'],
                        ignorePatterns: [
                            '**/node_modules/**',
                            '**/dist/**',
                            '**/build/**'
                        ],
                        batchDelay: 1000
                    },
                    fileOperations: {
                        allowedExtensions: ['.ts', '.js', '.json', '.md', '.yaml', '.yml', '.html', '.css'],
                        restrictedPaths: ['node_modules', 'dist', 'build']
                    }
                };
            case 'javascript':
                return {
                    fileWatching: {
                        watchedExtensions: ['.js', '.json', '.md', '.yaml', '.yml'],
                        ignorePatterns: [
                            '**/node_modules/**',
                            '**/dist/**',
                            '**/build/**'
                        ],
                        batchDelay: 800
                    },
                    fileOperations: {
                        allowedExtensions: ['.js', '.json', '.md', '.yaml', '.yml', '.html', '.css'],
                        restrictedPaths: ['node_modules', 'dist', 'build']
                    }
                };
            case 'mixed':
                return {
                    fileWatching: {
                        watchedExtensions: ['.py', '.ts', '.js', '.json', '.md', '.yaml', '.yml'],
                        ignorePatterns: [
                            '**/node_modules/**',
                            '**/__pycache__/**',
                            '**/dist/**',
                            '**/build/**',
                            '**/venv/**'
                        ],
                        batchDelay: 2000
                    },
                    fileOperations: {
                        allowedExtensions: ['.py', '.ts', '.js', '.json', '.md', '.yaml', '.yml', '.html', '.css'],
                        restrictedPaths: ['node_modules', '__pycache__', 'dist', 'build', 'venv']
                    }
                };
            default:
                return {};
        }
    }

    /**
     * Get project template based on type
     */
    private getProjectTemplate(projectType: ProjectInfo['type']): ProjectTemplate {
        const templates: Record<ProjectInfo['type'], ProjectTemplate> = {
            python: {
                type: 'python',
                config: {
                    // Only specify the fields we want to override
                },
                requiredFiles: ['requirements.txt', 'pyproject.toml', 'setup.py'],
                suggestedStructure: ['src/', 'tests/', 'docs/', 'README.md']
            },
            typescript: {
                type: 'typescript',
                config: {
                    // Only specify the fields we want to override
                },
                requiredFiles: ['package.json', 'tsconfig.json'],
                suggestedStructure: ['src/', 'tests/', 'docs/', 'README.md']
            },
            javascript: {
                type: 'javascript',
                config: {
                    // Only specify the fields we want to override
                },
                requiredFiles: ['package.json'],
                suggestedStructure: ['src/', 'tests/', 'docs/', 'README.md']
            },
            mixed: {
                type: 'mixed',
                config: {
                    // Only specify the fields we want to override
                },
                suggestedStructure: ['src/', 'tests/', 'docs/', 'README.md']
            },
            unknown: {
                type: 'unknown',
                config: {},
                suggestedStructure: ['README.md']
            }
        };

        return templates[projectType] || templates.unknown;
    }

    /**
     * Get default workspace configuration
     */
    private getDefaultConfig(): WorkspaceConfig {
        return {
            autoInitialize: true,
            fileWatching: {
                watchedExtensions: ['.py', '.ts', '.js', '.md', '.txt', '.json', '.yaml', '.yml'],
                ignorePatterns: [
                    '**/node_modules/**',
                    '**/__pycache__/**',
                    '**/.git/**',
                    '**/dist/**',
                    '**/build/**'
                ],
                autoSyncToMemory: true,
                batchUpdates: true,
                batchDelay: 1000
            },
            fileOperations: {
                defaultEncoding: 'utf8',
                autoCreateDirectories: true,
                backupOriginalFiles: true,
                allowedExtensions: ['.py', '.ts', '.js', '.md', '.txt', '.json', '.yaml', '.yml'],
                restrictedPaths: ['node_modules', '__pycache__', '.git', 'dist', 'build'],
                maxFileSize: 10 * 1024 * 1024
            },
            gitIntegration: {
                autoStage: true,
                requireCleanWorkingDir: false,
                agentCommitPrefix: '[AutoGen MCP]',
                defaultAuthor: {
                    name: 'AutoGen MCP Agent',
                    email: 'autogen-mcp@example.com'
                }
            },
            mcpServer: {
                endpoint: 'http://localhost:8000',
                websocket: true,
                autoConnect: true
            },
            agents: {
                enabled: true,
                memoryCollection: 'workspace',
                defaultAgentId: 'autogen-assistant'
            }
        };
    }

    /**
     * Apply configuration to all services
     */
    private async applyConfiguration(
        workspacePath: string,
        config: WorkspaceConfig,
        projectInfo: ProjectInfo
    ): Promise<void> {
        const workspaceFolder = vscode.workspace.workspaceFolders?.find(
            folder => folder.uri.fsPath === workspacePath
        );

        if (!workspaceFolder) {
            return;
        }

        // Apply file watching configuration
        this.fileWatcher.updateConfig(config.fileWatching);
        this.fileWatcher.startWatching(workspaceFolder, config.fileWatching);

        // Apply file operations configuration
        this.fileOperations.updateConfig(config.fileOperations);

        // Apply Git integration configuration
        this.gitIntegration.updateConfig(config.gitIntegration);

        // Initialize Git if needed and not present
        if (!projectInfo.hasGit) {
            const shouldInit = await vscode.window.showInformationMessage(
                `Initialize Git repository in ${workspaceFolder.name}?`,
                { detail: 'AutoGen MCP can automatically manage Git commits for agent-generated files.' },
                'Yes', 'No'
            );

            if (shouldInit === 'Yes') {
                await this.gitIntegration.initializeRepository(workspaceFolder);
            }
        }

        // Initialize AutoGen MCP configuration if needed
        if (!projectInfo.hasAutoGen && config.autoInitialize) {
            await this.workspaceManager.initializeAutoGen(workspaceFolder);
        }
    }

    /**
     * Load workspace configuration from file
     */
    private async loadWorkspaceConfig(workspacePath: string): Promise<WorkspaceConfig | null> {
        try {
            const workspaceFolder = vscode.workspace.workspaceFolders?.find(
                folder => folder.uri.fsPath === workspacePath
            );

            if (!workspaceFolder) {
                return null;
            }

            const config = await this.workspaceManager.getAutoGenConfig(workspaceFolder);
            return config ? this.convertToWorkspaceConfig(config) : null;
        } catch {
            return null;
        }
    }

    /**
     * Save workspace configuration to file
     */
    private async saveWorkspaceConfig(
        workspacePath: string,
        config: WorkspaceConfig
    ): Promise<boolean> {
        try {
            const workspaceFolder = vscode.workspace.workspaceFolders?.find(
                folder => folder.uri.fsPath === workspacePath
            );

            if (!workspaceFolder) {
                return false;
            }

            const fileConfig = this.convertToFileConfig(config);
            return await this.workspaceManager.updateAutoGenConfig(workspaceFolder, fileConfig);
        } catch {
            return false;
        }
    }

    /**
     * Convert file config to workspace config
     */
    private convertToWorkspaceConfig(fileConfig: any): WorkspaceConfig {
        const defaultConfig = this.getDefaultConfig();

        return {
            ...defaultConfig,
            mcpServer: {
                ...defaultConfig.mcpServer,
                ...fileConfig.mcp_server
            },
            agents: {
                ...defaultConfig.agents,
                ...fileConfig.agents
            },
            fileWatching: {
                ...defaultConfig.fileWatching,
                ...fileConfig.workspace?.file_watching
            }
        };
    }

    /**
     * Convert workspace config to file config
     */
    private convertToFileConfig(workspaceConfig: WorkspaceConfig): any {
        return {
            version: '1.0',
            mcp_server: workspaceConfig.mcpServer,
            agents: workspaceConfig.agents,
            workspace: {
                auto_watch: workspaceConfig.fileWatching.autoSyncToMemory,
                file_extensions: workspaceConfig.fileWatching.watchedExtensions,
                ignore_patterns: workspaceConfig.fileWatching.ignorePatterns
            },
            file_operations: workspaceConfig.fileOperations,
            git_integration: workspaceConfig.gitIntegration
        };
    }

    /**
     * Sanitize collection name for memory service
     */
    private sanitizeCollectionName(rootPath: string): string {
        const baseName = rootPath.split('/').pop() || rootPath.split('\\').pop() || 'workspace';
        return baseName.toLowerCase().replace(/[^a-z0-9]/g, '_');
    }

    /**
     * Update workspace configuration
     */
    async updateWorkspaceConfig(
        workspacePath: string,
        updates: Partial<WorkspaceConfig>
    ): Promise<boolean> {
        const currentConfig = this.configurations.get(workspacePath);
        if (!currentConfig) {
            return false;
        }

        const newConfig = { ...currentConfig, ...updates };
        const success = await this.saveWorkspaceConfig(workspacePath, newConfig);

        if (success) {
            this.configurations.set(workspacePath, newConfig);

            // Reapply configuration
            const projectInfo = this.workspaceManager.getProjectInfo(workspacePath);
            if (projectInfo) {
                await this.applyConfiguration(workspacePath, newConfig, projectInfo);
            }
        }

        return success;
    }

    /**
     * Get configuration for workspace
     */
    getWorkspaceConfig(workspacePath: string): WorkspaceConfig | undefined {
        return this.configurations.get(workspacePath);
    }

    /**
     * Get all workspace configurations
     */
    getAllConfigurations(): Map<string, WorkspaceConfig> {
        return new Map(this.configurations);
    }

    /**
     * Reset workspace to default configuration
     */
    async resetWorkspaceConfig(workspacePath: string): Promise<boolean> {
        const projectInfo = this.workspaceManager.getProjectInfo(workspacePath);
        if (!projectInfo) {
            return false;
        }

        const defaultConfig = this.createConfigFromTemplate(projectInfo);
        return await this.updateWorkspaceConfig(workspacePath, defaultConfig);
    }

    /**
     * Validate workspace configuration
     */
    validateConfig(config: WorkspaceConfig): { valid: boolean; errors: string[] } {
        const errors: string[] = [];

        // Validate MCP server endpoint
        if (!config.mcpServer.endpoint || !config.mcpServer.endpoint.match(/^https?:\/\/.+/)) {
            errors.push('Invalid MCP server endpoint');
        }

        // Validate file extensions
        if (config.fileWatching.watchedExtensions.some(ext => !ext.startsWith('.'))) {
            errors.push('File extensions must start with a dot');
        }

        // Validate memory collection name
        if (!config.agents.memoryCollection.match(/^[a-z0-9_]+$/)) {
            errors.push('Memory collection name must contain only lowercase letters, numbers, and underscores');
        }

        return {
            valid: errors.length === 0,
            errors
        };
    }

    /**
     * Export workspace configuration
     */
    exportConfig(workspacePath: string): string | null {
        const config = this.configurations.get(workspacePath);
        return config ? JSON.stringify(config, null, 2) : null;
    }

    /**
     * Import workspace configuration
     */
    async importConfig(workspacePath: string, configJson: string): Promise<boolean> {
        try {
            const config = JSON.parse(configJson) as WorkspaceConfig;
            const validation = this.validateConfig(config);

            if (!validation.valid) {
                vscode.window.showErrorMessage(
                    `Invalid configuration: ${validation.errors.join(', ')}`
                );
                return false;
            }

            return await this.updateWorkspaceConfig(workspacePath, config);
        } catch {
            vscode.window.showErrorMessage('Failed to parse configuration JSON');
            return false;
        }
    }
}

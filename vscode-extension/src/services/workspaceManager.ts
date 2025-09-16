import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';

/**
 * Project types that can be detected in a workspace
 */
export interface ProjectInfo {
    type: 'python' | 'typescript' | 'javascript' | 'mixed' | 'unknown';
    configFiles: string[];
    rootPath: string;
    hasGit: boolean;
    hasAutoGen: boolean;
}

/**
 * Manages workspace detection, initialization, and configuration
 */
export class WorkspaceManager {
    private workspaceRoots: readonly vscode.WorkspaceFolder[] = [];
    private projectInfo: Map<string, ProjectInfo> = new Map();

    constructor() {
        this.initialize();
    }

    /**
     * Initialize workspace management
     */
    private initialize() {
        this.workspaceRoots = vscode.workspace.workspaceFolders || [];
        this.detectProjects();

        // Listen for workspace changes
        vscode.workspace.onDidChangeWorkspaceFolders((event) => {
            this.handleWorkspaceChange(event);
        });
    }

    /**
     * Detect project types in all workspace folders
     */
    private async detectProjects() {
        for (const folder of this.workspaceRoots) {
            const projectInfo = await this.analyzeWorkspaceFolder(folder);
            this.projectInfo.set(folder.uri.fsPath, projectInfo);
        }
    }

    /**
     * Analyze a workspace folder to determine project type and configuration
     */
    private async analyzeWorkspaceFolder(folder: vscode.WorkspaceFolder): Promise<ProjectInfo> {
        const rootPath = folder.uri.fsPath;
        const configFiles: string[] = [];

        // Common configuration files to check
        const checkFiles = [
            'package.json',
            'tsconfig.json',
            'pyproject.toml',
            'requirements.txt',
            'setup.py',
            'poetry.lock',
            'node_modules',
            '.git',
            'autogen_mcp.py',
            'autogen-mcp.json'
        ];

        // Check which files exist
        const existingFiles = await Promise.all(
            checkFiles.map(async (file) => {
                const filePath = path.join(rootPath, file);
                try {
                    await fs.promises.access(filePath);
                    return file;
                } catch {
                    return null;
                }
            })
        );

        const foundFiles = existingFiles.filter(Boolean) as string[];
        configFiles.push(...foundFiles);

        // Determine project type
        let projectType: ProjectInfo['type'] = 'unknown';

        if (foundFiles.includes('package.json')) {
            // Check if it's TypeScript or JavaScript
            if (foundFiles.includes('tsconfig.json')) {
                projectType = 'typescript';
            } else {
                projectType = 'javascript';
            }
        } else if (foundFiles.some(f => ['pyproject.toml', 'requirements.txt', 'setup.py'].includes(f))) {
            projectType = 'python';
        }

        // Check for mixed projects
        const hasPython = foundFiles.some(f => ['pyproject.toml', 'requirements.txt', 'setup.py'].includes(f));
        const hasJS = foundFiles.includes('package.json');
        if (hasPython && hasJS) {
            projectType = 'mixed';
        }

        return {
            type: projectType,
            configFiles,
            rootPath,
            hasGit: foundFiles.includes('.git'),
            hasAutoGen: foundFiles.some(f => f.startsWith('autogen'))
        };
    }

    /**
     * Handle workspace folder changes
     */
    private async handleWorkspaceChange(event: vscode.WorkspaceFoldersChangeEvent) {
        // Remove deleted folders
        for (const removed of event.removed) {
            this.projectInfo.delete(removed.uri.fsPath);
        }

        // Add new folders
        for (const added of event.added) {
            const projectInfo = await this.analyzeWorkspaceFolder(added);
            this.projectInfo.set(added.uri.fsPath, projectInfo);
        }

        this.workspaceRoots = vscode.workspace.workspaceFolders || [];
    }

    /**
     * Get project information for a specific workspace folder
     */
    getProjectInfo(workspacePath: string): ProjectInfo | undefined {
        return this.projectInfo.get(workspacePath);
    }

    /**
     * Get all detected projects
     */
    getAllProjects(): Map<string, ProjectInfo> {
        return new Map(this.projectInfo);
    }

    /**
     * Check if the workspace has AutoGen MCP configuration
     */
    hasAutoGenConfig(): boolean {
        return Array.from(this.projectInfo.values()).some(info => info.hasAutoGen);
    }

    /**
     * Get the primary workspace folder (first one if multiple)
     */
    getPrimaryWorkspace(): vscode.WorkspaceFolder | undefined {
        return this.workspaceRoots[0];
    }

    /**
     * Initialize AutoGen MCP in workspace if not present
     */
    async initializeAutoGen(workspaceFolder: vscode.WorkspaceFolder): Promise<boolean> {
        const rootPath = workspaceFolder.uri.fsPath;
        const configPath = path.join(rootPath, 'autogen-mcp.json');

        try {
            // Check if config already exists
            await fs.promises.access(configPath);
            return false; // Already exists
        } catch {
            // Create default configuration
            const defaultConfig = {
                version: '1.0',
                mcp_server: {
                    endpoint: 'http://localhost:8000',
                    websocket: true
                },
                agents: {
                    enabled: true,
                    memory_collection: path.basename(rootPath)
                },
                workspace: {
                    auto_watch: true,
                    file_extensions: ['.py', '.ts', '.js', '.md', '.txt'],
                    ignore_patterns: ['node_modules', '__pycache__', '.git']
                }
            };

            await fs.promises.writeFile(
                configPath,
                JSON.stringify(defaultConfig, null, 2),
                'utf8'
            );

            // Update project info
            const projectInfo = await this.analyzeWorkspaceFolder(workspaceFolder);
            this.projectInfo.set(rootPath, projectInfo);

            return true; // Successfully created
        }
    }

    /**
     * Get AutoGen configuration for a workspace
     */
    async getAutoGenConfig(workspaceFolder: vscode.WorkspaceFolder): Promise<any> {
        const configPath = path.join(workspaceFolder.uri.fsPath, 'autogen-mcp.json');

        try {
            const configContent = await fs.promises.readFile(configPath, 'utf8');
            return JSON.parse(configContent);
        } catch {
            return null;
        }
    }

    /**
     * Update AutoGen configuration for a workspace
     */
    async updateAutoGenConfig(workspaceFolder: vscode.WorkspaceFolder, config: any): Promise<boolean> {
        const configPath = path.join(workspaceFolder.uri.fsPath, 'autogen-mcp.json');

        try {
            await fs.promises.writeFile(
                configPath,
                JSON.stringify(config, null, 2),
                'utf8'
            );
            return true;
        } catch {
            return false;
        }
    }
}

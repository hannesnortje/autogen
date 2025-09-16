import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

/**
 * Git operation types
 */
export interface GitCommitOptions {
    message: string;
    agentId?: string;
    files?: string[];
    author?: {
        name: string;
        email: string;
    };
    coAuthor?: string;
}

export interface GitStatus {
    branch: string;
    hasChanges: boolean;
    stagedFiles: string[];
    unstagedFiles: string[];
    untrackedFiles: string[];
}

export interface GitCommitResult {
    success: boolean;
    commitHash?: string;
    message?: string;
    error?: string;
}

/**
 * Configuration for Git operations
 */
export interface GitConfig {
    autoStage: boolean;
    requireCleanWorkingDir: boolean;
    agentCommitPrefix: string;
    defaultAuthor: {
        name: string;
        email: string;
    };
}

/**
 * Manages Git operations for agent-generated commits and version control
 */
export class GitIntegration {
    private config: GitConfig;
    private outputChannel: vscode.OutputChannel;

    constructor() {
        this.config = this.getDefaultConfig();
        this.outputChannel = vscode.window.createOutputChannel('AutoGen MCP - Git Integration');
    }

    /**
     * Get default Git configuration
     */
    private getDefaultConfig(): GitConfig {
        return {
            autoStage: true,
            requireCleanWorkingDir: false,
            agentCommitPrefix: '[AutoGen MCP]',
            defaultAuthor: {
                name: 'AutoGen MCP Agent',
                email: 'autogen-mcp@example.com'
            }
        };
    }

    /**
     * Check if workspace has Git repository
     */
    async hasGitRepository(workspaceFolder: vscode.WorkspaceFolder): Promise<boolean> {
        try {
            const gitDir = path.join(workspaceFolder.uri.fsPath, '.git');
            await fs.promises.access(gitDir);
            return true;
        } catch {
            return false;
        }
    }

    /**
     * Initialize Git repository in workspace
     */
    async initializeRepository(workspaceFolder: vscode.WorkspaceFolder): Promise<boolean> {
        try {
            await this.execGitCommand(workspaceFolder, 'init');

            // Create initial .gitignore if it doesn't exist
            await this.createDefaultGitignore(workspaceFolder);

            this.outputChannel.appendLine(`Initialized Git repository in ${workspaceFolder.name}`);
            return true;
        } catch (error) {
            this.outputChannel.appendLine(`Failed to initialize Git repository: ${error}`);
            return false;
        }
    }

    /**
     * Get current Git status
     */
    async getStatus(workspaceFolder: vscode.WorkspaceFolder): Promise<GitStatus | null> {
        try {
            const [branchResult, statusResult] = await Promise.all([
                this.execGitCommand(workspaceFolder, 'branch --show-current'),
                this.execGitCommand(workspaceFolder, 'status --porcelain')
            ]);

            const branch = branchResult.stdout.trim() || 'main';
            const statusLines = statusResult.stdout.trim().split('\n').filter(line => line);

            const stagedFiles: string[] = [];
            const unstagedFiles: string[] = [];
            const untrackedFiles: string[] = [];

            for (const line of statusLines) {
                const status = line.substring(0, 2);
                const filePath = line.substring(3);

                if (status[0] !== ' ') {
                    stagedFiles.push(filePath);
                }
                if (status[1] === 'M' || status[1] === 'D') {
                    unstagedFiles.push(filePath);
                }
                if (status[0] === '?' && status[1] === '?') {
                    untrackedFiles.push(filePath);
                }
            }

            return {
                branch,
                hasChanges: statusLines.length > 0,
                stagedFiles,
                unstagedFiles,
                untrackedFiles
            };

        } catch (error) {
            this.outputChannel.appendLine(`Failed to get Git status: ${error}`);
            return null;
        }
    }

    /**
     * Stage files for commit
     */
    async stageFiles(
        workspaceFolder: vscode.WorkspaceFolder,
        files: string[] | 'all' = 'all'
    ): Promise<boolean> {
        try {
            const command = files === 'all' ? 'add .' : `add ${files.map(f => `"${f}"`).join(' ')}`;
            await this.execGitCommand(workspaceFolder, command);

            this.outputChannel.appendLine(`Staged files: ${files === 'all' ? 'all' : files.join(', ')}`);
            return true;
        } catch (error) {
            this.outputChannel.appendLine(`Failed to stage files: ${error}`);
            return false;
        }
    }

    /**
     * Create commit with agent-generated changes
     */
    async createAgentCommit(
        workspaceFolder: vscode.WorkspaceFolder,
        options: GitCommitOptions
    ): Promise<GitCommitResult> {
        try {
            // Check if Git repository exists
            if (!(await this.hasGitRepository(workspaceFolder))) {
                return {
                    success: false,
                    error: 'No Git repository found. Initialize Git first.'
                };
            }

            // Stage files if specified and auto-stage is enabled
            if (this.config.autoStage) {
                if (options.files && options.files.length > 0) {
                    await this.stageFiles(workspaceFolder, options.files);
                } else {
                    await this.stageFiles(workspaceFolder, 'all');
                }
            }

            // Check if there are staged changes
            const status = await this.getStatus(workspaceFolder);
            if (!status || status.stagedFiles.length === 0) {
                return {
                    success: false,
                    error: 'No staged changes to commit'
                };
            }

            // Prepare commit message
            const agentPrefix = options.agentId
                ? `${this.config.agentCommitPrefix} [${options.agentId}]`
                : this.config.agentCommitPrefix;
            const commitMessage = `${agentPrefix} ${options.message}`;

            // Prepare author information
            const author = options.author || this.config.defaultAuthor;
            let commitCommand = `commit -m "${commitMessage}"`;

            if (author.name && author.email) {
                commitCommand = `commit --author="${author.name} <${author.email}>" -m "${commitMessage}"`;
            }

            // Add co-author if specified
            if (options.coAuthor) {
                const messageWithCoAuthor = `${commitMessage}\n\nCo-authored-by: ${options.coAuthor}`;
                commitCommand = commitCommand.replace(`-m "${commitMessage}"`, `-m "${messageWithCoAuthor}"`);
            }

            // Execute commit
            const result = await this.execGitCommand(workspaceFolder, commitCommand);

            // Extract commit hash from output
            const commitHashMatch = result.stdout.match(/\[.*?([a-f0-9]{7,})\]/);
            const commitHash = commitHashMatch ? commitHashMatch[1] : undefined;

            const commitResult: GitCommitResult = {
                success: true,
                commitHash,
                message: commitMessage
            };

            this.outputChannel.appendLine(`Created commit: ${commitMessage}`);
            if (commitHash) {
                this.outputChannel.appendLine(`Commit hash: ${commitHash}`);
            }

            // Show success notification
            vscode.window.showInformationMessage(
                `AutoGen MCP: Created Git commit - ${commitMessage.substring(0, 50)}${commitMessage.length > 50 ? '...' : ''}`
            );

            return commitResult;

        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            this.outputChannel.appendLine(`Failed to create commit: ${errorMessage}`);

            return {
                success: false,
                error: errorMessage
            };
        }
    }

    /**
     * Create and switch to a new branch for agent work
     */
    async createAgentBranch(
        workspaceFolder: vscode.WorkspaceFolder,
        branchName: string,
        agentId?: string
    ): Promise<boolean> {
        try {
            const fullBranchName = agentId ? `autogen/${agentId}/${branchName}` : `autogen/${branchName}`;

            await this.execGitCommand(workspaceFolder, `checkout -b ${fullBranchName}`);

            this.outputChannel.appendLine(`Created and switched to branch: ${fullBranchName}`);
            vscode.window.showInformationMessage(
                `AutoGen MCP: Created branch - ${fullBranchName}`
            );

            return true;
        } catch (error) {
            this.outputChannel.appendLine(`Failed to create branch: ${error}`);
            return false;
        }
    }

    /**
     * Switch to existing branch
     */
    async switchToBranch(
        workspaceFolder: vscode.WorkspaceFolder,
        branchName: string
    ): Promise<boolean> {
        try {
            await this.execGitCommand(workspaceFolder, `checkout ${branchName}`);

            this.outputChannel.appendLine(`Switched to branch: ${branchName}`);
            return true;
        } catch (error) {
            this.outputChannel.appendLine(`Failed to switch to branch: ${error}`);
            return false;
        }
    }

    /**
     * Get list of branches
     */
    async getBranches(workspaceFolder: vscode.WorkspaceFolder): Promise<string[]> {
        try {
            const result = await this.execGitCommand(workspaceFolder, 'branch --list');
            return result.stdout
                .split('\n')
                .map(line => line.replace(/^\*?\s*/, '').trim())
                .filter(line => line);
        } catch (error) {
            this.outputChannel.appendLine(`Failed to get branches: ${error}`);
            return [];
        }
    }

    /**
     * Create default .gitignore file
     */
    private async createDefaultGitignore(workspaceFolder: vscode.WorkspaceFolder): Promise<void> {
        const gitignorePath = path.join(workspaceFolder.uri.fsPath, '.gitignore');

        try {
            await fs.promises.access(gitignorePath);
            // .gitignore already exists
            return;
        } catch {
            // Create default .gitignore
            const defaultGitignore = `# AutoGen MCP generated .gitignore

# Dependencies
node_modules/
__pycache__/
*.pyc
*.pyo

# Build outputs
dist/
build/
*.egg-info/

# IDE and editor files
.vscode/settings.json
.idea/
*.swp
*.swo

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Environment files
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Logs
*.log
logs/

# Temporary files
*.tmp
*.temp

# AutoGen MCP specific
autogen-mcp.log
*.backup.*
`;

            await fs.promises.writeFile(gitignorePath, defaultGitignore, 'utf8');
            this.outputChannel.appendLine('Created default .gitignore');
        }
    }

    /**
     * Execute Git command in workspace directory
     */
    private async execGitCommand(
        workspaceFolder: vscode.WorkspaceFolder,
        command: string
    ): Promise<{ stdout: string; stderr: string }> {
        return execAsync(`git ${command}`, {
            cwd: workspaceFolder.uri.fsPath,
            encoding: 'utf8'
        });
    }

    /**
     * Update Git configuration
     */
    updateConfig(newConfig: Partial<GitConfig>): void {
        this.config = { ...this.config, ...newConfig };
    }

    /**
     * Get current configuration
     */
    getConfig(): GitConfig {
        return { ...this.config };
    }

    /**
     * Get Git integration statistics
     */
    async getStats(workspaceFolder: vscode.WorkspaceFolder): Promise<{
        hasRepository: boolean;
        currentBranch?: string;
        totalCommits?: number;
        agentCommits?: number;
    }> {
        const hasRepository = await this.hasGitRepository(workspaceFolder);

        if (!hasRepository) {
            return { hasRepository };
        }

        try {
            const [branchResult, totalCommitsResult, agentCommitsResult] = await Promise.all([
                this.execGitCommand(workspaceFolder, 'branch --show-current'),
                this.execGitCommand(workspaceFolder, 'rev-list --count HEAD').catch(() => ({ stdout: '0' })),
                this.execGitCommand(workspaceFolder, `log --grep="${this.config.agentCommitPrefix}" --oneline`).catch(() => ({ stdout: '' }))
            ]);

            return {
                hasRepository,
                currentBranch: branchResult.stdout.trim() || undefined,
                totalCommits: parseInt(totalCommitsResult.stdout.trim()) || 0,
                agentCommits: agentCommitsResult.stdout.split('\n').filter(line => line.trim()).length
            };
        } catch (error) {
            this.outputChannel.appendLine(`Failed to get Git stats: ${error}`);
            return { hasRepository };
        }
    }

    /**
     * Dispose resources
     */
    dispose(): void {
        this.outputChannel.dispose();
    }
}

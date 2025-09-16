import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';

/**
 * File operation types
 */
export interface FileWriteOperation {
    filePath: string;
    content: string;
    encoding?: BufferEncoding;
    createDirectories?: boolean;
    backup?: boolean;
    agentId?: string;
    metadata?: Record<string, any>;
}

export interface FileWriteResult {
    success: boolean;
    filePath: string;
    backupPath?: string;
    error?: string;
    metadata?: {
        createdAt: string;
        size: number;
        encoding: string;
    };
}

/**
 * Configuration for file operations
 */
export interface FileOperationsConfig {
    defaultEncoding: BufferEncoding;
    autoCreateDirectories: boolean;
    backupOriginalFiles: boolean;
    allowedExtensions: string[];
    restrictedPaths: string[];
    maxFileSize: number; // bytes
}

/**
 * Manages file operations for agent outputs and workspace integration
 */
export class FileOperations {
    private config: FileOperationsConfig;
    private outputChannel: vscode.OutputChannel;

    constructor() {
        this.config = this.getDefaultConfig();
        this.outputChannel = vscode.window.createOutputChannel('AutoGen MCP - File Operations');
    }

    /**
     * Get default file operations configuration
     */
    private getDefaultConfig(): FileOperationsConfig {
        return {
            defaultEncoding: 'utf8',
            autoCreateDirectories: true,
            backupOriginalFiles: true,
            allowedExtensions: ['.py', '.ts', '.js', '.md', '.txt', '.json', '.yaml', '.yml', '.html', '.css'],
            restrictedPaths: [
                'node_modules',
                '__pycache__',
                '.git',
                'dist',
                'build',
                '.vscode'
            ],
            maxFileSize: 10 * 1024 * 1024 // 10MB
        };
    }

    /**
     * Write content to a file in the workspace
     */
    async writeFile(
        workspaceFolder: vscode.WorkspaceFolder,
        operation: FileWriteOperation
    ): Promise<FileWriteResult> {
        try {
            // Validate operation
            const validation = await this.validateOperation(workspaceFolder, operation);
            if (!validation.valid) {
                return {
                    success: false,
                    filePath: operation.filePath,
                    error: validation.error
                };
            }

            const fullPath = path.resolve(workspaceFolder.uri.fsPath, operation.filePath);
            const encoding = operation.encoding || this.config.defaultEncoding;

            // Create directories if needed
            if (operation.createDirectories ?? this.config.autoCreateDirectories) {
                await this.ensureDirectoryExists(path.dirname(fullPath));
            }

            // Backup existing file if needed
            let backupPath: string | undefined;
            if (operation.backup ?? this.config.backupOriginalFiles) {
                backupPath = await this.backupFile(fullPath);
            }

            // Write the file
            await fs.promises.writeFile(fullPath, operation.content, encoding);

            // Get file stats
            const stats = await fs.promises.stat(fullPath);

            const result: FileWriteResult = {
                success: true,
                filePath: operation.filePath,
                backupPath,
                metadata: {
                    createdAt: new Date().toISOString(),
                    size: stats.size,
                    encoding
                }
            };

            // Log operation
            this.logOperation('write', operation, result);

            // Show success notification
            vscode.window.showInformationMessage(
                `AutoGen MCP: File created/updated - ${operation.filePath}`
            );

            return result;

        } catch (error) {
            const result: FileWriteResult = {
                success: false,
                filePath: operation.filePath,
                error: error instanceof Error ? error.message : 'Unknown error'
            };

            this.logOperation('write', operation, result);
            return result;
        }
    }

    /**
     * Write multiple files in batch
     */
    async writeFilesBatch(
        workspaceFolder: vscode.WorkspaceFolder,
        operations: FileWriteOperation[]
    ): Promise<FileWriteResult[]> {
        const results: FileWriteResult[] = [];

        for (const operation of operations) {
            const result = await this.writeFile(workspaceFolder, operation);
            results.push(result);

            // Stop on first error if configured
            if (!result.success) {
                this.outputChannel.appendLine(`Batch operation stopped due to error: ${result.error}`);
                break;
            }
        }

        return results;
    }

    /**
     * Create a new file with agent-generated content
     */
    async createAgentFile(
        workspaceFolder: vscode.WorkspaceFolder,
        filePath: string,
        content: string,
        agentId: string,
        metadata?: Record<string, any>
    ): Promise<FileWriteResult> {
        // Add agent metadata as comment/header
        const fileExtension = path.extname(filePath);
        const enhancedContent = this.addAgentMetadata(content, agentId, fileExtension, metadata);

        const operation: FileWriteOperation = {
            filePath,
            content: enhancedContent,
            agentId,
            metadata: {
                ...metadata,
                generatedBy: agentId,
                generatedAt: new Date().toISOString()
            }
        };

        return this.writeFile(workspaceFolder, operation);
    }

    /**
     * Add agent metadata as comments to file content
     */
    private addAgentMetadata(
        content: string,
        agentId: string,
        fileExtension: string,
        metadata?: Record<string, any>
    ): string {
        const timestamp = new Date().toISOString();

        // Determine comment syntax
        const commentSyntax = this.getCommentSyntax(fileExtension);
        if (!commentSyntax) {
            return content; // No comment syntax known, return as-is
        }

        const { start, end } = commentSyntax;

        let header = `${start} Generated by AutoGen MCP Agent: ${agentId}\n`;
        header += `${start} Generated at: ${timestamp}\n`;

        if (metadata) {
            header += `${start} Metadata: ${JSON.stringify(metadata)}\n`;
        }

        header += `${start} End of AutoGen MCP metadata${end ? ` ${end}` : ''}\n\n`;

        return header + content;
    }

    /**
     * Get comment syntax for file extension
     */
    private getCommentSyntax(extension: string): { start: string; end?: string } | null {
        const syntaxMap: Record<string, { start: string; end?: string }> = {
            '.py': { start: '#' },
            '.js': { start: '//' },
            '.ts': { start: '//' },
            '.java': { start: '//' },
            '.c': { start: '/*', end: '*/' },
            '.cpp': { start: '//' },
            '.h': { start: '//' },
            '.css': { start: '/*', end: '*/' },
            '.html': { start: '<!--', end: '-->' },
            '.xml': { start: '<!--', end: '-->' },
            '.yaml': { start: '#' },
            '.yml': { start: '#' },
            '.sh': { start: '#' },
            '.md': { start: '<!--', end: '-->' },
            '.json': { start: '// Note:' } // Non-standard but readable
        };

        return syntaxMap[extension.toLowerCase()] || null;
    }

    /**
     * Validate file operation before execution
     */
    private async validateOperation(
        workspaceFolder: vscode.WorkspaceFolder,
        operation: FileWriteOperation
    ): Promise<{ valid: boolean; error?: string }> {
        // Check file extension
        const ext = path.extname(operation.filePath);
        if (this.config.allowedExtensions.length > 0 && !this.config.allowedExtensions.includes(ext)) {
            return {
                valid: false,
                error: `File extension '${ext}' is not allowed`
            };
        }

        // Check file size
        if (Buffer.byteLength(operation.content, operation.encoding || this.config.defaultEncoding) > this.config.maxFileSize) {
            return {
                valid: false,
                error: `File size exceeds maximum limit of ${this.config.maxFileSize} bytes`
            };
        }

        // Check restricted paths
        const normalizedPath = path.normalize(operation.filePath);
        for (const restricted of this.config.restrictedPaths) {
            if (normalizedPath.includes(restricted)) {
                return {
                    valid: false,
                    error: `File path contains restricted directory: ${restricted}`
                };
            }
        }

        // Check if path is within workspace
        const fullPath = path.resolve(workspaceFolder.uri.fsPath, operation.filePath);
        if (!fullPath.startsWith(workspaceFolder.uri.fsPath)) {
            return {
                valid: false,
                error: 'File path is outside workspace'
            };
        }

        return { valid: true };
    }

    /**
     * Ensure directory exists
     */
    private async ensureDirectoryExists(dirPath: string): Promise<void> {
        try {
            await fs.promises.mkdir(dirPath, { recursive: true });
        } catch (error) {
            if ((error as NodeJS.ErrnoException).code !== 'EEXIST') {
                throw error;
            }
        }
    }

    /**
     * Backup an existing file
     */
    private async backupFile(filePath: string): Promise<string | undefined> {
        try {
            await fs.promises.access(filePath);

            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const backupPath = `${filePath}.backup.${timestamp}`;

            await fs.promises.copyFile(filePath, backupPath);
            return backupPath;

        } catch (error) {
            // File doesn't exist, no backup needed
            return undefined;
        }
    }

    /**
     * Log file operation
     */
    private logOperation(
        operationType: string,
        operation: FileWriteOperation,
        result: FileWriteResult
    ): void {
        const logEntry = {
            timestamp: new Date().toISOString(),
            operation: operationType,
            filePath: operation.filePath,
            agentId: operation.agentId,
            success: result.success,
            error: result.error,
            metadata: result.metadata
        };

        this.outputChannel.appendLine(JSON.stringify(logEntry, null, 2));
    }

    /**
     * Update configuration
     */
    updateConfig(newConfig: Partial<FileOperationsConfig>): void {
        this.config = { ...this.config, ...newConfig };
    }

    /**
     * Get current configuration
     */
    getConfig(): FileOperationsConfig {
        return { ...this.config };
    }

    /**
     * Get file operation statistics
     */
    getStats(): {
        allowedExtensions: number;
        restrictedPaths: number;
        maxFileSize: number;
    } {
        return {
            allowedExtensions: this.config.allowedExtensions.length,
            restrictedPaths: this.config.restrictedPaths.length,
            maxFileSize: this.config.maxFileSize
        };
    }

    /**
     * Clean up backup files older than specified days
     */
    async cleanupBackups(workspaceFolder: vscode.WorkspaceFolder, daysOld: number = 7): Promise<number> {
        let cleanedCount = 0;
        const cutoffTime = Date.now() - (daysOld * 24 * 60 * 60 * 1000);

        try {
            const files = await this.findBackupFiles(workspaceFolder.uri.fsPath);

            for (const backupFile of files) {
                const stats = await fs.promises.stat(backupFile);
                if (stats.mtime.getTime() < cutoffTime) {
                    await fs.promises.unlink(backupFile);
                    cleanedCount++;
                }
            }

        } catch (error) {
            this.outputChannel.appendLine(`Error cleaning backups: ${error}`);
        }

        return cleanedCount;
    }

    /**
     * Find backup files in workspace
     */
    private async findBackupFiles(rootPath: string): Promise<string[]> {
        const backupFiles: string[] = [];

        const search = async (dir: string) => {
            const entries = await fs.promises.readdir(dir, { withFileTypes: true });

            for (const entry of entries) {
                const fullPath = path.join(dir, entry.name);

                if (entry.isDirectory() && !this.config.restrictedPaths.includes(entry.name)) {
                    await search(fullPath);
                } else if (entry.isFile() && entry.name.includes('.backup.')) {
                    backupFiles.push(fullPath);
                }
            }
        };

        await search(rootPath);
        return backupFiles;
    }

    /**
     * Dispose resources
     */
    dispose(): void {
        this.outputChannel.dispose();
    }
}

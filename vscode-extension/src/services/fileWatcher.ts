import * as vscode from 'vscode';
import * as path from 'path';
import { RealtimeClient } from '../realtime';

/**
 * File change events
 */
export interface FileChangeEvent {
    type: 'created' | 'modified' | 'deleted';
    filePath: string;
    workspaceFolder: string;
    content?: string;
    timestamp: Date;
}

/**
 * Configuration for file watching
 */
export interface FileWatchConfig {
    watchedExtensions: string[];
    ignorePatterns: string[];
    autoSyncToMemory: boolean;
    batchUpdates: boolean;
    batchDelay: number; // ms
}

/**
 * Manages file system watching and memory synchronization
 */
export class FileWatcher {
    private watchers: Map<string, vscode.FileSystemWatcher> = new Map();
    private realtimeClient: RealtimeClient;
    private config: FileWatchConfig;
    private pendingUpdates: Map<string, FileChangeEvent> = new Map();
    private batchTimer: NodeJS.Timeout | null = null;

    constructor(realtimeClient: RealtimeClient) {
        this.realtimeClient = realtimeClient;
        this.config = this.getDefaultConfig();
    }

    /**
     * Get default file watching configuration
     */
    private getDefaultConfig(): FileWatchConfig {
        return {
            watchedExtensions: ['.py', '.ts', '.js', '.md', '.txt', '.json', '.yaml', '.yml'],
            ignorePatterns: [
                '**/node_modules/**',
                '**/__pycache__/**',
                '**/.git/**',
                '**/dist/**',
                '**/build/**',
                '**/.vscode/**'
            ],
            autoSyncToMemory: true,
            batchUpdates: true,
            batchDelay: 1000 // 1 second
        };
    }

    /**
     * Start watching files in a workspace folder
     */
    startWatching(workspaceFolder: vscode.WorkspaceFolder, config?: Partial<FileWatchConfig>) {
        if (config) {
            this.config = { ...this.config, ...config };
        }

        const watcherKey = workspaceFolder.uri.fsPath;

        // Don't create duplicate watchers
        if (this.watchers.has(watcherKey)) {
            return;
        }

        // Create file system watcher pattern
        const pattern = new vscode.RelativePattern(
            workspaceFolder,
            `**/*{${this.config.watchedExtensions.join(',')}}`
        );

        const watcher = vscode.workspace.createFileSystemWatcher(pattern);

        // Handle file events
        watcher.onDidCreate((uri) => this.handleFileEvent('created', uri, workspaceFolder));
        watcher.onDidChange((uri) => this.handleFileEvent('modified', uri, workspaceFolder));
        watcher.onDidDelete((uri) => this.handleFileEvent('deleted', uri, workspaceFolder));

        this.watchers.set(watcherKey, watcher);

        vscode.window.showInformationMessage(
            `AutoGen MCP: Started watching files in ${workspaceFolder.name}`
        );
    }

    /**
     * Stop watching files in a workspace folder
     */
    stopWatching(workspaceFolder: vscode.WorkspaceFolder) {
        const watcherKey = workspaceFolder.uri.fsPath;
        const watcher = this.watchers.get(watcherKey);

        if (watcher) {
            watcher.dispose();
            this.watchers.delete(watcherKey);
        }
    }

    /**
     * Handle file system events
     */
    private async handleFileEvent(
        type: 'created' | 'modified' | 'deleted',
        uri: vscode.Uri,
        workspaceFolder: vscode.WorkspaceFolder
    ) {
        // Check if file should be ignored
        if (this.shouldIgnoreFile(uri.fsPath)) {
            return;
        }

        const relativePath = path.relative(workspaceFolder.uri.fsPath, uri.fsPath);

        // Read file content for created/modified files
        let content: string | undefined;
        if (type !== 'deleted') {
            try {
                const document = await vscode.workspace.openTextDocument(uri);
                content = document.getText();
            } catch (error) {
                console.warn(`Failed to read file content: ${uri.fsPath}`, error);
            }
        }

        const event: FileChangeEvent = {
            type,
            filePath: relativePath,
            workspaceFolder: workspaceFolder.name,
            content,
            timestamp: new Date()
        };

        if (this.config.batchUpdates) {
            this.batchFileUpdate(uri.fsPath, event);
        } else {
            await this.processFileUpdate(event);
        }
    }

    /**
     * Check if a file should be ignored based on patterns
     */
    private shouldIgnoreFile(filePath: string): boolean {
        return this.config.ignorePatterns.some(pattern => {
            // Simple glob pattern matching
            const regex = new RegExp(pattern.replace(/\*\*/g, '.*').replace(/\*/g, '[^/]*'));
            return regex.test(filePath);
        });
    }

    /**
     * Batch file updates to reduce noise
     */
    private batchFileUpdate(filePath: string, event: FileChangeEvent) {
        // Store the latest event for this file
        this.pendingUpdates.set(filePath, event);

        // Reset timer
        if (this.batchTimer) {
            clearTimeout(this.batchTimer);
        }

        this.batchTimer = setTimeout(() => {
            this.processBatchedUpdates();
        }, this.config.batchDelay);
    }

    /**
     * Process all batched file updates
     */
    private async processBatchedUpdates() {
        const updates = Array.from(this.pendingUpdates.values());
        this.pendingUpdates.clear();

        for (const update of updates) {
            await this.processFileUpdate(update);
        }
    }

    /**
     * Process a single file update
     */
    private async processFileUpdate(event: FileChangeEvent) {
        try {
            if (this.config.autoSyncToMemory) {
                await this.syncToMemory(event);
            }

            // Emit real-time update
            this.realtimeClient.broadcast('file-change', event);

            // Show notification for significant changes
            if (event.type === 'created') {
                vscode.window.showInformationMessage(
                    `AutoGen MCP: New file detected - ${event.filePath}`
                );
            }

        } catch (error) {
            console.error('Error processing file update:', error);
        }
    }

    /**
     * Synchronize file changes to memory service
     */
    private async syncToMemory(event: FileChangeEvent): Promise<void> {
        if (event.type === 'deleted') {
            // Remove from memory service
            this.realtimeClient.broadcast('memory-remove', {
                type: 'file',
                path: event.filePath,
                workspace: event.workspaceFolder
            });
        } else if (event.content) {
            // Add/update in memory service
            this.realtimeClient.broadcast('memory-update', {
                type: 'file',
                path: event.filePath,
                workspace: event.workspaceFolder,
                content: event.content,
                metadata: {
                    lastModified: event.timestamp.toISOString(),
                    fileType: path.extname(event.filePath),
                    changeType: event.type
                }
            });
        }
    }

    /**
     * Update file watching configuration
     */
    updateConfig(newConfig: Partial<FileWatchConfig>) {
        this.config = { ...this.config, ...newConfig };

        // Restart watchers with new configuration
        const workspaceFolders = Array.from(this.watchers.keys());
        for (const folderPath of workspaceFolders) {
            const workspaceFolder = vscode.workspace.workspaceFolders?.find(
                folder => folder.uri.fsPath === folderPath
            );
            if (workspaceFolder) {
                this.stopWatching(workspaceFolder);
                this.startWatching(workspaceFolder);
            }
        }
    }

    /**
     * Get current configuration
     */
    getConfig(): FileWatchConfig {
        return { ...this.config };
    }

    /**
     * Get statistics about file watching
     */
    getStats(): {
        watchedFolders: number;
        pendingUpdates: number;
        isActive: boolean;
    } {
        return {
            watchedFolders: this.watchers.size,
            pendingUpdates: this.pendingUpdates.size,
            isActive: this.watchers.size > 0
        };
    }

    /**
     * Manually trigger file scan for a workspace
     */
    async scanWorkspace(workspaceFolder: vscode.WorkspaceFolder): Promise<FileChangeEvent[]> {
        const events: FileChangeEvent[] = [];

        // Use VS Code's findFiles to scan workspace
        const pattern = `**/*{${this.config.watchedExtensions.join(',')}}`;
        const excludePattern = `{${this.config.ignorePatterns.join(',')}}`;

        const files = await vscode.workspace.findFiles(
            new vscode.RelativePattern(workspaceFolder, pattern),
            excludePattern
        );

        for (const fileUri of files) {
            try {
                const document = await vscode.workspace.openTextDocument(fileUri);
                const relativePath = path.relative(workspaceFolder.uri.fsPath, fileUri.fsPath);

                const event: FileChangeEvent = {
                    type: 'created', // Treat initial scan as creation
                    filePath: relativePath,
                    workspaceFolder: workspaceFolder.name,
                    content: document.getText(),
                    timestamp: new Date()
                };

                events.push(event);

                if (this.config.autoSyncToMemory) {
                    await this.syncToMemory(event);
                }

            } catch (error) {
                console.warn(`Failed to scan file: ${fileUri.fsPath}`, error);
            }
        }

        return events;
    }

    /**
     * Dispose all watchers
     */
    dispose() {
        for (const watcher of this.watchers.values()) {
            watcher.dispose();
        }
        this.watchers.clear();

        if (this.batchTimer) {
            clearTimeout(this.batchTimer);
        }
    }
}

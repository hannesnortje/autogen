import * as vscode from 'vscode';
import { McpClient } from './mcpClient';

export interface MemoryItem {
    id: string;
    content: string;
    scope: string;
    score?: number;
}

export class AutoGenMemoryProvider implements vscode.TreeDataProvider<MemoryItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<MemoryItem | undefined | null | void> = new vscode.EventEmitter<MemoryItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<MemoryItem | undefined | null | void> = this._onDidChangeTreeData.event;

    private memories: MemoryItem[] = [];

    constructor(private mcpClient: McpClient) {
        this.loadMemories();
    }

    refresh(): void {
        this.loadMemories();
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: MemoryItem): vscode.TreeItem {
        const item = new vscode.TreeItem(
            element.content.substring(0, 50) + (element.content.length > 50 ? '...' : ''),
            vscode.TreeItemCollapsibleState.None
        );

        item.tooltip = `Scope: ${element.scope}\nContent: ${element.content}`;
        item.description = element.scope;
        item.iconPath = new vscode.ThemeIcon('note');

        return item;
    }

    getChildren(element?: MemoryItem): Thenable<MemoryItem[]> {
        if (!element) {
            return Promise.resolve(this.memories);
        }
        return Promise.resolve([]);
    }

    private async loadMemories(): Promise<void> {
        try {
            // For now, create mock memories
            // In a real implementation, this would fetch from the MCP server
            this.memories = [
                {
                    id: 'memory-001',
                    content: 'Project uses Python 3.12 with Poetry for dependency management',
                    scope: 'project'
                },
                {
                    id: 'memory-002',
                    content: 'FastAPI server runs on port 9000 with HTTP and WebSocket support',
                    scope: 'architecture'
                }
            ];
        } catch (error) {
            this.memories = [];
            vscode.window.showErrorMessage(`Failed to load memories: ${error}`);
        }
    }
}

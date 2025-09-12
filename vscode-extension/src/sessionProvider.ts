import * as vscode from 'vscode';
import { McpClient } from './mcpClient';

export interface SessionItem {
    id: string;
    project: string;
    status: string;
    createdAt: string;
}

export class AutoGenSessionProvider implements vscode.TreeDataProvider<SessionItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<SessionItem | undefined | null | void> = new vscode.EventEmitter<SessionItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<SessionItem | undefined | null | void> = this._onDidChangeTreeData.event;

    private sessions: SessionItem[] = [];

    constructor(private mcpClient: McpClient) {
        this.loadSessions();
    }

    refresh(): void {
        this.loadSessions();
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: SessionItem): vscode.TreeItem {
        const item = new vscode.TreeItem(
            `${element.project} (${element.status})`,
            vscode.TreeItemCollapsibleState.None
        );

        item.tooltip = `Session ID: ${element.id}\nCreated: ${element.createdAt}`;
        item.description = element.id.substring(0, 8);
        item.iconPath = new vscode.ThemeIcon(
            element.status === 'active' ? 'play-circle' : 'stop-circle'
        );

        return item;
    }

    getChildren(element?: SessionItem): Thenable<SessionItem[]> {
        if (!element) {
            return Promise.resolve(this.sessions);
        }
        return Promise.resolve([]);
    }

    private async loadSessions(): Promise<void> {
        try {
            // For now, create mock sessions
            // In a real implementation, this would fetch from the MCP server
            this.sessions = [
                {
                    id: 'session-001',
                    project: vscode.workspace.name || 'default-project',
                    status: 'active',
                    createdAt: new Date().toISOString()
                }
            ];
        } catch (error) {
            this.sessions = [];
            vscode.window.showErrorMessage(`Failed to load sessions: ${error}`);
        }
    }
}

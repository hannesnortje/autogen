import * as vscode from 'vscode';
import { McpClient } from './mcpClient';

export interface SessionData {
    id: string;
    name: string;
    status: 'active' | 'stopped' | 'error';
    created_at: string;
    last_activity?: string;
    agents: string[];
    conversation_count: number;
    memory_count: number;
}

export class SessionTreeItem extends vscode.TreeItem {
    constructor(
        public readonly session: SessionData,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState
    ) {
        super(session.name, collapsibleState);

        this.tooltip = this.createTooltip();
        this.description = this.createDescription();
        this.contextValue = `session-${session.status}`;
        this.iconPath = this.getIconPath();

        if (collapsibleState === vscode.TreeItemCollapsibleState.None) {
            this.command = {
                command: 'autogen.openSessionDashboard',
                title: 'Open Session Dashboard',
                arguments: [session.id]
            };
        }
    }

    private createTooltip(): string {
        const statusIcon = this.session.status === 'active' ? '🟢' :
                          this.session.status === 'stopped' ? '🔴' : '🟡';

        return `${statusIcon} ${this.session.name}\n` +
               `Status: ${this.session.status}\n` +
               `Agents: ${this.session.agents.length}\n` +
               `Conversations: ${this.session.conversation_count}\n` +
               `Memories: ${this.session.memory_count}\n` +
               `Created: ${new Date(this.session.created_at).toLocaleString()}\n` +
               (this.session.last_activity ?
                `Last Activity: ${new Date(this.session.last_activity).toLocaleString()}` : '');
    }

    private createDescription(): string {
        const agentCount = this.session.agents.length;
        const convCount = this.session.conversation_count;
        return `${agentCount} agents, ${convCount} conversations`;
    }

    private getIconPath(): vscode.ThemeIcon {
        switch (this.session.status) {
            case 'active':
                return new vscode.ThemeIcon('play-circle', new vscode.ThemeColor('testing.iconPassed'));
            case 'stopped':
                return new vscode.ThemeIcon('stop-circle', new vscode.ThemeColor('testing.iconFailed'));
            case 'error':
                return new vscode.ThemeIcon('error', new vscode.ThemeColor('testing.iconErrored'));
            default:
                return new vscode.ThemeIcon('circle-outline');
        }
    }
}

export class AgentTreeItem extends vscode.TreeItem {
    constructor(
        public readonly agentName: string,
        public readonly sessionId: string
    ) {
        super(agentName, vscode.TreeItemCollapsibleState.None);

        this.tooltip = `Agent: ${agentName}`;
        this.contextValue = 'agent';
        this.iconPath = new vscode.ThemeIcon('person');

        this.command = {
            command: 'autogen.viewAgentDetails',
            title: 'View Agent Details',
            arguments: [sessionId, agentName]
        };
    }
}

export class SessionTreeProvider implements vscode.TreeDataProvider<SessionTreeItem | AgentTreeItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<SessionTreeItem | AgentTreeItem | undefined | null | void> = new vscode.EventEmitter<SessionTreeItem | AgentTreeItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<SessionTreeItem | AgentTreeItem | undefined | null | void> = this._onDidChangeTreeData.event;

    private sessions: SessionData[] = [];

    constructor(private mcpClient: McpClient) {
        this.refreshSessions();
    }

    refresh(): void {
        this.refreshSessions();
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: SessionTreeItem | AgentTreeItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: SessionTreeItem | AgentTreeItem): Thenable<(SessionTreeItem | AgentTreeItem)[]> {
        if (!element) {
            // Root level - return sessions
            return Promise.resolve(this.getSessions());
        } else if (element instanceof SessionTreeItem) {
            // Session level - return agents
            return Promise.resolve(this.getAgents(element.session));
        } else {
            // Agent level - no children
            return Promise.resolve([]);
        }
    }

    private getSessions(): SessionTreeItem[] {
        return this.sessions.map(session => {
            const hasAgents = session.agents.length > 0;
            const collapsibleState = hasAgents ?
                vscode.TreeItemCollapsibleState.Collapsed :
                vscode.TreeItemCollapsibleState.None;

            return new SessionTreeItem(session, collapsibleState);
        });
    }

    private getAgents(session: SessionData): AgentTreeItem[] {
        return session.agents.map(agentName =>
            new AgentTreeItem(agentName, session.id)
        );
    }

    private async refreshSessions(): Promise<void> {
        try {
            // Check if server is available
            const isConnected = await this.mcpClient.isServerAvailable();
            if (!isConnected) {
                this.sessions = [];
                return;
            }

            // Fetch sessions from MCP server
            const sessionInfos = await this.mcpClient.listSessions();
            this.sessions = sessionInfos.map((sessionInfo) => ({
                id: sessionInfo.session_id,
                name: sessionInfo.project || `Session ${sessionInfo.session_id}`,
                status: sessionInfo.status as 'active' | 'stopped' | 'error',
                created_at: sessionInfo.created_at,
                last_activity: undefined, // Not available in current API
                agents: sessionInfo.agents,
                conversation_count: 0, // Not available in current API
                memory_count: 0 // Not available in current API
            }));
        } catch (error) {
            console.warn('Failed to fetch sessions:', error);
            this.sessions = [];
        }
    }

    // Public method to get session by ID
    getSession(sessionId: string): SessionData | undefined {
        return this.sessions.find(session => session.id === sessionId);
    }

    // Public method to get all sessions
    getAllSessions(): SessionData[] {
        return [...this.sessions];
    }
}

import * as vscode from 'vscode';

export interface OrchestrationRequest {
    project: string;
    agents: string[];
    objective: string;
}

export interface OrchestrationResponse {
    session_id: string;
    status: string;
    message: string;
}

export interface MemorySearchRequest {
    query: string;
    scope: string;
    k: number;
}

export interface MemorySearchResponse {
    results: Array<{
        content: string;
        score: number;
        metadata: any;
    }>;
}

export interface ObjectiveRequest {
    objective: string;
    project: string;
}

export class McpClient {
    constructor(public readonly serverUrl: string) {}

    async startOrchestration(request: OrchestrationRequest): Promise<OrchestrationResponse> {
        const response = await fetch(`${this.serverUrl}/orchestrate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(request)
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    }

    async searchMemory(request: MemorySearchRequest): Promise<MemorySearchResponse> {
        const params = new URLSearchParams({
            query: request.query,
            scope: request.scope,
            k: request.k.toString()
        });

        const response = await fetch(`${this.serverUrl}/memory/search?${params}`);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    }

    async addObjective(request: ObjectiveRequest): Promise<{ status: string }> {
        const response = await fetch(`${this.serverUrl}/objectives`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(request)
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    }

    async getHealth(): Promise<{ status: string }> {
        const response = await fetch(`${this.serverUrl}/health`);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    }
}

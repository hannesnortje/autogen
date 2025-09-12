import * as vscode from 'vscode';

export interface OrchestrationRequest {
    project: string;
    agents: string[];
    objective: string;
}

export interface OrchestrationResponse {
    session_id: string;
    status: string;
    message?: string;
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

export interface SessionInfo {
    session_id: string;
    project: string;
    status: string;
    agents: string[];
    created_at: string;
}

export interface SessionsResponse {
    sessions: SessionInfo[];
}

export interface StopSessionRequest {
    session_id: string;
}

export class McpServerError extends Error {
    constructor(
        message: string,
        public statusCode?: number,
        public response?: any
    ) {
        super(message);
        this.name = 'McpServerError';
    }
}

export class McpClient {
    private currentSessionId: string | null = null;

    constructor(public readonly serverUrl: string) {}

    async isServerAvailable(): Promise<boolean> {
        try {
            await this.getHealth();
            return true;
        } catch (error) {
            return false;
        }
    }

    getCurrentSessionId(): string | null {
        return this.currentSessionId;
    }

    setCurrentSessionId(sessionId: string | null): void {
        this.currentSessionId = sessionId;
    }

    private async makeRequest<T>(
        endpoint: string,
        options: RequestInit = {}
    ): Promise<T> {
        try {
            const url = `${this.serverUrl}${endpoint}`;
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers,
                },
            });

            if (!response.ok) {
                let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
                try {
                    const errorBody = await response.json();
                    if (errorBody.detail) {
                        errorMessage = errorBody.detail;
                    } else if (errorBody.message) {
                        errorMessage = errorBody.message;
                    }
                } catch (e) {
                    // Use default error message if JSON parsing fails
                }
                throw new McpServerError(errorMessage, response.status);
            }

            return await response.json();
        } catch (error) {
            if (error instanceof McpServerError) {
                throw error;
            }
            // Handle network errors, timeouts, etc.
            const message = error instanceof Error ? error.message : 'Unknown error';
            throw new McpServerError(
                `Failed to connect to MCP server at ${this.serverUrl}: ${message}`
            );
        }
    }

    async startOrchestration(request: OrchestrationRequest): Promise<OrchestrationResponse> {
        const response = await this.makeRequest<OrchestrationResponse>('/orchestrate/start', {
            method: 'POST',
            body: JSON.stringify(request)
        });

        // Store the session ID for future operations
        if (response.session_id) {
            this.setCurrentSessionId(response.session_id);
        }

        return response;
    }

    async stopSession(sessionId?: string): Promise<{ status: string; message: string }> {
        const targetSessionId = sessionId || this.currentSessionId;
        if (!targetSessionId) {
            throw new McpServerError('No active session to stop');
        }

        const request: StopSessionRequest = { session_id: targetSessionId };
        const response = await this.makeRequest<{ status: string; message: string }>('/orchestrate/stop', {
            method: 'POST',
            body: JSON.stringify(request)
        });

        // Clear current session if we stopped it
        if (targetSessionId === this.currentSessionId) {
            this.setCurrentSessionId(null);
        }

        return response;
    }

    async searchMemory(request: MemorySearchRequest): Promise<MemorySearchResponse> {
        const params = new URLSearchParams({
            query: request.query,
            scope: request.scope,
            k: request.k.toString()
        });

        return await this.makeRequest<MemorySearchResponse>(`/memory/search?${params}`);
    }

    async addObjective(request: ObjectiveRequest): Promise<{ status: string }> {
        return await this.makeRequest<{ status: string }>('/objectives', {
            method: 'POST',
            body: JSON.stringify(request)
        });
    }

    async getSessionInfo(sessionId?: string): Promise<SessionInfo> {
        const targetSessionId = sessionId || this.currentSessionId;
        if (!targetSessionId) {
            throw new McpServerError('No session ID provided');
        }

        return await this.makeRequest<SessionInfo>(`/orchestrate/session/${targetSessionId}`);
    }

    async listSessions(): Promise<SessionInfo[]> {
        const resp = await this.makeRequest<SessionsResponse>('/orchestrate/sessions');
        return resp.sessions || [];
    }

    async getHealth(): Promise<{ status: string }> {
        return await this.makeRequest<{ status: string }>('/health');
    }
}

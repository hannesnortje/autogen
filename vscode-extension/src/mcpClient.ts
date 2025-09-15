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

// Memory Analytics Interfaces
export interface MemoryAnalyticsReport {
    system_overview: {
        total_entries: number;
        total_size_bytes: number;
        collections_count: number;
        average_entry_size: number;
    };
    scope_breakdown: {
        [scope: string]: {
            entries: number;
            size_bytes: number;
            last_accessed: string;
        };
    };
    usage_patterns: {
        read_operations: number;
        write_operations: number;
        search_operations: number;
        cache_hit_ratio: number;
    };
    performance_metrics: {
        average_read_time: number;
        average_write_time: number;
        average_search_time: number;
        slow_operations_count: number;
    };
    health_indicators: {
        status: string;
        memory_usage_percentage: number;
        fragmentation_level: number;
        optimization_score: number;
    };
}

export interface MemoryHealthStatus {
    status: 'healthy' | 'warning' | 'critical' | 'error';
    overall_score: number;
    indicators: {
        storage_usage: {
            status: string;
            value: number;
            threshold: number;
            message: string;
        };
        performance: {
            status: string;
            value: number;
            threshold: number;
            message: string;
        };
        fragmentation: {
            status: string;
            value: number;
            threshold: number;
            message: string;
        };
        access_patterns: {
            status: string;
            value: number;
            threshold: number;
            message: string;
        };
    };
    recommendations: string[];
}

export interface MemoryOptimizationRequest {
    strategy: 'lru' | 'importance' | 'frequency' | 'hybrid';
    scope?: string;
    dry_run?: boolean;
    max_removals?: number;
}

export interface MemoryOptimizationResult {
    strategy_used: string;
    entries_removed: number;
    space_freed_bytes: number;
    optimization_time: number;
    dry_run: boolean;
    removed_entries?: Array<{
        id: string;
        content_preview: string;
        removal_reason: string;
        last_accessed: string;
    }>;
}

export interface MemoryMetrics {
    timestamp: string;
    storage: {
        total_entries: number;
        total_size_bytes: number;
        collections_count: number;
        average_entry_size: number;
    };
    performance: {
        operations_per_minute: number;
        average_response_time: number;
        cache_hit_ratio: number;
        error_rate: number;
    };
    health: {
        memory_usage_percentage: number;
        fragmentation_level: number;
        optimization_score: number;
        last_optimization: string;
    };
}

// Cross-Project Learning Interfaces
export interface ProjectRegistration {
    name: string;
    description: string;
    tech_stack: string[];
    domain: string;
    patterns_used?: string[];
    success_metrics?: { [key: string]: number };
}

export interface ProjectRecommendationsRequest {
    current_project: {
        name: string;
        description?: string;
        tech_stack: string[];
        domain: string;
        current_challenge?: string;
    };
    recommendation_types: string[];
    max_recommendations?: number;
}

export interface ProjectRecommendation {
    type: 'solution' | 'pattern' | 'best_practice' | 'similar_project';
    title: string;
    description: string;
    source_project: string;
    relevance_score: number;
    implementation_guide: string;
    tags: string[];
    success_metrics?: { [key: string]: number };
}

export interface ProjectRecommendationsResponse {
    recommendations: ProjectRecommendation[];
    similar_projects: Array<{
        name: string;
        similarity_score: number;
        shared_patterns: string[];
        tech_overlap: string[];
    }>;
}

export interface CrossProjectAnalysis {
    total_projects: number;
    pattern_frequency: { [pattern: string]: number };
    tech_stack_distribution: { [tech: string]: number };
    domain_distribution: { [domain: string]: number };
    success_patterns: Array<{
        pattern: string;
        success_rate: number;
        projects_count: number;
        average_metrics: { [key: string]: number };
    }>;
    emerging_trends: Array<{
        trend: string;
        growth_rate: number;
        adoption_count: number;
        description: string;
    }>;
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

    // Memory Analytics Methods
    async getMemoryAnalyticsReport(): Promise<MemoryAnalyticsReport> {
        return await this.makeRequest<MemoryAnalyticsReport>('/memory/analytics/report');
    }

    async getMemoryHealth(): Promise<MemoryHealthStatus> {
        return await this.makeRequest<MemoryHealthStatus>('/memory/analytics/health');
    }

    async optimizeMemory(request: MemoryOptimizationRequest): Promise<MemoryOptimizationResult> {
        return await this.makeRequest<MemoryOptimizationResult>('/memory/analytics/optimize', {
            method: 'POST',
            body: JSON.stringify(request)
        });
    }

    async getMemoryMetrics(): Promise<MemoryMetrics> {
        return await this.makeRequest<MemoryMetrics>('/memory/analytics/metrics');
    }

    // Cross-Project Learning Methods
    async registerProject(request: ProjectRegistration): Promise<{ status: string; project_id: string }> {
        return await this.makeRequest<{ status: string; project_id: string }>('/cross-project/register', {
            method: 'POST',
            body: JSON.stringify(request)
        });
    }

    async getProjectRecommendations(request: ProjectRecommendationsRequest): Promise<ProjectRecommendationsResponse> {
        return await this.makeRequest<ProjectRecommendationsResponse>('/cross-project/recommendations', {
            method: 'POST',
            body: JSON.stringify(request)
        });
    }

    async getCrossProjectAnalysis(): Promise<CrossProjectAnalysis> {
        return await this.makeRequest<CrossProjectAnalysis>('/cross-project/analysis');
    }
}

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
    private retryAttempts: number = 3;
    private retryDelay: number = 1000; // 1 second
    private requestTimeout: number = 30000; // 30 seconds
    private requestCache: Map<string, { data: any; timestamp: number; ttl: number }> = new Map();

    constructor(public readonly serverUrl: string) {
        // Clear expired cache entries every 5 minutes
        setInterval(() => this.clearExpiredCache(), 5 * 60 * 1000);
    }

    private clearExpiredCache(): void {
        const now = Date.now();
        for (const [key, entry] of this.requestCache.entries()) {
            if (now - entry.timestamp > entry.ttl) {
                this.requestCache.delete(key);
            }
        }
    }

    private getCacheKey(endpoint: string, options: RequestInit): string {
        const method = options.method || 'GET';
        const body = options.body || '';
        return `${method}:${endpoint}:${body}`;
    }

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
        options: RequestInit = {},
        retryAttempts?: number,
        cacheTtl?: number
    ): Promise<T> {
        const attempts = retryAttempts ?? this.retryAttempts;
        const cacheKey = this.getCacheKey(endpoint, options);

        // Check cache for GET requests
        if ((!options.method || options.method === 'GET') && cacheTtl && this.requestCache.has(cacheKey)) {
            const cached = this.requestCache.get(cacheKey)!;
            if (Date.now() - cached.timestamp < cached.ttl) {
                return cached.data;
            }
            this.requestCache.delete(cacheKey);
        }

        let lastError: Error | null = null;

        for (let attempt = 0; attempt < attempts; attempt++) {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), this.requestTimeout);

                const url = `${this.serverUrl}${endpoint}`;
                const response = await fetch(url, {
                    ...options,
                    signal: controller.signal,
                    headers: {
                        'Content-Type': 'application/json',
                        ...options.headers,
                    },
                });

                clearTimeout(timeoutId);

                if (!response.ok) {
                    let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
                    try {
                        const errorBody = await response.json();
                        if (errorBody && typeof errorBody === 'object' && 'detail' in errorBody && typeof (errorBody as any).detail === 'string') {
                            errorMessage = (errorBody as any).detail;
                        } else if (errorBody && typeof errorBody === 'object' && 'message' in errorBody && typeof (errorBody as any).message === 'string') {
                            errorMessage = (errorBody as any).message;
                        }
                    } catch (e) {
                        // Use default error message if JSON parsing fails
                    }

                    // Don't retry for client errors (4xx), only server errors (5xx) and network issues
                    if (response.status >= 400 && response.status < 500) {
                        throw new McpServerError(errorMessage, response.status);
                    }

                    lastError = new McpServerError(errorMessage, response.status);

                    // Wait before retrying (exponential backoff)
                    if (attempt < attempts - 1) {
                        await new Promise(resolve => setTimeout(resolve, this.retryDelay * Math.pow(2, attempt)));
                        continue;
                    }
                    throw lastError;
                }

                const data = await response.json();

                // Cache successful GET requests
                if ((!options.method || options.method === 'GET') && cacheTtl) {
                    this.requestCache.set(cacheKey, {
                        data,
                        timestamp: Date.now(),
                        ttl: cacheTtl
                    });
                }

                return data as T;
            } catch (error) {
                if (error instanceof McpServerError) {
                    lastError = error;
                } else {
                    // Handle network errors, timeouts, etc.
                    const message = error instanceof Error ? error.message : 'Unknown error';
                    lastError = new McpServerError(
                        `Failed to connect to MCP server at ${this.serverUrl}: ${message}`
                    );
                }

                // Don't retry for certain error types
                if (error instanceof Error &&
                    (error.name === 'AbortError' ||
                     error.message.includes('Failed to fetch') ||
                     error.message.includes('NetworkError'))) {

                    // Wait before retrying network errors (exponential backoff)
                    if (attempt < attempts - 1) {
                        await new Promise(resolve => setTimeout(resolve, this.retryDelay * Math.pow(2, attempt)));
                        continue;
                    }
                }

                throw lastError;
            }
        }

        throw lastError || new McpServerError('Request failed after all retry attempts');
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

        // Cache session info for 1 minute
        return await this.makeRequest<SessionInfo>(`/orchestrate/session/${targetSessionId}`, {}, undefined, 60 * 1000);
    }

    async listSessions(): Promise<SessionInfo[]> {
        // Cache session list for 30 seconds
        const resp = await this.makeRequest<SessionsResponse>('/orchestrate/sessions', {}, undefined, 30 * 1000);
        return resp.sessions || [];
    }

    async getHealth(): Promise<{ status: string }> {
        // Cache health status for 15 seconds
        return await this.makeRequest<{ status: string }>('/health', {}, undefined, 15 * 1000);
    }

    // Memory Analytics Methods
    async getMemoryAnalyticsReport(): Promise<MemoryAnalyticsReport> {
        // Cache for 2 minutes since analytics data changes relatively slowly
        return await this.makeRequest<MemoryAnalyticsReport>('/memory/analytics/report', {}, undefined, 2 * 60 * 1000);
    }

    async getMemoryHealth(): Promise<MemoryHealthStatus> {
        // Cache for 30 seconds for health status
        return await this.makeRequest<MemoryHealthStatus>('/memory/analytics/health', {}, undefined, 30 * 1000);
    }

    async optimizeMemory(request: MemoryOptimizationRequest): Promise<MemoryOptimizationResult> {
        // No caching for optimization requests (POST operations)
        return await this.makeRequest<MemoryOptimizationResult>('/memory/analytics/optimize', {
            method: 'POST',
            body: JSON.stringify(request)
        });
    }

    async getMemoryMetrics(): Promise<MemoryMetrics> {
        // Cache for 1 minute since metrics update frequently
        return await this.makeRequest<MemoryMetrics>('/memory/analytics/metrics', {}, undefined, 60 * 1000);
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
        // Cache cross-project analysis for 5 minutes since it's computationally expensive
        return await this.makeRequest<CrossProjectAnalysis>('/cross-project/analysis', {}, undefined, 5 * 60 * 1000);
    }

    // Helper methods for caching and retry logic
    private cleanupCache(): void {
        const now = Date.now();
        for (const [key, cached] of this.requestCache.entries()) {
            if (now - cached.timestamp >= cached.ttl) {
                this.requestCache.delete(key);
            }
        }
    }

    // Public method to manually clear cache if needed
    public clearCache(): void {
        this.requestCache.clear();
    }
}

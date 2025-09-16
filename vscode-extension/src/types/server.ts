/**
 * Server connection and management type definitions for AutoGen VS Code Extension
 */

/**
 * Server connection states
 */
export enum ServerStatus {
    DISCONNECTED = 'disconnected',
    CONNECTING = 'connecting',
    CONNECTED = 'connected',
    RECONNECTING = 'reconnecting',
    ERROR = 'error',
    STARTING = 'starting',
    STOPPING = 'stopping'
}

/**
 * Server types supported by the extension
 */
export enum ServerType {
    LOCAL = 'local',
    REMOTE = 'remote'
}

/**
 * Server health check response structure
 */
export interface HealthCheckResponse {
    status: 'healthy' | 'unhealthy' | 'degraded';
    timestamp: Date;
    version?: string;
    uptime?: number;
    memory?: {
        used: number;
        total: number;
        percentage: number;
    };
    connections?: {
        active: number;
        total: number;
    };
    services?: {
        memory: boolean;
        sessions: boolean;
        agents: boolean;
    };
    errors?: string[];
}

/**
 * Server configuration options
 */
export interface ServerConfig {
    /** Server URL (e.g., http://localhost:9000) */
    url: string;
    /** Server type (local or remote) */
    type: ServerType;
    /** Port number */
    port: number;
    /** Host address */
    host: string;
    /** Path to local server executable (for local servers) */
    serverPath?: string;
    /** Auto-start server if not running */
    autoStart: boolean;
    /** Health check interval in milliseconds */
    healthCheckInterval: number;
    /** Connection timeout in milliseconds */
    connectionTimeout: number;
    /** Maximum retry attempts */
    maxRetries: number;
    /** Retry delay in milliseconds */
    retryDelay: number;
    /** Enable debug logging */
    debug: boolean;
}

/**
 * Server connection information
 */
export interface ServerConnection {
    /** Unique connection ID */
    id: string;
    /** Server configuration */
    config: ServerConfig;
    /** Current connection status */
    status: ServerStatus;
    /** Connection established timestamp */
    connectedAt?: Date;
    /** Last successful health check timestamp */
    lastHealthCheck?: Date;
    /** Last error encountered */
    lastError?: ServerError;
    /** Number of retry attempts */
    retryCount: number;
    /** Process ID for local servers */
    processId?: number;
}

/**
 * Server error information
 */
export interface ServerError {
    /** Error code */
    code: string;
    /** Error message */
    message: string;
    /** Error timestamp */
    timestamp: Date;
    /** Additional error details */
    details?: Record<string, unknown>;
    /** Whether the error is recoverable */
    recoverable: boolean;
}

/**
 * Server event types
 */
export enum ServerEventType {
    STATUS_CHANGED = 'status-changed',
    HEALTH_CHECK = 'health-check',
    CONNECTION_ESTABLISHED = 'connection-established',
    CONNECTION_LOST = 'connection-lost',
    ERROR = 'error',
    RETRY_ATTEMPT = 'retry-attempt',
    SERVER_STARTED = 'server-started',
    SERVER_STOPPED = 'server-stopped'
}

/**
 * Server event data structure
 */
export interface ServerEvent {
    /** Event type */
    type: ServerEventType;
    /** Event timestamp */
    timestamp: Date;
    /** Server connection ID */
    connectionId: string;
    /** Event-specific data */
    data: Record<string, unknown>;
}

/**
 * Server manager interface for managing AutoGen server connections
 */
export interface IServerManager {
    /**
     * Get current server connection
     */
    getConnection(): ServerConnection | null;

    /**
     * Connect to the server
     */
    connect(config?: Partial<ServerConfig>): Promise<ServerConnection>;

    /**
     * Disconnect from the server
     */
    disconnect(): Promise<void>;

    /**
     * Start the local server (if applicable)
     */
    startServer(): Promise<void>;

    /**
     * Stop the local server (if applicable)
     */
    stopServer(): Promise<void>;

    /**
     * Restart the server connection
     */
    restart(): Promise<ServerConnection>;

    /**
     * Perform health check
     */
    healthCheck(): Promise<HealthCheckResponse>;

    /**
     * Get current server status
     */
    getStatus(): ServerStatus;

    /**
     * Check if server is connected and healthy
     */
    isHealthy(): boolean;

    /**
     * Update server configuration
     */
    updateConfig(config: Partial<ServerConfig>): void;

    /**
     * Get current server configuration
     */
    getConfig(): ServerConfig;

    /**
     * Add event listener
     */
    on(event: ServerEventType, listener: (event: ServerEvent) => void): void;

    /**
     * Remove event listener
     */
    off(event: ServerEventType, listener: (event: ServerEvent) => void): void;

    /**
     * Dispose of the server manager and cleanup resources
     */
    dispose(): void;
}

/**
 * Server validation result
 */
export interface ServerValidationResult {
    /** Whether the server configuration is valid */
    valid: boolean;
    /** Validation errors */
    errors: string[];
    /** Validation warnings */
    warnings: string[];
}

/**
 * Server metrics for monitoring
 */
export interface ServerMetrics {
    /** Connection uptime in milliseconds */
    uptime: number;
    /** Number of successful health checks */
    healthChecks: number;
    /** Number of failed health checks */
    failedHealthChecks: number;
    /** Number of reconnection attempts */
    reconnections: number;
    /** Average response time in milliseconds */
    averageResponseTime: number;
    /** Last response time in milliseconds */
    lastResponseTime: number;
    /** Total bytes sent */
    bytesSent: number;
    /** Total bytes received */
    bytesReceived: number;
}

/**
 * Default server configuration
 */
export const DEFAULT_SERVER_CONFIG: ServerConfig = {
    url: 'http://localhost:9000',
    type: ServerType.LOCAL,
    port: 9000,
    host: 'localhost',
    autoStart: true,
    healthCheckInterval: 30000, // 30 seconds
    connectionTimeout: 10000, // 10 seconds
    maxRetries: 3,
    retryDelay: 2000, // 2 seconds
    debug: false
};

/**
 * Common server error codes
 */
export enum ServerErrorCode {
    CONNECTION_FAILED = 'CONNECTION_FAILED',
    CONNECTION_TIMEOUT = 'CONNECTION_TIMEOUT',
    HEALTH_CHECK_FAILED = 'HEALTH_CHECK_FAILED',
    SERVER_START_FAILED = 'SERVER_START_FAILED',
    SERVER_STOP_FAILED = 'SERVER_STOP_FAILED',
    INVALID_CONFIG = 'INVALID_CONFIG',
    NETWORK_ERROR = 'NETWORK_ERROR',
    SERVER_UNREACHABLE = 'SERVER_UNREACHABLE',
    AUTHENTICATION_FAILED = 'AUTHENTICATION_FAILED',
    PERMISSION_DENIED = 'PERMISSION_DENIED',
    SERVICE_UNAVAILABLE = 'SERVICE_UNAVAILABLE'
}

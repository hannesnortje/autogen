import * as vscode from 'vscode';
import { spawn, ChildProcess } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';
import {
    IServerManager,
    ServerConfig,
    ServerConnection,
    ServerStatus,
    ServerEvent,
    ServerEventType,
    HealthCheckResponse,
    ServerError,
    ServerErrorCode,
    ServerType,
    ServerMetrics,
    DEFAULT_SERVER_CONFIG
} from '../types/server';

/**
 * ServerManager handles AutoGen MCP server connections, health monitoring,
 * and local server lifecycle management.
 */
export class ServerManager implements IServerManager {
    private connection: ServerConnection | null = null;
    private config: ServerConfig;
    private healthCheckTimer: NodeJS.Timeout | null = null;
    private reconnectTimer: NodeJS.Timeout | null = null;
    private serverProcess: ChildProcess | null = null;
    private eventEmitter = new vscode.EventEmitter<ServerEvent>();
    private disposables: vscode.Disposable[] = [];
    private metrics: ServerMetrics = {
        uptime: 0,
        healthChecks: 0,
        failedHealthChecks: 0,
        reconnections: 0,
        averageResponseTime: 0,
        lastResponseTime: 0,
        bytesSent: 0,
        bytesReceived: 0
    };

    constructor(initialConfig?: Partial<ServerConfig>) {
        this.config = { ...DEFAULT_SERVER_CONFIG, ...initialConfig };
        this.loadConfigFromSettings();

        // Listen for configuration changes
        this.disposables.push(
            vscode.workspace.onDidChangeConfiguration((e) => {
                if (e.affectsConfiguration('autogen.server')) {
                    this.loadConfigFromSettings();
                }
            })
        );
    }

    /**
     * Load server configuration from VS Code settings
     */
    private loadConfigFromSettings(): void {
        const config = vscode.workspace.getConfiguration('autogen.server');
        const url = config.get<string>('url') || DEFAULT_SERVER_CONFIG.url;
        const urlObj = new URL(url);

        this.config = {
            ...this.config,
            url,
            host: urlObj.hostname,
            port: parseInt(urlObj.port) || DEFAULT_SERVER_CONFIG.port,
            autoStart: config.get<boolean>('autoStart') ?? DEFAULT_SERVER_CONFIG.autoStart,
            serverPath: config.get<string>('path'),
            healthCheckInterval: config.get<number>('healthCheckInterval') || DEFAULT_SERVER_CONFIG.healthCheckInterval,
            connectionTimeout: config.get<number>('connectionTimeout') || DEFAULT_SERVER_CONFIG.connectionTimeout,
            maxRetries: config.get<number>('maxRetries') || DEFAULT_SERVER_CONFIG.maxRetries,
            retryDelay: config.get<number>('retryDelay') || DEFAULT_SERVER_CONFIG.retryDelay,
            debug: config.get<boolean>('debug') ?? DEFAULT_SERVER_CONFIG.debug,
            type: url.includes('localhost') || url.includes('127.0.0.1') ? ServerType.LOCAL : ServerType.REMOTE
        };
    }

    /**
     * Get current server connection
     */
    getConnection(): ServerConnection | null {
        return this.connection;
    }

    /**
     * Connect to the server
     */
    async connect(config?: Partial<ServerConfig>): Promise<ServerConnection> {
        if (config) {
            this.updateConfig(config);
        }

        // If already connected, return existing connection
        if (this.connection && this.connection.status === ServerStatus.CONNECTED) {
            return this.connection;
        }

        // Create new connection
        this.connection = {
            id: this.generateConnectionId(),
            config: this.config,
            status: ServerStatus.CONNECTING,
            retryCount: 0
        };

        this.emitEvent(ServerEventType.STATUS_CHANGED, {
            status: ServerStatus.CONNECTING,
            connectionId: this.connection.id
        });

        try {
            // Try to connect to existing server first
            const healthCheck = await this.performHealthCheck();

            if (healthCheck.status === 'healthy') {
                this.connection.status = ServerStatus.CONNECTED;
                this.connection.connectedAt = new Date();
                this.connection.lastHealthCheck = new Date();
                this.startHealthCheckMonitoring();

                this.emitEvent(ServerEventType.CONNECTION_ESTABLISHED, {
                    connectionId: this.connection.id,
                    healthCheck
                });

                return this.connection;
            }
        } catch (error) {
            this.log(`Initial connection failed: ${error}`);
        }

        // If connection failed and auto-start is enabled, try to start server
        if (this.config.autoStart && this.config.type === ServerType.LOCAL) {
            try {
                await this.startServer();

                // Wait a bit for server to start up
                await this.delay(2000);

                // Try connecting again
                const healthCheck = await this.performHealthCheck();
                if (healthCheck.status === 'healthy') {
                    this.connection.status = ServerStatus.CONNECTED;
                    this.connection.connectedAt = new Date();
                    this.connection.lastHealthCheck = new Date();
                    this.startHealthCheckMonitoring();

                    this.emitEvent(ServerEventType.CONNECTION_ESTABLISHED, {
                        connectionId: this.connection.id,
                        healthCheck
                    });

                    return this.connection;
                }
            } catch (startError) {
                this.log(`Failed to start server: ${startError}`);
            }
        }

        // Connection failed
        this.connection.status = ServerStatus.ERROR;
        this.connection.lastError = {
            code: ServerErrorCode.CONNECTION_FAILED,
            message: 'Unable to connect to AutoGen server',
            timestamp: new Date(),
            recoverable: true
        };

        this.emitEvent(ServerEventType.ERROR, {
            connectionId: this.connection.id,
            error: this.connection.lastError
        });

        throw new Error(`Failed to connect to server at ${this.config.url}`);
    }

    /**
     * Disconnect from the server
     */
    async disconnect(): Promise<void> {
        if (!this.connection) {
            return;
        }

        this.stopHealthCheckMonitoring();
        this.stopReconnectTimer();

        const wasConnected = this.connection.status === ServerStatus.CONNECTED;
        this.connection.status = ServerStatus.DISCONNECTED;

        if (wasConnected) {
            this.emitEvent(ServerEventType.CONNECTION_LOST, {
                connectionId: this.connection.id,
                reason: 'Manual disconnect'
            });
        }

        this.emitEvent(ServerEventType.STATUS_CHANGED, {
            status: ServerStatus.DISCONNECTED,
            connectionId: this.connection.id
        });

        this.connection = null;
    }

    /**
     * Start the local server
     */
    async startServer(): Promise<void> {
        if (this.config.type !== ServerType.LOCAL) {
            throw new Error('Cannot start remote server');
        }

        if (this.serverProcess) {
            this.log('Server process already running');
            return;
        }

        const projectPath = this.config.serverPath || this.findServerPath();
        if (!projectPath) {
            throw new Error('AutoGen server path not configured. Set autogen.server.path');
        }

        if (!fs.existsSync(projectPath)) {
            throw new Error(`AutoGen project path not found: ${projectPath}`);
        }
        // Ensure pyproject exists as a sanity check
        const pyproject = path.join(projectPath, 'pyproject.toml');
        if (!fs.existsSync(pyproject)) {
            this.log(`Warning: pyproject.toml not found in ${projectPath}. Continuing regardless.`);
        }

        return new Promise((resolve, reject) => {
            this.emitEvent(ServerEventType.STATUS_CHANGED, {
                status: ServerStatus.STARTING,
                connectionId: this.connection?.id || 'unknown'
            });

            // Start server process via Poetry
            const command = process.platform === 'win32' ? 'poetry.exe' : 'poetry';
            const args = ['run', 'python', '-m', 'src.autogen_mcp.mcp_server', `--port=${this.config.port}`];
            this.log(`Starting server: ${command} ${args.join(' ')} (cwd=${projectPath})`);
            this.serverProcess = spawn(command, args, {
                cwd: projectPath,
                detached: false,
                stdio: this.config.debug ? 'pipe' : 'ignore'
            });

            if (this.config.debug && this.serverProcess.stdout && this.serverProcess.stderr) {
                this.serverProcess.stdout.on('data', (data) => {
                    this.log(`Server stdout: ${data.toString()}`);
                });

                this.serverProcess.stderr.on('data', (data) => {
                    this.log(`Server stderr: ${data.toString()}`);
                });
            }

            this.serverProcess.on('error', (error) => {
                this.log(`Server process error: ${error.message}`);
                this.serverProcess = null;
                reject(new Error(`Failed to start server: ${error.message}`));
            });

            this.serverProcess.on('exit', (code, signal) => {
                this.log(`Server process exited with code ${code}, signal ${signal}`);
                this.serverProcess = null;

                if (this.connection) {
                    this.connection.processId = undefined;
                }

                this.emitEvent(ServerEventType.SERVER_STOPPED, {
                    connectionId: this.connection?.id || 'unknown',
                    exitCode: code,
                    signal
                });
            });

            // Store process ID
            if (this.connection) {
                this.connection.processId = this.serverProcess.pid;
            }

            this.emitEvent(ServerEventType.SERVER_STARTED, {
                connectionId: this.connection?.id || 'unknown',
                processId: this.serverProcess.pid
            });

            // Server started successfully
            setTimeout(() => resolve(), 1000);
        });
    }

    /**
     * Stop the local server
     */
    async stopServer(): Promise<void> {
        if (!this.serverProcess) {
            return;
        }

        return new Promise((resolve) => {
            this.emitEvent(ServerEventType.STATUS_CHANGED, {
                status: ServerStatus.STOPPING,
                connectionId: this.connection?.id || 'unknown'
            });

            const process = this.serverProcess!;
            this.serverProcess = null;

            // Try graceful shutdown first
            process.kill('SIGTERM');

            // Force kill after timeout
            const killTimer = setTimeout(() => {
                if (!process.killed) {
                    process.kill('SIGKILL');
                }
            }, 5000);

            process.on('exit', () => {
                clearTimeout(killTimer);
                resolve();
            });
        });
    }

    /**
     * Restart the server connection
     */
    async restart(): Promise<ServerConnection> {
        await this.disconnect();

        if (this.config.type === ServerType.LOCAL && this.serverProcess) {
            await this.stopServer();
            await this.delay(1000);
        }

        return this.connect();
    }

    /**
     * Perform health check
     */
    async healthCheck(): Promise<HealthCheckResponse> {
        return this.performHealthCheck();
    }

    /**
     * Internal health check implementation
     */
    private async performHealthCheck(): Promise<HealthCheckResponse> {
        const startTime = Date.now();

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.config.connectionTimeout);

            const response = await fetch(`${this.config.url}/health`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                },
                signal: controller.signal
            });

            clearTimeout(timeoutId);
            const responseTime = Date.now() - startTime;

            // Update metrics
            this.metrics.lastResponseTime = responseTime;
            this.metrics.healthChecks++;
            this.updateAverageResponseTime(responseTime);

            if (!response.ok) {
                throw new Error(`Health check failed with status: ${response.status}`);
            }

            const data = await response.json();
            const healthCheck: HealthCheckResponse = {
                status: 'healthy',
                timestamp: new Date(),
                ...(data && typeof data === 'object' ? data : {})
            };

            if (this.connection) {
                this.connection.lastHealthCheck = new Date();
            }

            this.emitEvent(ServerEventType.HEALTH_CHECK, {
                connectionId: this.connection?.id || 'unknown',
                healthCheck,
                responseTime
            });

            return healthCheck;

        } catch (error) {
            this.metrics.failedHealthChecks++;

            const healthCheck: HealthCheckResponse = {
                status: 'unhealthy',
                timestamp: new Date(),
                errors: [error instanceof Error ? error.message : String(error)]
            };

            if (this.connection) {
                this.connection.lastError = {
                    code: ServerErrorCode.HEALTH_CHECK_FAILED,
                    message: error instanceof Error ? error.message : String(error),
                    timestamp: new Date(),
                    recoverable: true
                };
            }

            this.emitEvent(ServerEventType.HEALTH_CHECK, {
                connectionId: this.connection?.id || 'unknown',
                healthCheck,
                error
            });

            throw error;
        }
    }

    /**
     * Get current server status
     */
    getStatus(): ServerStatus {
        return this.connection?.status || ServerStatus.DISCONNECTED;
    }

    /**
     * Check if server is connected and healthy
     */
    isHealthy(): boolean {
        if (!this.connection || this.connection.status !== ServerStatus.CONNECTED) {
            return false;
        }

        if (!this.connection.lastHealthCheck) {
            return false;
        }

        return (Date.now() - this.connection.lastHealthCheck.getTime()) < (this.config.healthCheckInterval * 2);
    }

    /**
     * Update server configuration
     */
    updateConfig(config: Partial<ServerConfig>): void {
        this.config = { ...this.config, ...config };

        if (this.connection) {
            this.connection.config = this.config;
        }
    }

    /**
     * Get current server configuration
     */
    getConfig(): ServerConfig {
        return { ...this.config };
    }

    /**
     * Get server metrics
     */
    getMetrics(): ServerMetrics {
        if (this.connection?.connectedAt) {
            this.metrics.uptime = Date.now() - this.connection.connectedAt.getTime();
        }
        return { ...this.metrics };
    }

    /**
     * Add event listener
     */
    on(event: ServerEventType, listener: (event: ServerEvent) => void): void {
        this.eventEmitter.event(listener);
    }

    /**
     * Remove event listener
     */
    off(event: ServerEventType, listener: (event: ServerEvent) => void): void {
        // Note: VS Code's EventEmitter doesn't support removing specific listeners
        // This is a limitation of the current implementation
    }

    /**
     * Dispose of the server manager and cleanup resources
     */
    dispose(): void {
        this.disconnect();
        this.stopHealthCheckMonitoring();
        this.stopReconnectTimer();

        if (this.serverProcess) {
            this.serverProcess.kill();
        }

        this.eventEmitter.dispose();
        this.disposables.forEach(d => d.dispose());
    }

    /**
     * Start health check monitoring
     */
    private startHealthCheckMonitoring(): void {
        this.stopHealthCheckMonitoring();

        this.healthCheckTimer = setInterval(async () => {
            if (!this.connection || this.connection.status !== ServerStatus.CONNECTED) {
                return;
            }

            try {
                await this.performHealthCheck();
            } catch (error) {
                this.log(`Health check failed: ${error}`);
                await this.handleConnectionLoss();
            }
        }, this.config.healthCheckInterval);
    }

    /**
     * Stop health check monitoring
     */
    private stopHealthCheckMonitoring(): void {
        if (this.healthCheckTimer) {
            clearInterval(this.healthCheckTimer);
            this.healthCheckTimer = null;
        }
    }

    /**
     * Handle connection loss and attempt reconnection
     */
    private async handleConnectionLoss(): Promise<void> {
        if (!this.connection || this.connection.retryCount >= this.config.maxRetries) {
            this.connection!.status = ServerStatus.ERROR;
            this.emitEvent(ServerEventType.CONNECTION_LOST, {
                connectionId: this.connection!.id,
                reason: 'Max retries exceeded'
            });
            return;
        }

        this.connection.status = ServerStatus.RECONNECTING;
        this.connection.retryCount++;
        this.metrics.reconnections++;

        this.emitEvent(ServerEventType.RETRY_ATTEMPT, {
            connectionId: this.connection.id,
            attempt: this.connection.retryCount,
            maxRetries: this.config.maxRetries
        });

        this.reconnectTimer = setTimeout(async () => {
            try {
                await this.performHealthCheck();
                this.connection!.status = ServerStatus.CONNECTED;
                this.connection!.retryCount = 0;

                this.emitEvent(ServerEventType.CONNECTION_ESTABLISHED, {
                    connectionId: this.connection!.id,
                    recovered: true
                });
            } catch (error) {
                await this.handleConnectionLoss();
            }
        }, this.config.retryDelay);
    }

    /**
     * Stop reconnection timer
     */
    private stopReconnectTimer(): void {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
    }

    /**
     * Find server executable in PATH
     */
    private findServerPath(): string | null {
        // This would need to be implemented based on the actual AutoGen server installation
        // For now, return null to indicate server path must be configured
        return null;
    }

    /**
     * Generate unique connection ID
     */
    private generateConnectionId(): string {
        return `conn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Update average response time metric
     */
    private updateAverageResponseTime(responseTime: number): void {
        if (this.metrics.healthChecks === 1) {
            this.metrics.averageResponseTime = responseTime;
        } else {
            this.metrics.averageResponseTime =
                (this.metrics.averageResponseTime * (this.metrics.healthChecks - 1) + responseTime) /
                this.metrics.healthChecks;
        }
    }

    /**
     * Emit server event
     */
    private emitEvent(type: ServerEventType, data: Record<string, unknown>): void {
        const event: ServerEvent = {
            type,
            timestamp: new Date(),
            connectionId: this.connection?.id || 'unknown',
            data
        };

        this.eventEmitter.fire(event);
    }

    /**
     * Log debug message
     */
    private log(message: string): void {
        if (this.config.debug) {
            console.log(`[ServerManager] ${message}`);
        }
    }

    /**
     * Utility delay function
     */
    private delay(ms: number): Promise<void> {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

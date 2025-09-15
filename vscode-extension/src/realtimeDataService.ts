import * as vscode from 'vscode';
import WebSocket from 'ws';

export interface RealtimeDataUpdate {
    type: 'memory_metrics' | 'health_status' | 'analytics_report' | 'optimization_complete';
    data: any;
    timestamp: string;
}

export interface WebSocketConfig {
    url: string;
    reconnectInterval: number;
    maxReconnectAttempts: number;
    heartbeatInterval: number;
}

export class WebSocketClient {
    private ws: WebSocket | null = null;
    private reconnectTimer: NodeJS.Timeout | null = null;
    private heartbeatTimer: NodeJS.Timeout | null = null;
    private reconnectAttempts: number = 0;
    private isIntentionallyClosed: boolean = false;
    private eventHandlers: Map<string, Function[]> = new Map();

    constructor(
        private config: WebSocketConfig,
        private outputChannel: vscode.OutputChannel
    ) {}

    public connect(): void {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.outputChannel.appendLine('WebSocket already connected');
            return;
        }

        this.outputChannel.appendLine(`Connecting to WebSocket: ${this.config.url}`);
        this.isIntentionallyClosed = false;

        try {
            this.ws = new WebSocket(this.config.url);
            this.setupEventHandlers();
        } catch (error) {
            this.outputChannel.appendLine(`Failed to create WebSocket connection: ${error}`);
            this.scheduleReconnect();
        }
    }

    public disconnect(): void {
        this.outputChannel.appendLine('Disconnecting WebSocket');
        this.isIntentionallyClosed = true;
        this.clearTimers();

        if (this.ws) {
            this.ws.close(1000, 'Intentional disconnect');
            this.ws = null;
        }
    }

    public isConnected(): boolean {
        return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
    }

    public send(message: any): void {
        if (!this.isConnected()) {
            this.outputChannel.appendLine('WebSocket not connected, cannot send message');
            return;
        }

        try {
            this.ws!.send(JSON.stringify(message));
        } catch (error) {
            this.outputChannel.appendLine(`Failed to send WebSocket message: ${error}`);
        }
    }

    public subscribe(eventType: string, handler: Function): void {
        if (!this.eventHandlers.has(eventType)) {
            this.eventHandlers.set(eventType, []);
        }
        this.eventHandlers.get(eventType)!.push(handler);
    }

    public unsubscribe(eventType: string, handler: Function): void {
        const handlers = this.eventHandlers.get(eventType);
        if (handlers) {
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }

    private setupEventHandlers(): void {
        if (!this.ws) return;

        this.ws.on('open', () => {
            this.outputChannel.appendLine('WebSocket connected successfully');
            this.reconnectAttempts = 0;
            this.startHeartbeat();
            this.emit('connected', null);

            // Subscribe to real-time updates
            this.send({
                type: 'subscribe',
                topics: ['memory_metrics', 'health_status', 'analytics_report', 'optimization_complete']
            });
        });

        this.ws.on('message', (data: WebSocket.RawData) => {
            try {
                const message = JSON.parse(data.toString());
                this.handleMessage(message);
            } catch (error) {
                this.outputChannel.appendLine(`Failed to parse WebSocket message: ${error}`);
            }
        });

        this.ws.on('close', (code: number, reason: Buffer) => {
            this.outputChannel.appendLine(`WebSocket closed: ${code} - ${reason.toString()}`);
            this.clearTimers();
            this.emit('disconnected', { code, reason: reason.toString() });

            if (!this.isIntentionallyClosed) {
                this.scheduleReconnect();
            }
        });

        this.ws.on('error', (error: Error) => {
            this.outputChannel.appendLine(`WebSocket error: ${error.message}`);
            this.emit('error', error);
        });

        this.ws.on('pong', () => {
            // Heartbeat response received
        });
    }

    private handleMessage(message: any): void {
        switch (message.type) {
            case 'memory_metrics':
            case 'health_status':
            case 'analytics_report':
            case 'optimization_complete':
                this.emit('data', {
                    type: message.type,
                    data: message.data,
                    timestamp: message.timestamp || new Date().toISOString()
                } as RealtimeDataUpdate);
                break;

            case 'heartbeat':
                // Server heartbeat - respond with pong
                this.send({ type: 'pong' });
                break;

            case 'subscription_confirmed':
                this.outputChannel.appendLine(`Subscribed to topics: ${message.topics.join(', ')}`);
                break;

            case 'error':
                this.outputChannel.appendLine(`Server error: ${message.message}`);
                this.emit('server_error', message);
                break;

            default:
                this.outputChannel.appendLine(`Unknown message type: ${message.type}`);
        }
    }

    private emit(event: string, data: any): void {
        const handlers = this.eventHandlers.get(event);
        if (handlers) {
            handlers.forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    this.outputChannel.appendLine(`Error in event handler for ${event}: ${error}`);
                }
            });
        }
    }

    private startHeartbeat(): void {
        this.heartbeatTimer = setInterval(() => {
            if (this.isConnected()) {
                this.ws!.ping();
            }
        }, this.config.heartbeatInterval);
    }

    private scheduleReconnect(): void {
        if (this.isIntentionallyClosed || this.reconnectAttempts >= this.config.maxReconnectAttempts) {
            if (this.reconnectAttempts >= this.config.maxReconnectAttempts) {
                this.outputChannel.appendLine('Max reconnection attempts reached');
                this.emit('max_reconnect_attempts_reached', null);
            }
            return;
        }

        this.reconnectAttempts++;
        const delay = Math.min(this.config.reconnectInterval * this.reconnectAttempts, 30000); // Max 30 seconds

        this.outputChannel.appendLine(`Scheduling reconnect attempt ${this.reconnectAttempts} in ${delay}ms`);

        this.reconnectTimer = setTimeout(() => {
            this.outputChannel.appendLine(`Reconnection attempt ${this.reconnectAttempts}`);
            this.connect();
        }, delay);
    }

    private clearTimers(): void {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }

        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
    }

    public dispose(): void {
        this.disconnect();
        this.eventHandlers.clear();
    }
}

export class RealtimeDataManager {
    private webSocketClient: WebSocketClient;
    private lastDataReceived: Map<string, Date> = new Map();
    private dataBuffers: Map<string, any[]> = new Map();

    constructor(
        private outputChannel: vscode.OutputChannel,
        private config?: Partial<WebSocketConfig>
    ) {
        const defaultConfig: WebSocketConfig = {
            url: 'ws://localhost:9001/ws', // Default WebSocket URL
            reconnectInterval: 2000,
            maxReconnectAttempts: 10,
            heartbeatInterval: 30000
        };

        const finalConfig = { ...defaultConfig, ...config };
        this.webSocketClient = new WebSocketClient(finalConfig, outputChannel);
        this.setupDataHandlers();
    }

    public start(): void {
        this.outputChannel.appendLine('Starting real-time data manager');
        this.webSocketClient.connect();
    }

    public stop(): void {
        this.outputChannel.appendLine('Stopping real-time data manager');
        this.webSocketClient.disconnect();
    }

    public isConnected(): boolean {
        return this.webSocketClient.isConnected();
    }

    public onDataUpdate(handler: (update: RealtimeDataUpdate) => void): void {
        this.webSocketClient.subscribe('data', handler);
    }

    public onConnectionStatusChange(handler: (status: 'connected' | 'disconnected' | 'error') => void): void {
        this.webSocketClient.subscribe('connected', () => handler('connected'));
        this.webSocketClient.subscribe('disconnected', () => handler('disconnected'));
        this.webSocketClient.subscribe('error', () => handler('error'));
    }

    public getLastDataReceived(type: string): Date | null {
        return this.lastDataReceived.get(type) || null;
    }

    public requestDataRefresh(types: string[] = []): void {
        if (!this.webSocketClient.isConnected()) {
            this.outputChannel.appendLine('Cannot request data refresh - WebSocket not connected');
            return;
        }

        const message = {
            type: 'request_refresh',
            data_types: types.length > 0 ? types : ['memory_metrics', 'health_status', 'analytics_report']
        };

        this.webSocketClient.send(message);
    }

    private setupDataHandlers(): void {
        this.webSocketClient.subscribe('data', (update: RealtimeDataUpdate) => {
            this.lastDataReceived.set(update.type, new Date(update.timestamp));

            // Buffer data for potential aggregation
            if (!this.dataBuffers.has(update.type)) {
                this.dataBuffers.set(update.type, []);
            }

            const buffer = this.dataBuffers.get(update.type)!;
            buffer.push(update);

            // Keep only last 10 updates per type
            if (buffer.length > 10) {
                buffer.shift();
            }

            this.outputChannel.appendLine(`Received real-time update: ${update.type}`);
        });

        this.webSocketClient.subscribe('connected', () => {
            this.outputChannel.appendLine('Real-time data connection established');
        });

        this.webSocketClient.subscribe('disconnected', () => {
            this.outputChannel.appendLine('Real-time data connection lost');
        });

        this.webSocketClient.subscribe('max_reconnect_attempts_reached', () => {
            vscode.window.showWarningMessage(
                'Real-time data connection could not be established. Analytics will work with periodic updates only.',
                'Retry'
            ).then(selection => {
                if (selection === 'Retry') {
                    this.start();
                }
            });
        });
    }

    public dispose(): void {
        this.webSocketClient.dispose();
        this.dataBuffers.clear();
        this.lastDataReceived.clear();
    }
}

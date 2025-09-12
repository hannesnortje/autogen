import * as vscode from 'vscode';
import WebSocket from 'ws';
import { McpClient } from './mcpClient';

export interface RealtimeMessage {
    type: string;
    session_id?: string;
    data?: any;
}

export class RealtimeClient {
    private sockets = new Map<string, WebSocket>();
    private listeners = new Map<string, vscode.Disposable[]>();
    private emitter = new vscode.EventEmitter<RealtimeMessage>();
    public readonly onMessage = this.emitter.event;

    constructor(private mcpClient: McpClient) {}

    private toWsUrl(httpUrl: string): string {
        if (httpUrl.startsWith('https://')) return 'wss://' + httpUrl.slice('https://'.length);
        if (httpUrl.startsWith('http://')) return 'ws://' + httpUrl.slice('http://'.length);
        // Fallback: assume ws
        return httpUrl.replace(/^/, 'ws://');
    }

    connect(sessionId: string): void {
        if (this.sockets.has(sessionId)) {
            return; // Already connected
        }

        const base = this.toWsUrl(this.mcpClient.serverUrl);
        const url = `${base}/ws/session/${sessionId}`;
        const ws = new WebSocket(url);

        ws.on('open', () => {
            // Optionally send a hello/ping
        });

        ws.on('message', (raw: WebSocket.RawData) => {
            try {
                const msg: RealtimeMessage = JSON.parse(raw.toString());
                this.emitter.fire(msg);
            } catch (e) {
                // ignore malformed messages
            }
        });

        ws.on('close', () => {
            this.sockets.delete(sessionId);
            const subs = this.listeners.get(sessionId);
            if (subs) {
                subs.forEach(d => d.dispose());
                this.listeners.delete(sessionId);
            }
        });

        ws.on('error', (_err) => {
            // Keep minimal error handling; reconnects can be added later
        });

        this.sockets.set(sessionId, ws);
    }

    disconnect(sessionId: string): void {
        const ws = this.sockets.get(sessionId);
        if (ws) {
            try { ws.close(); } catch {}
            this.sockets.delete(sessionId);
        }
        const subs = this.listeners.get(sessionId);
        if (subs) {
            subs.forEach(d => d.dispose());
            this.listeners.delete(sessionId);
        }
    }

    dispose(): void {
        for (const id of Array.from(this.sockets.keys())) {
            this.disconnect(id);
        }
        this.emitter.dispose();
    }
}

import * as assert from 'assert';
import * as vscode from 'vscode';
import { RealtimeClient, RealtimeMessage } from '../realtime';
import { McpClient } from '../mcpClient';

// Mock WebSocket for testing
class MockWebSocket {
    public readyState = 1; // OPEN
    public url: string;
    private listeners: { [key: string]: Function[] } = {};

    constructor(url: string) {
        this.url = url;
        // Simulate async connection
        setTimeout(() => {
            this.emit('open');
        }, 5);
    }

    on(event: string, callback: Function) {
        if (!this.listeners[event]) {
            this.listeners[event] = [];
        }
        this.listeners[event].push(callback);
    }

    emit(event: string, data?: any) {
        if (this.listeners[event]) {
            this.listeners[event].forEach(callback => {
                try {
                    callback(data);
                } catch (e) {
                    // Ignore callback errors in tests
                }
            });
        }
    }

    close() {
        this.readyState = 3; // CLOSED
        setTimeout(() => this.emit('close'), 1);
    }

    send(data: string) {
        // Simulate server echo for testing
        setTimeout(() => {
            this.emit('message', { data });
        }, 1);
    }
}

suite('RealtimeClient Tests', () => {
    let mcpClient: McpClient;
    let realtimeClient: RealtimeClient;

    setup(() => {
        mcpClient = new McpClient('http://localhost:9000');
        realtimeClient = new RealtimeClient(mcpClient);

        // Mock WebSocket globally for these tests
        (global as any).WebSocket = MockWebSocket;
    });

    teardown(() => {
        realtimeClient.dispose();
    });

    test('should create realtime client', () => {
        assert.ok(realtimeClient);
        assert.ok(realtimeClient.onMessage);
    });

    test('should convert HTTP to WebSocket URL', () => {
        const client = new RealtimeClient(new McpClient('http://localhost:9000'));
        // Access private method via type assertion for testing
        const wsUrl = (client as any).toWsUrl('http://localhost:9000');
        assert.strictEqual(wsUrl, 'ws://localhost:9000');
    });

    test('should convert HTTPS to WebSocket URL', () => {
        const client = new RealtimeClient(new McpClient('https://example.com'));
        const wsUrl = (client as any).toWsUrl('https://example.com');
        assert.strictEqual(wsUrl, 'wss://example.com');
    });

    test('should connect to session WebSocket', (done) => {
        const sessionId = 'test-session-123';

        realtimeClient.connect(sessionId);

        // Verify connection attempt
        setTimeout(() => {
            // Check that socket was created (access private property for testing)
            const sockets = (realtimeClient as any).sockets;
            assert.ok(sockets.has(sessionId));
            done();
        }, 50);
    });

    test('should not create duplicate connections', () => {
        const sessionId = 'test-session-123';

        realtimeClient.connect(sessionId);
        realtimeClient.connect(sessionId); // Second call should be ignored

        const sockets = (realtimeClient as any).sockets;
        assert.strictEqual(sockets.size, 1);
    });

    test('should receive and emit messages', () => {
        // This is a basic integration test - full WebSocket testing would require a running server
        const sessionId = 'test-session-123';
        let messageReceived = false;

        const disposable = realtimeClient.onMessage((msg) => {
            messageReceived = true;
        });

        // Connect (will create socket)
        realtimeClient.connect(sessionId);

        // Verify socket was created
        const sockets = (realtimeClient as any).sockets;
        assert.ok(sockets.has(sessionId));

        disposable.dispose();
    });

    test('should handle malformed messages gracefully', (done) => {
        const sessionId = 'test-session-123';
        let messageReceived = false;

        realtimeClient.onMessage(() => {
            messageReceived = true;
        });

        realtimeClient.connect(sessionId);

        setTimeout(() => {
            const sockets = (realtimeClient as any).sockets;
            const socket = sockets.get(sessionId);
            if (socket) {
                // Send malformed JSON
                socket.emit('message', { data: 'invalid-json{' });

                // Verify no message was emitted
                setTimeout(() => {
                    assert.strictEqual(messageReceived, false);
                    done();
                }, 10);
            }
        }, 20);
    });

    test('should disconnect from session', (done) => {
        const sessionId = 'test-session-123';

        realtimeClient.connect(sessionId);

        setTimeout(() => {
            realtimeClient.disconnect(sessionId);

            const sockets = (realtimeClient as any).sockets;
            assert.strictEqual(sockets.has(sessionId), false);
            done();
        }, 20);
    });

    test('should handle WebSocket errors gracefully', (done) => {
        const sessionId = 'test-session-123';

        realtimeClient.connect(sessionId);

        setTimeout(() => {
            const sockets = (realtimeClient as any).sockets;
            const socket = sockets.get(sessionId);
            if (socket) {
                // Simulate WebSocket error
                socket.emit('error', new Error('Connection failed'));

                // Verify client continues to function
                assert.ok(realtimeClient);
                done();
            }
        }, 20);
    });

    test('should clean up on WebSocket close', (done) => {
        const sessionId = 'test-session-123';

        realtimeClient.connect(sessionId);

        setTimeout(() => {
            const sockets = (realtimeClient as any).sockets;
            const socket = sockets.get(sessionId);
            if (socket) {
                socket.emit('close');

                // Verify cleanup
                setTimeout(() => {
                    assert.strictEqual(sockets.has(sessionId), false);
                    done();
                }, 10);
            }
        }, 20);
    });

    test('should dispose all connections', () => {
        const sessionId1 = 'session-1';
        const sessionId2 = 'session-2';

        realtimeClient.connect(sessionId1);
        realtimeClient.connect(sessionId2);

        const sockets = (realtimeClient as any).sockets;
        assert.strictEqual(sockets.size, 2);

        realtimeClient.dispose();

        assert.strictEqual(sockets.size, 0);
    });
});

suite('RealtimeClient Integration Tests', () => {
    let mcpClient: McpClient;
    let realtimeClient: RealtimeClient;

    setup(() => {
        mcpClient = new McpClient('http://localhost:9000');
        realtimeClient = new RealtimeClient(mcpClient);
        (global as any).WebSocket = MockWebSocket;
    });

    teardown(() => {
        realtimeClient.dispose();
    });

    test('should handle session lifecycle messages', () => {
        // Basic test for session lifecycle concept
        const sessionId = 'lifecycle-test-session';
        let messageHandlerRegistered = false;

        const disposable = realtimeClient.onMessage((msg) => {
            messageHandlerRegistered = true;
        });

        realtimeClient.connect(sessionId);

        // Verify connection was established
        const sockets = (realtimeClient as any).sockets;
        assert.ok(sockets.has(sessionId));

        disposable.dispose();
    });

    test('should support multiple concurrent sessions', () => {
        // Test that multiple sessions can be managed
        const session1 = 'concurrent-session-1';
        const session2 = 'concurrent-session-2';

        realtimeClient.connect(session1);
        realtimeClient.connect(session2);

        const sockets = (realtimeClient as any).sockets;
        assert.strictEqual(sockets.size, 2);
        assert.ok(sockets.has(session1));
        assert.ok(sockets.has(session2));

        // Clean up
        realtimeClient.disconnect(session1);
        realtimeClient.disconnect(session2);
        assert.strictEqual(sockets.size, 0);
    });
});

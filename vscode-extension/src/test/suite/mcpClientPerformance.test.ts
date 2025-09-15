import * as assert from 'assert';
import * as sinon from 'sinon';
import { McpClient, McpServerError } from '../../mcpClient';

// Mock fetch globally
const mockFetch = sinon.stub();
(global as any).fetch = mockFetch;

// Mock AbortController
const mockAbortController = {
    signal: {},
    abort: sinon.stub()
};
(global as any).AbortController = sinon.stub().returns(mockAbortController);

// Mock setTimeout and clearTimeout
const mockSetTimeout = sinon.stub().returns(123);
const mockClearTimeout = sinon.stub();
(global as any).setTimeout = mockSetTimeout;
(global as any).clearTimeout = mockClearTimeout;

describe('McpClient Performance Enhancements', () => {
    let client: McpClient;

    beforeEach(() => {
        client = new McpClient('http://localhost:8000');
        mockFetch.reset();
        mockAbortController.abort.reset();
        mockSetTimeout.reset();
        mockClearTimeout.reset();
        client.clearCache();
    });

    describe('Retry Logic', () => {
        it('should retry on server errors (5xx)', async () => {
            // First two calls return 500, third succeeds
            mockFetch
                .onFirstCall().resolves({
                    ok: false,
                    status: 500,
                    statusText: 'Internal Server Error',
                    json: () => Promise.resolve({ detail: 'Server error' })
                })
                .onSecondCall().resolves({
                    ok: false,
                    status: 500,
                    statusText: 'Internal Server Error',
                    json: () => Promise.resolve({ detail: 'Server error' })
                })
                .onThirdCall().resolves({
                    ok: true,
                    json: () => Promise.resolve({ status: 'ok' })
                });

            const result = await client.getHealth();
            assert.strictEqual(result.status, 'ok');
            assert.strictEqual(mockFetch.callCount, 3);
        });

        it('should not retry on client errors (4xx)', async () => {
            mockFetch.resolves({
                ok: false,
                status: 404,
                statusText: 'Not Found',
                json: () => Promise.resolve({ detail: 'Endpoint not found' })
            });

            try {
                await client.getHealth();
                assert.fail('Should have thrown an error');
            } catch (error) {
                assert.ok(error instanceof McpServerError);
                assert.strictEqual((error as McpServerError).statusCode, 404);
                assert.strictEqual(mockFetch.callCount, 1); // No retries for 4xx
            }
        });

        it('should handle network errors with retries', async () => {
            mockFetch
                .onFirstCall().rejects(new Error('Network error'))
                .onSecondCall().rejects(new Error('Network error'))
                .onThirdCall().resolves({
                    ok: true,
                    json: () => Promise.resolve({ status: 'ok' })
                });

            const result = await client.getHealth();
            assert.strictEqual(result.status, 'ok');
            assert.strictEqual(mockFetch.callCount, 3);
        });
    });

    describe('Request Caching', () => {
        it('should cache GET requests', async () => {
            const responseData = { status: 'healthy', uptime: 12345 };
            mockFetch.resolves({
                ok: true,
                json: () => Promise.resolve(responseData)
            });

            // First call
            const result1 = await client.getHealth();
            assert.deepStrictEqual(result1, responseData);
            assert.strictEqual(mockFetch.callCount, 1);

            // Second call should use cache
            const result2 = await client.getHealth();
            assert.deepStrictEqual(result2, responseData);
            assert.strictEqual(mockFetch.callCount, 1); // No additional fetch
        });

        it('should respect cache TTL', async () => {
            const responseData = { status: 'healthy' };
            mockFetch.resolves({
                ok: true,
                json: () => Promise.resolve(responseData)
            });

            // Mock Date.now to control time
            const originalNow = Date.now;
            let currentTime = 1000000;
            Date.now = () => currentTime;

            try {
                // First call
                await client.getHealth();
                assert.strictEqual(mockFetch.callCount, 1);

                // Second call within TTL - should use cache
                currentTime += 10000; // 10 seconds later
                await client.getHealth();
                assert.strictEqual(mockFetch.callCount, 1);

                // Third call after TTL expires - should make new request
                currentTime += 20000; // 20 more seconds (30 total, TTL is 15s)
                await client.getHealth();
                assert.strictEqual(mockFetch.callCount, 2);
            } finally {
                Date.now = originalNow;
            }
        });

        it('should clear cache manually', async () => {
            const responseData = { status: 'healthy' };
            mockFetch.resolves({
                ok: true,
                json: () => Promise.resolve(responseData)
            });

            // First call
            await client.getHealth();
            assert.strictEqual(mockFetch.callCount, 1);

            // Clear cache
            client.clearCache();

            // Second call should make new request
            await client.getHealth();
            assert.strictEqual(mockFetch.callCount, 2);
        });
    });

    describe('Timeout Handling', () => {
        it('should set request timeout', async () => {
            mockFetch.resolves({
                ok: true,
                json: () => Promise.resolve({ status: 'ok' })
            });

            await client.getHealth();

            // Verify AbortController was created
            assert.ok(mockAbortController.abort.notCalled);

            // Verify timeout was set
            assert.ok(mockSetTimeout.calledOnce);
            assert.strictEqual(mockSetTimeout.firstCall.args[1], 30000); // 30 second timeout

            // Verify timeout was cleared
            assert.ok(mockClearTimeout.calledOnce);
        });

        it('should abort request on timeout', async () => {
            // Simulate timeout by having setTimeout immediately call its callback
            mockSetTimeout.callsFake((callback: any, delay: any) => {
                if (delay === 30000) { // Our timeout
                    callback();
                }
                return 123;
            });

            mockFetch.rejects(new Error('The operation was aborted'));

            try {
                await client.getHealth();
                assert.fail('Should have thrown timeout error');
            } catch (error) {
                assert.ok(error instanceof McpServerError);
                assert.ok(mockAbortController.abort.calledOnce);
            }
        });
    });

    describe('Error Handling', () => {
        it('should parse JSON error responses', async () => {
            mockFetch.resolves({
                ok: false,
                status: 400,
                statusText: 'Bad Request',
                json: () => Promise.resolve({
                    detail: 'Invalid request parameters'
                })
            });

            try {
                await client.getHealth();
                assert.fail('Should have thrown an error');
            } catch (error) {
                assert.ok(error instanceof McpServerError);
                assert.strictEqual((error as McpServerError).message, 'Invalid request parameters');
                assert.strictEqual((error as McpServerError).statusCode, 400);
            }
        });

        it('should handle JSON parsing errors gracefully', async () => {
            mockFetch.resolves({
                ok: false,
                status: 500,
                statusText: 'Internal Server Error',
                json: () => Promise.reject(new Error('Invalid JSON'))
            });

            try {
                await client.getHealth();
                assert.fail('Should have thrown an error');
            } catch (error) {
                assert.ok(error instanceof McpServerError);
                assert.strictEqual((error as McpServerError).message, 'HTTP 500: Internal Server Error');
                assert.strictEqual((error as McpServerError).statusCode, 500);
            }
        });

        it('should handle network connection errors', async () => {
            mockFetch.rejects(new Error('Failed to fetch'));

            try {
                await client.getHealth();
                assert.fail('Should have thrown an error');
            } catch (error) {
                assert.ok(error instanceof McpServerError);
                assert.ok((error as McpServerError).message.includes('Failed to connect to MCP server'));
            }
        });
    });

    describe('Memory Analytics Caching', () => {
        it('should cache memory analytics report for 2 minutes', async () => {
            const reportData = {
                totalMemoryUsage: 1024,
                peakMemoryUsage: 2048,
                memoryOptimizationOpportunities: []
            };

            mockFetch.resolves({
                ok: true,
                json: () => Promise.resolve(reportData)
            });

            // Mock time
            const originalNow = Date.now;
            let currentTime = 1000000;
            Date.now = () => currentTime;

            try {
                // First call
                await client.getMemoryAnalyticsReport();
                assert.strictEqual(mockFetch.callCount, 1);

                // Call within 2 minutes - should use cache
                currentTime += 60000; // 1 minute later
                await client.getMemoryAnalyticsReport();
                assert.strictEqual(mockFetch.callCount, 1);

                // Call after 2 minutes - should make new request
                currentTime += 70000; // 70 more seconds (2+ minutes total)
                await client.getMemoryAnalyticsReport();
                assert.strictEqual(mockFetch.callCount, 2);
            } finally {
                Date.now = originalNow;
            }
        });

        it('should cache memory metrics for 1 minute', async () => {
            const metricsData = {
                currentMemoryUsage: 512,
                memoryLeaks: [],
                performanceMetrics: {}
            };

            mockFetch.resolves({
                ok: true,
                json: () => Promise.resolve(metricsData)
            });

            // Mock time
            const originalNow = Date.now;
            let currentTime = 1000000;
            Date.now = () => currentTime;

            try {
                // First call
                await client.getMemoryMetrics();
                assert.strictEqual(mockFetch.callCount, 1);

                // Call within 1 minute - should use cache
                currentTime += 30000; // 30 seconds later
                await client.getMemoryMetrics();
                assert.strictEqual(mockFetch.callCount, 1);

                // Call after 1 minute - should make new request
                currentTime += 40000; // 40 more seconds (70 total)
                await client.getMemoryMetrics();
                assert.strictEqual(mockFetch.callCount, 2);
            } finally {
                Date.now = originalNow;
            }
        });
    });
});

import { URL } from 'url';
import {
    ServerConfig,
    ServerType,
    ServerValidationResult,
    ServerErrorCode,
    DEFAULT_SERVER_CONFIG
} from '../types/server';

/**
 * Server utility functions for validation, URL parsing, and connection helpers
 */

/**
 * Validate a server URL
 */
export function validateServerUrl(url: string): { valid: boolean; error?: string } {
    if (!url || typeof url !== 'string') {
        return { valid: false, error: 'URL is required' };
    }

    try {
        const urlObj = new URL(url);

        if (!['http:', 'https:'].includes(urlObj.protocol)) {
            return { valid: false, error: 'URL must use HTTP or HTTPS protocol' };
        }

        if (!urlObj.hostname) {
            return { valid: false, error: 'URL must have a valid hostname' };
        }

        const port = parseInt(urlObj.port);
        if (urlObj.port && (isNaN(port) || port < 1 || port > 65535)) {
            return { valid: false, error: 'Port must be between 1 and 65535' };
        }

        return { valid: true };
    } catch (error) {
        return { valid: false, error: 'Invalid URL format' };
    }
}

/**
 * Parse a server URL into components
 */
export function parseServerUrl(url: string): {
    protocol: string;
    hostname: string;
    port: number;
    pathname: string;
    isLocal: boolean;
} {
    const urlObj = new URL(url);
    const port = parseInt(urlObj.port) || (urlObj.protocol === 'https:' ? 443 : 80);
    const isLocal = ['localhost', '127.0.0.1', '::1'].includes(urlObj.hostname);

    return {
        protocol: urlObj.protocol.replace(':', ''),
        hostname: urlObj.hostname,
        port,
        pathname: urlObj.pathname,
        isLocal
    };
}

/**
 * Build a server URL from components
 */
export function buildServerUrl(
    protocol: string = 'http',
    hostname: string = 'localhost',
    port: number = 9000,
    pathname: string = ''
): string {
    const baseUrl = `${protocol}://${hostname}:${port}`;
    return pathname ? `${baseUrl}${pathname.startsWith('/') ? '' : '/'}${pathname}` : baseUrl;
}

/**
 * Validate server configuration
 */
export function validateServerConfig(config: Partial<ServerConfig>): ServerValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];

    // Validate URL
    if (config.url) {
        const urlValidation = validateServerUrl(config.url);
        if (!urlValidation.valid) {
            errors.push(`Invalid URL: ${urlValidation.error}`);
        }
    } else {
        errors.push('Server URL is required');
    }

    // Validate port
    if (config.port !== undefined) {
        if (!Number.isInteger(config.port) || config.port < 1 || config.port > 65535) {
            errors.push('Port must be an integer between 1 and 65535');
        }
    }

    // Validate host
    if (config.host !== undefined) {
        if (!config.host || typeof config.host !== 'string') {
            errors.push('Host must be a non-empty string');
        }
    }

    // Validate server type
    if (config.type !== undefined) {
        if (!Object.values(ServerType).includes(config.type)) {
            errors.push(`Invalid server type: ${config.type}`);
        }
    }

    // Validate timeout values
    if (config.connectionTimeout !== undefined) {
        if (!Number.isInteger(config.connectionTimeout) || config.connectionTimeout < 1000) {
            errors.push('Connection timeout must be at least 1000ms');
        }
    }

    if (config.healthCheckInterval !== undefined) {
        if (!Number.isInteger(config.healthCheckInterval) || config.healthCheckInterval < 5000) {
            errors.push('Health check interval must be at least 5000ms');
        }
    }

    // Validate retry settings
    if (config.maxRetries !== undefined) {
        if (!Number.isInteger(config.maxRetries) || config.maxRetries < 0) {
            errors.push('Max retries must be a non-negative integer');
        }
    }

    if (config.retryDelay !== undefined) {
        if (!Number.isInteger(config.retryDelay) || config.retryDelay < 1000) {
            errors.push('Retry delay must be at least 1000ms');
        }
    }

    // Validate server path for local servers
    if (config.type === ServerType.LOCAL && config.serverPath) {
        if (typeof config.serverPath !== 'string' || !config.serverPath.trim()) {
            warnings.push('Local server path should be a valid file path');
        }
    }

    // Check for common issues
    if (config.url && config.type === ServerType.REMOTE) {
        const parsed = parseServerUrl(config.url);
        if (parsed.isLocal) {
            warnings.push('URL appears to be local but server type is set to remote');
        }
    }

    if (config.autoStart && config.type === ServerType.REMOTE) {
        warnings.push('Auto-start is not supported for remote servers');
    }

    return {
        valid: errors.length === 0,
        errors,
        warnings
    };
}

/**
 * Normalize server configuration with defaults
 */
export function normalizeServerConfig(config: Partial<ServerConfig>): ServerConfig {
    const normalized = { ...DEFAULT_SERVER_CONFIG, ...config };

    // Auto-detect server type from URL if not specified
    if (config.url && !config.type) {
        const parsed = parseServerUrl(config.url);
        normalized.type = parsed.isLocal ? ServerType.LOCAL : ServerType.REMOTE;
    }

    // Extract host and port from URL if not specified
    if (config.url) {
        const parsed = parseServerUrl(config.url);
        if (!config.host) {
            normalized.host = parsed.hostname;
        }
        if (!config.port) {
            normalized.port = parsed.port;
        }
    }

    // Disable auto-start for remote servers
    if (normalized.type === ServerType.REMOTE) {
        normalized.autoStart = false;
    }

    return normalized;
}

/**
 * Check if a port is likely to be available
 */
export async function isPortAvailable(port: number, host: string = 'localhost'): Promise<boolean> {
    return new Promise((resolve) => {
        const net = require('net');
        const server = net.createServer();

        server.listen(port, host, () => {
            server.once('close', () => {
                resolve(true);
            });
            server.close();
        });

        server.on('error', () => {
            resolve(false);
        });
    });
}

/**
 * Find an available port starting from the given port
 */
export async function findAvailablePort(
    startPort: number = 9000,
    endPort: number = 9100,
    host: string = 'localhost'
): Promise<number | null> {
    for (let port = startPort; port <= endPort; port++) {
        if (await isPortAvailable(port, host)) {
            return port;
        }
    }
    return null;
}

/**
 * Create a timeout promise
 */
export function createTimeout<T>(promise: Promise<T>, timeoutMs: number): Promise<T> {
    return new Promise((resolve, reject) => {
        const timeoutId = setTimeout(() => {
            reject(new Error(`Operation timed out after ${timeoutMs}ms`));
        }, timeoutMs);

        promise
            .then((result) => {
                clearTimeout(timeoutId);
                resolve(result);
            })
            .catch((error) => {
                clearTimeout(timeoutId);
                reject(error);
            });
    });
}

/**
 * Retry a function with exponential backoff
 */
export async function retryWithBackoff<T>(
    fn: () => Promise<T>,
    maxRetries: number = 3,
    baseDelay: number = 1000,
    maxDelay: number = 10000
): Promise<T> {
    let lastError: Error;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
        try {
            return await fn();
        } catch (error) {
            lastError = error instanceof Error ? error : new Error(String(error));

            if (attempt === maxRetries) {
                break;
            }

            // Calculate delay with exponential backoff
            const delay = Math.min(baseDelay * Math.pow(2, attempt), maxDelay);
            await new Promise(resolve => setTimeout(resolve, delay));
        }
    }

    throw lastError!;
}

/**
 * Test server connectivity
 */
export async function testServerConnection(
    url: string,
    timeoutMs: number = 5000
): Promise<{
    connected: boolean;
    responseTime: number;
    error?: string;
}> {
    const startTime = Date.now();

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

        const response = await fetch(`${url}/health`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            },
            signal: controller.signal
        });

        clearTimeout(timeoutId);
        const responseTime = Date.now() - startTime;

        return {
            connected: response.ok,
            responseTime,
            error: response.ok ? undefined : `HTTP ${response.status}: ${response.statusText}`
        };

    } catch (error) {
        const responseTime = Date.now() - startTime;

        let errorMessage = 'Unknown error';
        if (error instanceof Error) {
            if (error.name === 'AbortError') {
                errorMessage = 'Connection timeout';
            } else {
                errorMessage = error.message;
            }
        }

        return {
            connected: false,
            responseTime,
            error: errorMessage
        };
    }
}

/**
 * Format server error for display
 */
export function formatServerError(error: unknown): string {
    if (!error) {
        return 'Unknown error occurred';
    }

    if (typeof error === 'string') {
        return error;
    }

    if (error instanceof Error) {
        // Handle common network errors
        if (error.message.includes('ECONNREFUSED')) {
            return 'Connection refused - server may not be running';
        }
        if (error.message.includes('ENOTFOUND')) {
            return 'Host not found - check server URL';
        }
        if (error.message.includes('ETIMEDOUT')) {
            return 'Connection timeout - server may be slow to respond';
        }
        if (error.message.includes('ECONNRESET')) {
            return 'Connection reset - server may have restarted';
        }

        return error.message;
    }

    return JSON.stringify(error);
}

/**
 * Get server error code from error message or object
 */
export function getServerErrorCode(error: unknown): ServerErrorCode {
    const errorStr = typeof error === 'string' ? error :
                    error instanceof Error ? error.message :
                    JSON.stringify(error);

    if (errorStr.includes('ECONNREFUSED') || errorStr.includes('Connection refused')) {
        return ServerErrorCode.CONNECTION_FAILED;
    }
    if (errorStr.includes('ETIMEDOUT') || errorStr.includes('timeout')) {
        return ServerErrorCode.CONNECTION_TIMEOUT;
    }
    if (errorStr.includes('ENOTFOUND') || errorStr.includes('Host not found')) {
        return ServerErrorCode.SERVER_UNREACHABLE;
    }
    if (errorStr.includes('ECONNRESET')) {
        return ServerErrorCode.NETWORK_ERROR;
    }
    if (errorStr.includes('401') || errorStr.includes('Unauthorized')) {
        return ServerErrorCode.AUTHENTICATION_FAILED;
    }
    if (errorStr.includes('403') || errorStr.includes('Forbidden')) {
        return ServerErrorCode.PERMISSION_DENIED;
    }
    if (errorStr.includes('503') || errorStr.includes('Service Unavailable')) {
        return ServerErrorCode.SERVICE_UNAVAILABLE;
    }

    return ServerErrorCode.NETWORK_ERROR;
}

/**
 * Check if an error is recoverable (should retry)
 */
export function isRecoverableError(error: unknown): boolean {
    const errorCode = getServerErrorCode(error);

    // These errors are typically recoverable with retry
    const recoverableErrors = [
        ServerErrorCode.CONNECTION_TIMEOUT,
        ServerErrorCode.NETWORK_ERROR,
        ServerErrorCode.SERVICE_UNAVAILABLE,
        ServerErrorCode.SERVER_UNREACHABLE
    ];

    return recoverableErrors.includes(errorCode);
}

/**
 * Generate a simple health check URL from base URL
 */
export function getHealthCheckUrl(baseUrl: string): string {
    const url = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;
    return `${url}/health`;
}

/**
 * Sanitize server configuration for logging (remove sensitive data)
 */
export function sanitizeConfigForLogging(config: ServerConfig): Partial<ServerConfig> {
    const sanitized = { ...config };

    // Remove or mask sensitive information
    if (sanitized.serverPath) {
        sanitized.serverPath = '[REDACTED]';
    }

    return sanitized;
}

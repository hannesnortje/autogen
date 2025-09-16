import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';

interface SystemStatus {
  mcpConnected: boolean;
  agentCount: number;
  memoryUsage: number;
  lastUpdate: string;
  serverVersion?: string;
  uptime?: string;
  connectionLatency?: number;
  activeSessionsCount?: number;
  totalMemoryEntries?: number;
  memoryTiers?: {
    general: number;
    project: number;
    lessons: number;
  };
  serverHealth?: {
    cpu: number;
    memory: number;
    diskSpace: number;
  };
}

@customElement('system-health')
export class SystemHealth extends LitElement {
  static styles = css`
    :host {
      display: block;
    }

    .health-card {
      padding: 20px;
      background-color: var(--vscode-editorWidget-background);
      border-radius: 8px;
      border: 1px solid var(--vscode-editorWidget-border);
      height: 100%;
    }

    .health-title {
      font-size: 18px;
      font-weight: 600;
      margin: 0 0 16px 0;
      color: var(--vscode-titleBar-activeForeground);
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .health-icon {
      width: 16px;
      height: 16px;
      fill: currentColor;
    }

    .health-metrics {
      display: grid;
      gap: 16px;
    }

    .metric-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px;
      background-color: var(--vscode-input-background);
      border-radius: 6px;
      border: 1px solid var(--vscode-input-border);
    }

    .metric-label {
      font-size: 14px;
      color: var(--vscode-foreground);
      font-weight: 500;
    }

    .metric-value {
      font-size: 14px;
      font-weight: 600;
    }

    .metric-status-good {
      color: var(--vscode-testing-iconPassed);
    }

    .metric-status-warning {
      color: var(--vscode-testing-iconQueued);
    }

    .metric-status-error {
      color: var(--vscode-testing-iconFailed);
    }

    .status-indicator {
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
    }

    .last-update {
      margin-top: 16px;
      font-size: 12px;
      color: var(--vscode-descriptionForeground);
      text-align: center;
    }

    /* Server health styles */
    .server-health {
      margin-top: 20px;
      padding-top: 16px;
      border-top: 1px solid var(--vscode-editorWidget-border);
    }

    .server-health h3 {
      font-size: 14px;
      font-weight: 600;
      margin: 0 0 12px 0;
      color: var(--vscode-titleBar-activeForeground);
    }

    .resource-metrics {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .resource-item {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 12px;
    }

    .resource-label {
      min-width: 50px;
      color: var(--vscode-descriptionForeground);
    }

    .resource-bar {
      flex: 1;
      height: 6px;
      background-color: var(--vscode-progressBar-background);
      border-radius: 3px;
      overflow: hidden;
    }

    .resource-fill {
      height: 100%;
      background-color: var(--vscode-progressBar-background);
      transition: width 0.3s ease;
    }

    .resource-value {
      min-width: 35px;
      text-align: right;
      font-weight: 500;
    }

    /* Uptime styles */
    .uptime-info {
      margin-top: 12px;
      padding-top: 12px;
      border-top: 1px solid var(--vscode-editorWidget-border);
      font-size: 12px;
      text-align: center;
    }

    .uptime-label {
      color: var(--vscode-descriptionForeground);
      margin-right: 8px;
    }

    .uptime-value {
      font-weight: 500;
      color: var(--vscode-foreground);
    }
  `;

  @property({ type: Object })
  systemStatus: SystemStatus | null = null;

  private getConnectionStatus() {
    if (!this.systemStatus) return { status: 'error', text: 'No data' };
    return this.systemStatus.mcpConnected
      ? { status: 'good', text: 'Connected' }
      : { status: 'error', text: 'Disconnected' };
  }

  private getAgentStatus() {
    if (!this.systemStatus) return { status: 'error', count: 0 };
    const count = this.systemStatus.agentCount;
    return {
      status: count > 0 ? 'good' : 'warning',
      count
    };
  }

  private getMemoryStatus() {
    if (!this.systemStatus) return { status: 'error', usage: 0 };
    const usage = this.systemStatus.memoryUsage;
    let status = 'good';
    if (usage > 80) status = 'error';
    else if (usage > 60) status = 'warning';

    return { status, usage };
  }

  render() {
    const connectionStatus = this.getConnectionStatus();
    const agentStatus = this.getAgentStatus();
    const memoryStatus = this.getMemoryStatus();

    return html`
      <div class="health-card">
        <h2 class="health-title">
          <svg class="health-icon" viewBox="0 0 16 16">
            <path d="M8 16A8 8 0 1 1 8 0a8 8 0 0 1 0 16zm.93-9.412l-1 4.705c-.07.34-.504.653-.804.653-.3 0-.734-.313-.804-.653l-1-4.705c-.17-.827.648-1.538 1.317-1.538h1.975c.67 0 1.487.711 1.316 1.538z"/>
          </svg>
          System Health
        </h2>

        <div class="health-metrics">
          <!-- Server Connection -->
          <div class="metric-item">
            <span class="metric-label">MCP Server</span>
            <div class="status-indicator">
              <span class="status-dot metric-status-${connectionStatus.status}"></span>
              <span class="metric-value metric-status-${connectionStatus.status}">
                ${connectionStatus.text}
              </span>
            </div>
          </div>

          <!-- Server Version -->
          ${this.systemStatus?.serverVersion ? html`
            <div class="metric-item">
              <span class="metric-label">Version</span>
              <span class="metric-value">
                ${this.systemStatus.serverVersion}
              </span>
            </div>
          ` : ''}

          <!-- Connection Latency -->
          ${this.systemStatus?.connectionLatency ? html`
            <div class="metric-item">
              <span class="metric-label">Latency</span>
              <span class="metric-value metric-status-${this.systemStatus.connectionLatency < 100 ? 'good' : this.systemStatus.connectionLatency < 500 ? 'warning' : 'error'}">
                ${this.systemStatus.connectionLatency}ms
              </span>
            </div>
          ` : ''}

          <!-- Active Agents -->
          <div class="metric-item">
            <span class="metric-label">Active Agents</span>
            <span class="metric-value metric-status-${agentStatus.status}">
              ${agentStatus.count}
            </span>
          </div>

          <!-- Active Sessions -->
          ${this.systemStatus?.activeSessionsCount !== undefined ? html`
            <div class="metric-item">
              <span class="metric-label">Sessions</span>
              <span class="metric-value metric-status-${this.systemStatus.activeSessionsCount > 0 ? 'good' : 'warning'}">
                ${this.systemStatus.activeSessionsCount}
              </span>
            </div>
          ` : ''}

          <!-- Memory Usage -->
          <div class="metric-item">
            <span class="metric-label">Memory Usage</span>
            <span class="metric-value metric-status-${memoryStatus.status}">
              ${memoryStatus.usage}%
            </span>
          </div>

          <!-- Total Memory Entries -->
          ${this.systemStatus?.totalMemoryEntries !== undefined ? html`
            <div class="metric-item">
              <span class="metric-label">Memory Entries</span>
              <span class="metric-value">
                ${this.systemStatus.totalMemoryEntries.toLocaleString()}
              </span>
            </div>
          ` : ''}
        </div>

        <!-- Server Health (if available) -->
        ${this.systemStatus?.serverHealth ? html`
          <div class="server-health">
            <h3>Server Resources</h3>
            <div class="resource-metrics">
              <div class="resource-item">
                <span class="resource-label">CPU</span>
                <div class="resource-bar">
                  <div class="resource-fill" style="width: ${this.systemStatus.serverHealth.cpu}%"></div>
                </div>
                <span class="resource-value">${this.systemStatus.serverHealth.cpu}%</span>
              </div>

              <div class="resource-item">
                <span class="resource-label">Memory</span>
                <div class="resource-bar">
                  <div class="resource-fill" style="width: ${this.systemStatus.serverHealth.memory}%"></div>
                </div>
                <span class="resource-value">${this.systemStatus.serverHealth.memory}%</span>
              </div>

              <div class="resource-item">
                <span class="resource-label">Disk</span>
                <div class="resource-bar">
                  <div class="resource-fill" style="width: ${this.systemStatus.serverHealth.diskSpace}%"></div>
                </div>
                <span class="resource-value">${this.systemStatus.serverHealth.diskSpace}%</span>
              </div>
            </div>
          </div>
        ` : ''}

        <!-- Uptime -->
        ${this.systemStatus?.uptime ? html`
          <div class="uptime-info">
            <span class="uptime-label">Uptime:</span>
            <span class="uptime-value">${this.systemStatus.uptime}</span>
          </div>
        ` : ''}

        ${this.systemStatus ? html`
          <div class="last-update">
            Last updated: ${this.systemStatus.lastUpdate}
          </div>
        ` : ''}
      </div>
    `;
  }
}

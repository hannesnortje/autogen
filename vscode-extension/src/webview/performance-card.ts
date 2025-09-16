import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';

@customElement('performance-card')
export class PerformanceCard extends LitElement {
  static styles = css`
    :host {
      display: block;
    }

    .performance-card {
      padding: 20px;
      background-color: var(--vscode-editorWidget-background);
      border-radius: 8px;
      border: 1px solid var(--vscode-editorWidget-border);
      height: 100%;
    }

    .performance-title {
      font-size: 18px;
      font-weight: 600;
      margin: 0 0 16px 0;
      color: var(--vscode-titleBar-activeForeground);
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .performance-icon {
      width: 16px;
      height: 16px;
      fill: currentColor;
    }

    .performance-metrics {
      display: grid;
      gap: 16px;
    }

    .metric-item {
      padding: 12px;
      background-color: var(--vscode-input-background);
      border-radius: 6px;
      border: 1px solid var(--vscode-input-border);
    }

    .metric-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
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

    .metric-good {
      color: var(--vscode-testing-iconPassed);
    }

    .metric-warning {
      color: var(--vscode-testing-iconQueued);
    }

    .metric-error {
      color: var(--vscode-testing-iconFailed);
    }

    .progress-bar {
      width: 100%;
      height: 8px;
      background-color: var(--vscode-progressBar-background);
      border-radius: 4px;
      overflow: hidden;
    }

    .progress-fill {
      height: 100%;
      background-color: var(--vscode-progressBar-background);
      transition: width 0.3s ease, background-color 0.3s ease;
      border-radius: 4px;
    }

    .progress-good {
      background-color: var(--vscode-testing-iconPassed);
    }

    .progress-warning {
      background-color: var(--vscode-testing-iconQueued);
    }

    .progress-error {
      background-color: var(--vscode-testing-iconFailed);
    }

    .stats-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
      margin-top: 16px;
    }

    .stat-item {
      text-align: center;
      padding: 12px;
      background-color: var(--vscode-list-hoverBackground);
      border-radius: 6px;
    }

    .stat-value {
      font-size: 18px;
      font-weight: 600;
      color: var(--vscode-testing-iconPassed);
      display: block;
    }

    .stat-label {
      font-size: 12px;
      color: var(--vscode-descriptionForeground);
      margin-top: 4px;
    }

    .last-update {
      margin-top: 16px;
      font-size: 12px;
      color: var(--vscode-descriptionForeground);
      text-align: center;
    }
  `;

  @property({ type: Number })
  memoryUsage = 0;

  @property({ type: String })
  lastUpdate = 'Unknown';

  private getMemoryStatus(usage: number) {
    if (usage > 80) return 'error';
    if (usage > 60) return 'warning';
    return 'good';
  }

  private getCpuUsage() {
    // Mock CPU usage - would come from actual system metrics
    return Math.floor(Math.random() * 40) + 10; // 10-50%
  }

  private getResponseTime() {
    // Mock response time - would come from actual metrics
    return Math.floor(Math.random() * 50) + 20; // 20-70ms
  }

  private getUptime() {
    // Mock uptime - would come from actual metrics
    const hours = Math.floor(Math.random() * 12) + 1;
    const minutes = Math.floor(Math.random() * 60);
    return `${hours}h ${minutes}m`;
  }

  render() {
    const memoryStatus = this.getMemoryStatus(this.memoryUsage);
    const cpuUsage = this.getCpuUsage();
    const cpuStatus = this.getMemoryStatus(cpuUsage);
    const responseTime = this.getResponseTime();
    const uptime = this.getUptime();

    return html`
      <div class="performance-card">
        <h2 class="performance-title">
          <svg class="performance-icon" viewBox="0 0 16 16">
            <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
            <path d="m8.93 6.588-2.29.287-.082.38.45.083c.294.07.352.176.288.469l-.738 3.468c-.194.897.105 1.319.808 1.319.545 0 1.178-.252 1.465-.598l.088-.416c-.2.176-.492.246-.686.246-.275 0-.375-.193-.304-.533L8.93 6.588z"/>
            <circle cx="8" cy="4.5" r="1"/>
          </svg>
          Performance
        </h2>

        <div class="performance-metrics">
          <div class="metric-item">
            <div class="metric-header">
              <span class="metric-label">Memory Usage</span>
              <span class="metric-value metric-${memoryStatus}">${this.memoryUsage}%</span>
            </div>
            <div class="progress-bar">
              <div class="progress-fill progress-${memoryStatus}"
                   style="width: ${this.memoryUsage}%"></div>
            </div>
          </div>

          <div class="metric-item">
            <div class="metric-header">
              <span class="metric-label">CPU Usage</span>
              <span class="metric-value metric-${cpuStatus}">${cpuUsage}%</span>
            </div>
            <div class="progress-bar">
              <div class="progress-fill progress-${cpuStatus}"
                   style="width: ${cpuUsage}%"></div>
            </div>
          </div>
        </div>

        <div class="stats-grid">
          <div class="stat-item">
            <span class="stat-value">${responseTime}ms</span>
            <div class="stat-label">Avg Response</div>
          </div>
          <div class="stat-item">
            <span class="stat-value">${uptime}</span>
            <div class="stat-label">Uptime</div>
          </div>
        </div>

        <div class="last-update">
          Last updated: ${this.lastUpdate}
        </div>
      </div>
    `;
  }
}

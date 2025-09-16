import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';

@customElement('agents-status')
export class AgentsStatus extends LitElement {
  static styles = css`
    :host {
      display: block;
    }

    .agents-card {
      padding: 20px;
      background-color: var(--vscode-editorWidget-background);
      border-radius: 8px;
      border: 1px solid var(--vscode-editorWidget-border);
      height: 100%;
    }

    .agents-title {
      font-size: 18px;
      font-weight: 600;
      margin: 0 0 16px 0;
      color: var(--vscode-titleBar-activeForeground);
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .agents-icon {
      width: 16px;
      height: 16px;
      fill: currentColor;
    }

    .agents-overview {
      display: grid;
      gap: 16px;
      margin-bottom: 20px;
    }

    .agent-metric {
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
    }

    .metric-value {
      font-size: 16px;
      font-weight: 600;
      color: var(--vscode-testing-iconPassed);
    }

    .agent-list {
      margin-top: 16px;
    }

    .agent-list-title {
      font-size: 14px;
      font-weight: 600;
      margin: 0 0 12px 0;
      color: var(--vscode-foreground);
    }

    .agent-item {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 8px;
      margin-bottom: 8px;
      background-color: var(--vscode-list-hoverBackground);
      border-radius: 4px;
      font-size: 13px;
    }

    .agent-avatar {
      width: 24px;
      height: 24px;
      border-radius: 50%;
      background: linear-gradient(45deg, var(--vscode-progressBar-background), var(--vscode-button-background));
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 10px;
      font-weight: 600;
      color: var(--vscode-button-foreground);
    }

    .agent-info {
      flex: 1;
    }

    .agent-name {
      font-weight: 500;
      color: var(--vscode-foreground);
    }

    .agent-status {
      font-size: 11px;
      color: var(--vscode-descriptionForeground);
    }

    .status-active {
      color: var(--vscode-testing-iconPassed);
    }

    .status-idle {
      color: var(--vscode-testing-iconQueued);
    }

    .no-agents {
      text-align: center;
      padding: 20px;
      color: var(--vscode-descriptionForeground);
      font-style: italic;
    }

    .refresh-btn {
      margin-top: 16px;
      padding: 8px 16px;
      background-color: var(--vscode-button-background);
      color: var(--vscode-button-foreground);
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: 12px;
      width: 100%;
    }

    .refresh-btn:hover {
      background-color: var(--vscode-button-hoverBackground);
    }
  `;

  @property({ type: Number })
  agentCount = 0;

  // Mock agent data - in real implementation this would come from MCP server
  private mockAgents = [
    { id: 1, name: 'Code Analyst', type: 'analyst', status: 'active', avatar: 'CA' },
    { id: 2, name: 'Task Manager', type: 'manager', status: 'idle', avatar: 'TM' },
    { id: 3, name: 'Memory Optimizer', type: 'optimizer', status: 'active', avatar: 'MO' }
  ];

  private handleRefreshAgents() {
    // Post message to VS Code extension to refresh agent data
    if (typeof vscode !== 'undefined') {
      vscode.postMessage({
        command: 'refreshAgents'
      });
    }
  }

  render() {
    const activeAgents = this.mockAgents.filter(agent => agent.status === 'active').length;
    const idleAgents = this.mockAgents.filter(agent => agent.status === 'idle').length;

    return html`
      <div class="agents-card">
        <h2 class="agents-title">
          <svg class="agents-icon" viewBox="0 0 16 16">
            <path d="M6 2a2 2 0 1 1 4 0c0 .74-.4 1.39-1 1.73v.27h.5c.28 0 .5.22.5.5v2c0 .28-.22.5-.5.5h-3c-.28 0-.5-.22-.5-.5v-2c0-.28.22-.5.5-.5H7v-.27c-.6-.34-1-.99-1-1.73z"/>
            <path d="M2.5 8A2.5 2.5 0 0 0 0 10.5V14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3.5A2.5 2.5 0 0 0 13.5 8h-11z"/>
          </svg>
          Agents Status
        </h2>

        <div class="agents-overview">
          <div class="agent-metric">
            <span class="metric-label">Total Agents</span>
            <span class="metric-value">${this.agentCount}</span>
          </div>

          <div class="agent-metric">
            <span class="metric-label">Active</span>
            <span class="metric-value">${activeAgents}</span>
          </div>

          <div class="agent-metric">
            <span class="metric-label">Idle</span>
            <span class="metric-value">${idleAgents}</span>
          </div>
        </div>

        ${this.agentCount > 0 ? html`
          <div class="agent-list">
            <h3 class="agent-list-title">Active Agents</h3>
            ${this.mockAgents.map(agent => html`
              <div class="agent-item">
                <div class="agent-avatar">${agent.avatar}</div>
                <div class="agent-info">
                  <div class="agent-name">${agent.name}</div>
                  <div class="agent-status status-${agent.status}">
                    ${agent.status.charAt(0).toUpperCase() + agent.status.slice(1)} • ${agent.type}
                  </div>
                </div>
              </div>
            `)}
          </div>
        ` : html`
          <div class="no-agents">
            No agents currently active
          </div>
        `}

        <button class="refresh-btn" @click=${this.handleRefreshAgents}>
          Refresh Agents
        </button>
      </div>
    `;
  }
}

// VS Code webview API types
declare const vscode: {
  postMessage(message: any): void;
};

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';

/**
 * AutoGen Dashboard Component
 * Main dashboard interface built with Lit 3
 */
@customElement('autogen-dashboard')
export class AutoGenDashboard extends LitElement {
  @property({ type: String })
  projectName = 'AutoGen Agile Project';

  @property({ type: Boolean })
  connected = false;

  static styles = css`
    :host {
      display: block;
      font-family: var(--vscode-font-family);
      color: var(--vscode-foreground);
      background-color: var(--vscode-editor-background);
      padding: 20px;
    }

    .header {
      border-bottom: 1px solid var(--vscode-panel-border);
      padding-bottom: 16px;
      margin-bottom: 24px;
    }

    .title {
      font-size: 24px;
      font-weight: 600;
      margin: 0 0 8px 0;
    }

    .status {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .status-indicator {
      width: 12px;
      height: 12px;
      border-radius: 50%;
      background-color: var(--vscode-charts-red);
    }

    .status-indicator.connected {
      background-color: var(--vscode-charts-green);
    }

    .status-text {
      font-size: 14px;
      opacity: 0.8;
    }

    .section {
      margin-bottom: 24px;
    }

    .section-title {
      font-size: 16px;
      font-weight: 500;
      margin: 0 0 12px 0;
    }

    .placeholder {
      padding: 20px;
      text-align: center;
      background-color: var(--vscode-input-background);
      border: 1px dashed var(--vscode-input-border);
      border-radius: 4px;
      opacity: 0.7;
    }

    .actions {
      display: flex;
      gap: 12px;
      margin-top: 16px;
    }

    .btn {
      background-color: var(--vscode-button-background);
      color: var(--vscode-button-foreground);
      border: none;
      padding: 8px 16px;
      border-radius: 4px;
      cursor: pointer;
      font-size: 13px;
    }

    .btn:hover {
      background-color: var(--vscode-button-hoverBackground);
    }

    .btn.secondary {
      background-color: var(--vscode-button-secondaryBackground);
      color: var(--vscode-button-secondaryForeground);
    }

    .btn.secondary:hover {
      background-color: var(--vscode-button-secondaryHoverBackground);
    }
  `;

  render() {
    return html`
      <div class="header">
        <h1 class="title">${this.projectName}</h1>
        <div class="status">
          <div class="status-indicator ${this.connected ? 'connected' : ''}"></div>
          <span class="status-text">
            ${this.connected ? 'Connected to AutoGen MCP' : 'Disconnected from MCP Server'}
          </span>
        </div>
      </div>

      <div class="section">
        <h2 class="section-title">Active Sessions</h2>
        <div class="placeholder">
          No active AutoGen sessions
        </div>
      </div>

      <div class="section">
        <h2 class="section-title">Recent Activities</h2>
        <div class="placeholder">
          Recent agent interactions will appear here
        </div>
      </div>

      <div class="section">
        <h2 class="section-title">Project Memory</h2>
        <div class="placeholder">
          Persistent project context and memory
        </div>
      </div>

      <div class="actions">
        <button class="btn" @click="${this._startNewSession}">
          Start New Session
        </button>
        <button class="btn secondary" @click="${this._connectToMcp}">
          ${this.connected ? 'Reconnect' : 'Connect to MCP'}
        </button>
        <button class="btn secondary" @click="${this._openSettings}">
          Settings
        </button>
      </div>
    `;
  }

  private _startNewSession() {
    this.dispatchEvent(new CustomEvent('start-session', {
      bubbles: true,
      composed: true
    }));
  }

  private _connectToMcp() {
    this.dispatchEvent(new CustomEvent('connect-mcp', {
      bubbles: true,
      composed: true
    }));
  }

  private _openSettings() {
    this.dispatchEvent(new CustomEvent('open-settings', {
      bubbles: true,
      composed: true
    }));
  }

  connectedCallback() {
    super.connectedCallback();
    console.log('AutoGen Dashboard connected to DOM');
  }
}

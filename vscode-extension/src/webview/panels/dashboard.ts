import { html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import { BasePanel } from '../components/base/base-panel.js';
import { sharedStyles } from '../shared/styles.js';
import { themeProperty } from '../shared/themes.js';

/**
 * AutoGen Dashboard Component
 * Main dashboard interface built with Lit 3 - extends BasePanel
 */
@customElement('autogen-dashboard')
export class AutoGenDashboard extends BasePanel {
  @property({ type: String })
  projectName = 'AutoGen Agile Project';

  @property({ type: Boolean })
  connected = false;

  @themeProperty()
  theme!: string;

  static styles = css`
    ${sharedStyles}

    .status {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 16px;
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

    .dashboard-sections {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 24px;
    }

    .section {
      background-color: var(--vscode-input-background);
      border: 1px solid var(--vscode-panel-border);
      border-radius: 4px;
      padding: 20px;
    }

    .section-title {
      font-size: 16px;
      font-weight: 500;
      margin: 0 0 12px 0;
      color: var(--vscode-titleBar-activeForeground);
    }

    .placeholder {
      padding: 20px;
      text-align: center;
      border: 1px dashed var(--vscode-input-border);
      border-radius: 4px;
      opacity: 0.7;
      background-color: var(--vscode-editor-background);
    }

    .actions {
      display: flex;
      gap: 12px;
      margin-top: 24px;
      flex-wrap: wrap;
    }
  `;

  constructor() {
    super();
    this.title = 'AutoGen Dashboard';
    this.subtitle = 'Multi-agent workflow management';
    this.refreshable = true;
  }

  protected renderContent() {
    return html`
      <div class="status">
        <div class="status-indicator \${this.connected ? 'connected' : ''}"></div>
        <span class="status-text">
          \${this.connected ? 'Connected to AutoGen MCP' : 'Disconnected from MCP Server'}
        </span>
      </div>

      <div class="dashboard-sections">
        <div class="section">
          <h3 class="section-title">Active Sessions</h3>
          <div class="placeholder">
            No active AutoGen sessions
          </div>
        </div>

        <div class="section">
          <h3 class="section-title">Recent Activities</h3>
          <div class="placeholder">
            Recent agent interactions will appear here
          </div>
        </div>

        <div class="section">
          <h3 class="section-title">Project Memory</h3>
          <div class="placeholder">
            Persistent project context and memory
          </div>
        </div>
      </div>

      <div class="actions">
        <button class="btn" @click="\${this._startNewSession}">
          Start New Session
        </button>
        <button class="btn secondary" @click="\${this._connectToMcp}">
          \${this.connected ? 'Reconnect' : 'Connect to MCP'}
        </button>
        <button class="btn secondary" @click="\${this._openSettings}">
          Settings
        </button>
      </div>
    `;
  }

  protected async onRefresh(): Promise<void> {
    // Override with actual refresh logic
    await this.handleAsync(
      new Promise(resolve => setTimeout(resolve, 1000)),
      'Failed to refresh dashboard'
    );
  }

  private _startNewSession() {
    this.dispatchCustomEvent('start-session', {
      projectName: this.projectName
    });
  }

  private _connectToMcp() {
    this.dispatchCustomEvent('connect-mcp', {
      connected: this.connected
    });
  }

  private _openSettings() {
    this.dispatchCustomEvent('open-settings');
  }

  connectedCallback() {
    super.connectedCallback();
    console.log('AutoGen Dashboard connected to DOM');
  }
}

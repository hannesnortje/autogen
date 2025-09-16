import { html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { BasePanel } from '../components/base/base-panel.js';
import { sharedStyles } from '../shared/styles.js';
import { themeProperty } from '../shared/themes.js';

/**
 * Server status information received from extension
 */
interface ServerStatus {
  status: string;
  isHealthy: boolean;
  statusText: string;
  statusIcon: string;
  statusColor: string;
  connection?: {
    url: string;
    connectedAt?: string;
    lastHealthCheck?: string;
    config: {
      type: string;
      autoStart: boolean;
    };
  };
  metrics?: {
    uptime: number;
    healthChecks: number;
    failedHealthChecks: number;
    reconnections: number;
    averageResponseTime: number;
  };
  availableActions: Array<{
    id: string;
    label: string;
    icon: string;
    enabled: boolean;
    tooltip?: string;
  }>;
}

/**
 * AutoGen Dashboard Component
 * Main dashboard interface built with Lit 3 - extends BasePanel
 * Now includes comprehensive server connection status and controls
 */
@customElement('autogen-dashboard')
export class AutoGenDashboard extends BasePanel {
  @property({ type: String })
  projectName = 'AutoGen Agile Project';

  @property({ type: Object })
  serverStatus: ServerStatus | null = null;

  @state()
  private _executingAction: string | null = null;

  @themeProperty()
  theme!: string;

  static styles = css`
    ${sharedStyles}

    .server-status {
      background-color: var(--vscode-input-background);
      border: 1px solid var(--vscode-panel-border);
      border-radius: 8px;
      padding: 20px;
      margin-bottom: 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 16px;
    }

    .status-main {
      display: flex;
      align-items: center;
      gap: 12px;
      flex-grow: 1;
    }

    .status-indicator {
      width: 16px;
      height: 16px;
      border-radius: 50%;
      flex-shrink: 0;
      position: relative;
    }

    .status-indicator.connected {
      background-color: var(--vscode-charts-green);
    }

    .status-indicator.connecting {
      background-color: var(--vscode-charts-orange);
      animation: pulse 1.5s infinite;
    }

    .status-indicator.error {
      background-color: var(--vscode-charts-red);
    }

    .status-indicator.disconnected {
      background-color: var(--vscode-descriptionForeground);
      opacity: 0.5;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.5; transform: scale(1.1); }
    }

    .status-info {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .status-primary {
      font-size: 16px;
      font-weight: 500;
      color: var(--vscode-titleBar-activeForeground);
    }

    .status-secondary {
      font-size: 13px;
      opacity: 0.8;
      color: var(--vscode-descriptionForeground);
    }

    .status-actions {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }

    .action-btn {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 12px;
      border: 1px solid var(--vscode-button-border);
      background-color: var(--vscode-button-secondaryBackground);
      color: var(--vscode-button-secondaryForeground);
      border-radius: 4px;
      font-size: 12px;
      cursor: pointer;
      transition: all 0.2s ease;
      white-space: nowrap;
    }

    .action-btn:hover:not(:disabled) {
      background-color: var(--vscode-button-secondaryHoverBackground);
    }

    .action-btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .action-btn.primary {
      background-color: var(--vscode-button-background);
      color: var(--vscode-button-foreground);
    }

    .action-btn.primary:hover:not(:disabled) {
      background-color: var(--vscode-button-hoverBackground);
    }

    .server-details {
      background-color: var(--vscode-editor-background);
      border: 1px solid var(--vscode-panel-border);
      border-radius: 4px;
      padding: 16px;
      margin-top: 16px;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      font-size: 13px;
    }

    .detail-item {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .detail-label {
      font-weight: 500;
      color: var(--vscode-titleBar-activeForeground);
    }

    .detail-value {
      color: var(--vscode-descriptionForeground);
      font-family: var(--vscode-editor-font-family);
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

    .placeholder.disabled {
      opacity: 0.5;
    }

    .actions {
      display: flex;
      gap: 12px;
      margin-top: 24px;
      flex-wrap: wrap;
    }

    .connection-hint {
      font-size: 12px;
      color: var(--vscode-descriptionForeground);
      margin-top: 8px;
      font-style: italic;
    }

    .loading-text {
      opacity: 0.7;
      font-style: italic;
    }
  `;

  constructor() {
    super();
    this.title = 'AutoGen Dashboard';
    this.subtitle = 'Multi-agent workflow management';
    this.refreshable = true;

    // Listen for messages from extension
    window.addEventListener('message', this._handleExtensionMessage.bind(this));
  }

  protected renderContent() {
    const isConnected = this.serverStatus?.status === 'connected' && this.serverStatus.isHealthy;
    const isConnecting = this.serverStatus?.status === 'connecting' || this.serverStatus?.status === 'starting';

    return html`
      ${this._renderServerStatus()}
      ${this.serverStatus?.connection ? this._renderServerDetails() : ''}

      <div class="dashboard-sections">
        <div class="section">
          <h3 class="section-title">Active Sessions</h3>
          <div class="placeholder ${!isConnected ? 'disabled' : ''}">
            ${!isConnected
              ? 'Connect to AutoGen server to view sessions'
              : 'No active AutoGen sessions'}
          </div>
        </div>

        <div class="section">
          <h3 class="section-title">Recent Activities</h3>
          <div class="placeholder ${!isConnected ? 'disabled' : ''}">
            ${!isConnected
              ? 'Server connection required'
              : 'Recent agent interactions will appear here'}
          </div>
        </div>

        <div class="section">
          <h3 class="section-title">Project Memory</h3>
          <div class="placeholder ${!isConnected ? 'disabled' : ''}">
            ${!isConnected
              ? 'Memory features require server connection'
              : 'Persistent project context and memory'}
          </div>
        </div>
      </div>

      <div class="actions">
        <button
          class="btn primary"
          ?disabled=${!isConnected || isConnecting}
          @click="${this._startNewSession}"
        >
          ${isConnecting ? 'Starting...' : 'Start New Session'}
        </button>

        <button class="btn secondary" @click="${this._openSettings}">
          Settings
        </button>

        <button class="btn secondary" @click="${this._viewLogs}">
          View Logs
        </button>
      </div>

      ${!isConnected ? html`
        <div class="connection-hint">
          💡 Tip: Ensure AutoGen MCP server is running and accessible at the configured URL.
        </div>
      ` : ''}
    `;
  }

  private _renderServerStatus() {
    if (!this.serverStatus) {
      return html`
        <div class="server-status">
          <div class="status-main">
            <div class="status-indicator disconnected"></div>
            <div class="status-info">
              <div class="status-primary loading-text">Loading server status...</div>
            </div>
          </div>
        </div>
      `;
    }

    const statusClass = this._getStatusClass(this.serverStatus.status);

    return html`
      <div class="server-status">
        <div class="status-main">
          <div class="status-indicator ${statusClass}"></div>
          <div class="status-info">
            <div class="status-primary">${this.serverStatus.statusText}</div>
            <div class="status-secondary">
              ${this.serverStatus.connection?.url || 'No connection configured'}
            </div>
          </div>
        </div>

        <div class="status-actions">
          ${this.serverStatus.availableActions.map(action => html`
            <button
              class="action-btn ${action.id === 'connect' || action.id === 'start' ? 'primary' : ''}"
              ?disabled=${!action.enabled || this._executingAction === action.id}
              title="${action.tooltip || action.label}"
              @click="${() => this._executeServerAction(action.id)}"
            >
              ${this._executingAction === action.id
                ? '⏳'
                : action.icon.replace(/\$\((.*?)\)/, '$1')}
              ${this._executingAction === action.id ? 'Working...' : action.label}
            </button>
          `)}
        </div>
      </div>
    `;
  }

  private _renderServerDetails() {
    if (!this.serverStatus?.connection) return '';

    const connection = this.serverStatus.connection;
    const metrics = this.serverStatus.metrics;

    return html`
      <div class="server-details">
        <div class="detail-item">
          <div class="detail-label">Server URL</div>
          <div class="detail-value">${connection.url}</div>
        </div>

        <div class="detail-item">
          <div class="detail-label">Server Type</div>
          <div class="detail-value">${connection.config.type}</div>
        </div>

        ${connection.connectedAt ? html`
          <div class="detail-item">
            <div class="detail-label">Connected Since</div>
            <div class="detail-value">${this._formatDateTime(connection.connectedAt)}</div>
          </div>
        ` : ''}

        ${connection.lastHealthCheck ? html`
          <div class="detail-item">
            <div class="detail-label">Last Health Check</div>
            <div class="detail-value">${this._formatDateTime(connection.lastHealthCheck)}</div>
          </div>
        ` : ''}

        ${metrics ? html`
          <div class="detail-item">
            <div class="detail-label">Health Checks</div>
            <div class="detail-value">${metrics.healthChecks} (${metrics.failedHealthChecks} failed)</div>
          </div>

          <div class="detail-item">
            <div class="detail-label">Avg Response Time</div>
            <div class="detail-value">${Math.round(metrics.averageResponseTime)}ms</div>
          </div>
        ` : ''}
      </div>
    `;
  }

  private _getStatusClass(status: string): string {
    switch (status) {
      case 'connected': return 'connected';
      case 'connecting':
      case 'reconnecting':
      case 'starting': return 'connecting';
      case 'error': return 'error';
      default: return 'disconnected';
    }
  }

  private _formatDateTime(dateStr: string): string {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) {
      return 'Just now';
    } else if (diffMins < 60) {
      return `${diffMins}m ago`;
    } else if (diffMins < 1440) {
      return `${Math.floor(diffMins / 60)}h ago`;
    } else {
      return date.toLocaleDateString();
    }
  }

  private async _executeServerAction(actionId: string) {
    if (this._executingAction) return;

    this._executingAction = actionId;

    try {
      // Send message to extension to execute server action
      this._sendMessage('executeServerAction', { actionId });

      // Reset executing state after a short delay to show feedback
      await new Promise(resolve => setTimeout(resolve, 500));
    } catch (error) {
      console.error(`Failed to execute server action ${actionId}:`, error);
    } finally {
      this._executingAction = null;
    }
  }

  protected async onRefresh(): Promise<void> {
    // Request fresh server status from extension
    this._sendMessage('refreshServerStatus');

    // Show loading state briefly
    await new Promise(resolve => setTimeout(resolve, 500));
  }

  private _startNewSession() {
    this.dispatchCustomEvent('start-session', {
      projectName: this.projectName
    });
  }

  private _openSettings() {
    this._sendMessage('openSettings');
  }

  private _viewLogs() {
    this._sendMessage('viewLogs');
  }

  private _sendMessage(type: string, data: any = {}) {
    // Send message to VS Code extension
    if (window.vscode) {
      window.vscode.postMessage({ type, ...data });
    }
  }

  private _handleExtensionMessage(event: MessageEvent) {
    const message = event.data;

    switch (message.type) {
      case 'serverStatusUpdate':
        this.serverStatus = message.status;
        this.requestUpdate();
        break;

      case 'serverActionResult':
        if (message.success) {
          // Action completed successfully
          this._executingAction = null;
        } else {
          // Action failed
          console.error('Server action failed:', message.error);
          this._executingAction = null;
        }
        break;
    }
  }

  connectedCallback() {
    super.connectedCallback();
    console.log('AutoGen Dashboard connected to DOM');

    // Request initial server status
    this._sendMessage('getServerStatus');
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    window.removeEventListener('message', this._handleExtensionMessage.bind(this));
  }
}

// Declare global vscode object for TypeScript
declare global {
  interface Window {
    vscode?: {
      postMessage(message: any): void;
    };
  }
}

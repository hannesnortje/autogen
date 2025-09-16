import { LitElement, html, css } from 'lit';
import { customElement } from 'lit/decorators.js';

@customElement('quick-actions')
export class QuickActions extends LitElement {
  static styles = css`
    :host {
      display: block;
    }

    .actions-card {
      padding: 20px;
      background-color: var(--vscode-editorWidget-background);
      border-radius: 8px;
      border: 1px solid var(--vscode-editorWidget-border);
      height: 100%;
    }

    .actions-title {
      font-size: 18px;
      font-weight: 600;
      margin: 0 0 16px 0;
      color: var(--vscode-titleBar-activeForeground);
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .actions-icon {
      width: 16px;
      height: 16px;
      fill: currentColor;
    }

    .actions-grid {
      display: grid;
      gap: 12px;
    }

    .action-btn {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 14px 16px;
      background-color: var(--vscode-button-background);
      color: var(--vscode-button-foreground);
      border: none;
      border-radius: 6px;
      cursor: pointer;
      font-size: 14px;
      font-weight: 500;
      text-align: left;
      transition: background-color 0.2s ease;
      width: 100%;
    }

    .action-btn:hover {
      background-color: var(--vscode-button-hoverBackground);
    }

    .action-btn:active {
      background-color: var(--vscode-button-activeBackground);
    }

    .action-btn.secondary {
      background-color: var(--vscode-button-secondaryBackground);
      color: var(--vscode-button-secondaryForeground);
    }

    .action-btn.secondary:hover {
      background-color: var(--vscode-button-secondaryHoverBackground);
    }

    .action-icon {
      width: 16px;
      height: 16px;
      fill: currentColor;
      flex-shrink: 0;
    }

    .action-content {
      flex: 1;
    }

    .action-label {
      font-weight: 600;
      margin-bottom: 2px;
    }

    .action-description {
      font-size: 12px;
      opacity: 0.8;
      line-height: 1.3;
    }

    .divider {
      height: 1px;
      background-color: var(--vscode-editorWidget-border);
      margin: 8px 0;
    }
  `;

  private handleStartServer() {
    this.postMessage('startMcpServer');
  }

  private handleStopServer() {
    this.postMessage('stopMcpServer');
  }

  private handleRefreshDashboard() {
    this.postMessage('refreshDashboard');
  }

  private handleOpenLogs() {
    this.postMessage('openLogs');
  }

  private handleOpenSettings() {
    this.postMessage('openSettings');
  }

  private handleViewMemory() {
    this.postMessage('viewMemory');
  }

  private handleCreateSession() {
    this.postMessage('createSession');
  }

  private handleCreateAgent() {
    this.postMessage('createAgent');
  }

  private handleExploreMemory() {
    this.postMessage('exploreMemory');
  }

  private handleExportData() {
    this.postMessage('exportData');
  }

  private postMessage(command: string) {
    if (typeof vscode !== 'undefined') {
      vscode.postMessage({ command });
    }
  }

  render() {
    return html`
      <div class="actions-card">
        <h2 class="actions-title">
          <svg class="actions-icon" viewBox="0 0 16 16">
            <path d="M8.5 1.5A.5.5 0 0 0 8 1H4a.5.5 0 0 0-.5.5V3H2.5A1.5 1.5 0 0 0 1 4.5v7A1.5 1.5 0 0 0 2.5 13h11a1.5 1.5 0 0 0 1.5-1.5v-7A1.5 1.5 0 0 0 13.5 3H12V1.5A.5.5 0 0 0 11.5 1H8a.5.5 0 0 0-.5.5z"/>
          </svg>
          Quick Actions
        </h2>

        <div class="actions-grid">
          <button class="action-btn" @click=${this.handleStartServer}>
            <svg class="action-icon" viewBox="0 0 16 16">
              <path d="m8 4.5 1 1L8 6.5 7 5.5l1-1zm-1 1v6h2V5.5H7z"/>
              <path d="M8 1a7 7 0 1 0 0 14A7 7 0 0 0 8 1zM0 8a8 8 0 1 1 16 0A8 8 0 0 1 0 8z"/>
            </svg>
            <div class="action-content">
              <div class="action-label">Start MCP Server</div>
              <div class="action-description">Launch the AutoGen MCP server</div>
            </div>
          </button>

          <button class="action-btn secondary" @click=${this.handleStopServer}>
            <svg class="action-icon" viewBox="0 0 16 16">
              <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
              <path d="M5 6.5h6v3H5z"/>
            </svg>
            <div class="action-content">
              <div class="action-label">Stop MCP Server</div>
              <div class="action-description">Shutdown the MCP server safely</div>
            </div>
          </button>

          <div class="divider"></div>

          <button class="action-btn secondary" @click=${this.handleRefreshDashboard}>
            <svg class="action-icon" viewBox="0 0 16 16">
              <path d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2v1z"/>
              <path d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466z"/>
            </svg>
            <div class="action-content">
              <div class="action-label">Refresh Dashboard</div>
              <div class="action-description">Update all dashboard data</div>
            </div>
          </button>

          <button class="action-btn secondary" @click=${this.handleViewMemory}>
            <svg class="action-icon" viewBox="0 0 16 16">
              <path d="M2 3a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V3z"/>
              <path d="M4 5h8v1H4V5zm0 2h8v1H4V7zm0 2h6v1H4V9z"/>
            </svg>
            <div class="action-content">
              <div class="action-label">View Memory</div>
              <div class="action-description">Open memory analytics panel</div>
            </div>
          </button>

          <div class="divider"></div>

          <button class="action-btn secondary" @click=${this.handleOpenLogs}>
            <svg class="action-icon" viewBox="0 0 16 16">
              <path d="M3 1a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1H3zm0 1h10v12H3V2z"/>
              <path d="M4 4h8v1H4V4zM4 6h6v1H4V6zM4 8h8v1H4V8zM4 10h6v1H4v-1z"/>
            </svg>
            <div class="action-content">
              <div class="action-label">View Logs</div>
              <div class="action-description">Open server logs and diagnostics</div>
            </div>
          </button>

          <button class="action-btn secondary" @click=${this.handleOpenSettings}>
            <svg class="action-icon" viewBox="0 0 16 16">
              <path d="M8 4.754a3.246 3.246 0 1 0 0 6.492 3.246 3.246 0 0 0 0-6.492zM5.754 8a2.246 2.246 0 1 1 4.492 0 2.246 2.246 0 0 1-4.492 0z"/>
              <path d="M9.796 1.343c-.527-1.79-3.065-1.79-3.592 0l-.094.319a.873.873 0 0 1-1.255.52l-.292-.16c-1.64-.892-3.433.902-2.54 2.541l.159.292a.873.873 0 0 1-.52 1.255l-.319.094c-1.79.527-1.79 3.065 0 3.592l.319.094a.873.873 0 0 1 .52 1.255l-.16.292c-.892 1.64.901 3.434 2.541 2.54l.292-.159a.873.873 0 0 1 1.255.52l.094.319c.527 1.79 3.065 1.79 3.592 0l.094-.319a.873.873 0 0 1 1.255-.52l.292.16c1.64.893 3.434-.902 2.54-2.541l-.159-.292a.873.873 0 0 1 .52-1.255l.319-.094c1.79-.527 1.79-3.065 0-3.592l-.319-.094a.873.873 0 0 1-.52-1.255l.16-.292c.893-1.64-.902-3.433-2.541-2.54l-.292.159a.873.873 0 0 1-1.255-.52l-.094-.319z"/>
            </svg>
            <div class="action-content">
              <div class="action-label">Settings</div>
              <div class="action-description">Configure extension preferences</div>
            </div>
          </button>
        </div>
      </div>
    `;
  }
}

// VS Code webview API types
declare const vscode: {
  postMessage(message: any): void;
};

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import './system-health.js';
import './agents-status.js';
import './performance-card.js';
import './quick-actions.js';
import './dashboard-footer.js';

// VS Code webview API types
declare const vscode: {
  postMessage(message: any): void;
};

declare function acquireVsCodeApi(): {
  postMessage(message: any): void;
};

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
}

type DashboardSection = 'overview' | 'sessions' | 'memory' | 'agents' | 'settings';

@customElement('dashboard-app')
export class DashboardApp extends LitElement {
  @state()
  private currentSection: DashboardSection = 'overview';

  @state()
  private systemStatus: SystemStatus | null = null;

  @state()
  private loading = true;

  @state()
  private error: string | null = null;

  @state()
  private breadcrumbs: Array<{ label: string; section?: DashboardSection }> = [
    { label: 'Dashboard', section: 'overview' }
  ];

  static styles = css`
    :host {
      display: block;
      padding: 0;
      font-family: var(--vscode-font-family);
      color: var(--vscode-foreground);
      background-color: var(--vscode-editor-background);
    }

    .dashboard-container {
      display: flex;
      flex-direction: column;
      height: 100vh;
    }

    .dashboard-navigation {
      display: flex;
      border-bottom: 1px solid var(--vscode-editorWidget-border);
      background-color: var(--vscode-editorWidget-background);
      position: sticky;
      top: 0;
      z-index: 100;
    }

    .nav-tabs {
      display: flex;
      list-style: none;
      margin: 0;
      padding: 0;
    }

    .nav-tab {
      padding: 12px 20px;
      cursor: pointer;
      border-bottom: 3px solid transparent;
      transition: all 0.2s ease;
      color: var(--vscode-tab-inactiveForeground);
      background-color: transparent;
    }

    .nav-tab:hover {
      background-color: var(--vscode-tab-hoverBackground);
      color: var(--vscode-tab-activeForeground);
    }

    .nav-tab.active {
      color: var(--vscode-tab-activeForeground);
      border-bottom-color: var(--vscode-tab-activeBorder);
      background-color: var(--vscode-tab-activeBackground);
    }

    .breadcrumbs {
      display: flex;
      align-items: center;
      padding: 8px 20px;
      background-color: var(--vscode-breadcrumb-background);
      border-bottom: 1px solid var(--vscode-editorWidget-border);
      font-size: 12px;
    }

    .breadcrumb-item {
      color: var(--vscode-breadcrumb-foreground);
    }

    .breadcrumb-separator {
      margin: 0 8px;
      color: var(--vscode-breadcrumb-focusForeground);
    }

    .dashboard-content {
      flex: 1;
      overflow-y: auto;
      padding: 20px;
    }

    .dashboard-header {
      margin-bottom: 30px;
      padding: 20px;
      background-color: var(--vscode-editorWidget-background);
      border-radius: 8px;
      border: 1px solid var(--vscode-editorWidget-border);
    }

    .dashboard-title {
      font-size: 24px;
      font-weight: 600;
      margin: 0 0 8px 0;
      color: var(--vscode-titleBar-activeForeground);
    }

    .dashboard-subtitle {
      font-size: 14px;
      margin: 0;
      color: var(--vscode-descriptionForeground);
    }

    .dashboard-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 20px;
      margin-bottom: 30px;
    }

    .dashboard-row {
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 20px;
      margin-bottom: 20px;
    }

    .status-indicator {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      font-size: 12px;
      padding: 4px 8px;
      border-radius: 4px;
      background-color: var(--vscode-badge-background);
      color: var(--vscode-badge-foreground);
    }

    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
    }

    .status-connected .status-dot {
      background-color: var(--vscode-testing-iconPassed);
    }

    .status-disconnected .status-dot {
      background-color: var(--vscode-testing-iconFailed);
    }

    .loading {
      text-align: center;
      padding: 40px;
      color: var(--vscode-descriptionForeground);
    }

    .error {
      text-align: center;
      padding: 40px;
      color: var(--vscode-errorForeground);
      background-color: var(--vscode-inputValidation-errorBackground);
      border-radius: 8px;
      border: 1px solid var(--vscode-inputValidation-errorBorder);
    }

    /* Tab navigation styles */
    .nav-tab {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 12px 20px;
      cursor: pointer;
      border-bottom: 3px solid transparent;
      transition: all 0.2s ease;
      color: var(--vscode-tab-inactiveForeground);
      background-color: transparent;
      border: none;
      font-family: inherit;
      font-size: 14px;
    }

    .tab-icon {
      font-size: 16px;
    }

    .tab-label {
      font-weight: 500;
    }

    /* Section styles */
    .section-header {
      margin-bottom: 24px;
      padding-bottom: 16px;
      border-bottom: 1px solid var(--vscode-editorWidget-border);
    }

    .section-header h2 {
      font-size: 20px;
      font-weight: 600;
      margin: 0 0 8px 0;
      color: var(--vscode-titleBar-activeForeground);
    }

    .section-header p {
      font-size: 14px;
      margin: 0;
      color: var(--vscode-descriptionForeground);
    }

    /* Button styles */
    .primary-btn, .secondary-btn {
      padding: 8px 16px;
      border-radius: 4px;
      border: none;
      cursor: pointer;
      font-family: inherit;
      font-size: 13px;
      font-weight: 500;
      transition: background-color 0.2s ease;
    }

    .primary-btn {
      background-color: var(--vscode-button-background);
      color: var(--vscode-button-foreground);
    }

    .primary-btn:hover {
      background-color: var(--vscode-button-hoverBackground);
    }

    .secondary-btn {
      background-color: var(--vscode-button-secondaryBackground);
      color: var(--vscode-button-secondaryForeground);
    }

    .secondary-btn:hover {
      background-color: var(--vscode-button-secondaryHoverBackground);
    }

    /* Sessions section styles */
    .sessions-toolbar {
      display: flex;
      gap: 12px;
      margin-bottom: 20px;
    }

    .sessions-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 24px;
    }

    .sessions-section h3 {
      font-size: 16px;
      font-weight: 600;
      margin: 0 0 16px 0;
      color: var(--vscode-titleBar-activeForeground);
    }

    .session-list {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .session-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px;
      background-color: var(--vscode-editorWidget-background);
      border: 1px solid var(--vscode-editorWidget-border);
      border-radius: 6px;
    }

    .session-info {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .session-name {
      font-weight: 500;
      color: var(--vscode-foreground);
    }

    .session-status {
      font-size: 12px;
      padding: 2px 8px;
      border-radius: 12px;
      text-transform: uppercase;
      font-weight: 600;
    }

    .session-status.running {
      background-color: var(--vscode-testing-runAction);
      color: white;
    }

    .session-status.completed {
      background-color: var(--vscode-testing-iconPassed);
      color: white;
    }

    .session-actions {
      display: flex;
      gap: 8px;
    }

    .session-actions button {
      padding: 6px 12px;
      border: 1px solid var(--vscode-editorWidget-border);
      background-color: transparent;
      color: var(--vscode-foreground);
      border-radius: 4px;
      cursor: pointer;
      font-size: 12px;
    }

    .session-actions button:hover {
      background-color: var(--vscode-editorWidget-background);
    }

    /* Memory section styles */
    .memory-overview {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }

    .memory-tier-card {
      padding: 20px;
      background-color: var(--vscode-editorWidget-background);
      border: 1px solid var(--vscode-editorWidget-border);
      border-radius: 8px;
      text-align: center;
    }

    .memory-tier-card h3 {
      font-size: 14px;
      font-weight: 600;
      margin: 0 0 12px 0;
      color: var(--vscode-titleBar-activeForeground);
    }

    .memory-stats {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 4px;
    }

    .memory-count {
      font-size: 24px;
      font-weight: 700;
      color: var(--vscode-charts-blue);
    }

    .memory-label {
      font-size: 12px;
      color: var(--vscode-descriptionForeground);
    }

    .memory-actions {
      display: flex;
      gap: 12px;
    }

    /* Agents section styles */
    .agents-toolbar {
      display: flex;
      gap: 12px;
      margin-bottom: 20px;
    }

    .agents-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 16px;
    }

    .agent-card {
      padding: 20px;
      background-color: var(--vscode-editorWidget-background);
      border: 1px solid var(--vscode-editorWidget-border);
      border-radius: 8px;
    }

    .agent-info {
      margin-bottom: 12px;
    }

    .agent-info h4 {
      font-size: 16px;
      font-weight: 600;
      margin: 0 0 8px 0;
      color: var(--vscode-titleBar-activeForeground);
    }

    .agent-type {
      font-size: 12px;
      padding: 2px 8px;
      background-color: var(--vscode-badge-background);
      color: var(--vscode-badge-foreground);
      border-radius: 12px;
      margin-right: 8px;
    }

    .agent-status.active {
      font-size: 12px;
      padding: 2px 8px;
      background-color: var(--vscode-testing-iconPassed);
      color: white;
      border-radius: 12px;
    }

    .agent-metrics {
      margin-bottom: 16px;
      font-size: 12px;
      color: var(--vscode-descriptionForeground);
    }

    .agent-metrics span {
      margin-right: 16px;
    }

    .agent-actions {
      display: flex;
      gap: 8px;
    }

    .agent-actions button {
      padding: 6px 12px;
      border: 1px solid var(--vscode-editorWidget-border);
      background-color: transparent;
      color: var(--vscode-foreground);
      border-radius: 4px;
      cursor: pointer;
      font-size: 12px;
    }

    .agent-actions button:hover {
      background-color: var(--vscode-editorWidget-background);
    }

    /* Settings section styles */
    .settings-group {
      margin-bottom: 32px;
      padding: 20px;
      background-color: var(--vscode-editorWidget-background);
      border: 1px solid var(--vscode-editorWidget-border);
      border-radius: 8px;
    }

    .settings-group h3 {
      font-size: 16px;
      font-weight: 600;
      margin: 0 0 16px 0;
      color: var(--vscode-titleBar-activeForeground);
    }

    .setting-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
    }

    .setting-item:last-child {
      margin-bottom: 0;
    }

    .setting-item label {
      font-weight: 500;
      color: var(--vscode-foreground);
    }

    .setting-item input[type="text"],
    .setting-item select {
      padding: 6px 10px;
      border: 1px solid var(--vscode-editorWidget-border);
      background-color: var(--vscode-input-background);
      color: var(--vscode-input-foreground);
      border-radius: 4px;
      font-family: inherit;
      font-size: 13px;
    }

    .setting-item input[type="checkbox"] {
      transform: scale(1.2);
    }

    .settings-actions {
      display: flex;
      gap: 12px;
    }
  `;

  connectedCallback() {
    super.connectedCallback();
    this.setupVSCodeAPI();
    this.setupMessageListener();
    this.loadDataFromAttributes();

    // Delay request to ensure vscode API is available
    setTimeout(() => {
      console.log('Requesting system status...');
      this.requestSystemStatus();
    }, 200);
  }

  private setupVSCodeAPI() {
    try {
      // Acquire VS Code API if available
      if (typeof acquireVsCodeApi !== 'undefined') {
        const api = acquireVsCodeApi();
        (window as any).vscode = api;
        console.log('VS Code API initialized successfully');
      } else {
        console.warn('VS Code API not available - running in development mode?');
      }
    } catch (error) {
      console.error('Failed to initialize VS Code API:', error);
    }
  }

  private loadDataFromAttributes() {
    // Load initial data from HTML data attributes
    const mcpConnected = this.getAttribute('data-mcp-connected') === 'true';
    const agentCount = parseInt(this.getAttribute('data-agent-count') || '0');
    const memoryUsage = parseInt(this.getAttribute('data-memory-usage') || '0');
    const lastUpdate = this.getAttribute('data-last-update') || '';

    if (lastUpdate) {
      this.systemStatus = {
        mcpConnected,
        agentCount,
        memoryUsage,
        lastUpdate,
        serverVersion: '1.0.0',
        uptime: '0 minutes',
        connectionLatency: Math.floor(Math.random() * 50) + 10
      };
      this.loading = false;
      console.log('Initial system status loaded from attributes:', this.systemStatus);
    }
  }

  private setupMessageListener() {
    // Listen for messages from VS Code extension
    window.addEventListener('message', (event) => {
      console.log('Dashboard received message:', event.data);
      const message = event.data;
      switch (message.command) {
        case 'systemStatus':
          console.log('Setting system status:', message.data);
          this.systemStatus = message.data;
          this.loading = false;
          this.error = null;
          break;
        case 'error':
          console.log('Setting error:', message.data);
          this.error = message.data;
          this.loading = false;
          break;
      }
    });

    // Handle messages from child components
    this.addEventListener('dashboard-message', (event: Event) => {
      const customEvent = event as CustomEvent;
      const message = customEvent.detail;

      // Forward component messages to VS Code extension
      if (message && message.command) {
        this.sendMessage(message);
      }
    });
  }

  private sendMessage(message: any) {
    try {
      if ((window as any).vscode) {
        console.log('Sending message to extension:', message);
        (window as any).vscode.postMessage(message);
      } else {
        console.warn('VS Code API not available, cannot send message:', message);
      }
    } catch (error) {
      console.error('Failed to send message to extension:', error);
    }
  }

  private requestSystemStatus() {
    // Post message to VS Code extension
    console.log('requestSystemStatus called, vscode available:', typeof (window as any).vscode !== 'undefined');

    this.sendMessage({
      command: 'getSystemStatus'
    });
  }

  private handleRefresh() {
    this.loading = true;
    this.error = null;
    this.requestSystemStatus();
  }

  private navigateToSection(section: DashboardSection) {
    this.currentSection = section;
    this.updateBreadcrumbs(section);
  }

  private updateBreadcrumbs(section: DashboardSection) {
    const sectionNames: Record<DashboardSection, string> = {
      overview: 'Overview',
      sessions: 'Sessions',
      memory: 'Memory',
      agents: 'Agents',
      settings: 'Settings'
    };

    this.breadcrumbs = [
      { label: 'Dashboard', section: 'overview' },
      { label: sectionNames[section] }
    ];
  }

  private handleTabClick(section: DashboardSection) {
    this.navigateToSection(section);
  }

  private renderNavigation() {
    const tabs: Array<{ section: DashboardSection; label: string; icon: string }> = [
      { section: 'overview', label: 'Overview', icon: '🏠' },
      { section: 'sessions', label: 'Sessions', icon: '💬' },
      { section: 'memory', label: 'Memory', icon: '🧠' },
      { section: 'agents', label: 'Agents', icon: '🤖' },
      { section: 'settings', label: 'Settings', icon: '⚙️' }
    ];

    return html`
      <div class="dashboard-navigation">
        <ul class="nav-tabs">
          ${tabs.map(tab => html`
            <li class="nav-tab ${this.currentSection === tab.section ? 'active' : ''}"
                @click=${() => this.handleTabClick(tab.section)}>
              <span class="tab-icon">${tab.icon}</span>
              <span class="tab-label">${tab.label}</span>
            </li>
          `)}
        </ul>
      </div>
      <div class="breadcrumbs">
        ${this.breadcrumbs.map((crumb, index) => html`
          ${index > 0 ? html`<span class="breadcrumb-separator">›</span>` : ''}
          <span class="breadcrumb-item">${crumb.label}</span>
        `)}
      </div>
    `;
  }

  render() {
    if (this.loading) {
      return html`
        <div class="loading">
          <div>Loading AutoGen MCP Dashboard...</div>
        </div>
      `;
    }

    if (this.error) {
      return html`
        <div class="error">
          <div>Error loading dashboard: ${this.error}</div>
          <button @click=${this.handleRefresh} class="refresh-btn">
            Retry
          </button>
        </div>
      `;
    }

    return html`
      <div class="dashboard-container">
        ${this.renderNavigation()}

        <div class="dashboard-content">
          ${this.renderCurrentSection()}
        </div>

        <dashboard-footer
          .lastUpdate=${this.systemStatus?.lastUpdate || 'Never'}>
        </dashboard-footer>
      </div>
    `;
  }

  private renderCurrentSection() {
    switch (this.currentSection) {
      case 'overview':
        return this.renderOverviewSection();
      case 'sessions':
        return this.renderSessionsSection();
      case 'memory':
        return this.renderMemorySection();
      case 'agents':
        return this.renderAgentsSection();
      case 'settings':
        return this.renderSettingsSection();
      default:
        return this.renderOverviewSection();
    }
  }

  private renderOverviewSection() {
    return html`
      <div class="dashboard-header">
        <h1 class="dashboard-title">AutoGen MCP Dashboard</h1>
        <p class="dashboard-subtitle">
          Monitor system status, agents, and memory usage
        </p>
        <div class="status-indicator ${this.systemStatus?.mcpConnected ? 'status-connected' : 'status-disconnected'}">
          <span class="status-dot"></span>
          MCP Server ${this.systemStatus?.mcpConnected ? 'Connected' : 'Disconnected'}
        </div>
      </div>

      <div class="dashboard-row">
        <system-health
          .systemStatus=${this.systemStatus}>
        </system-health>
        <quick-actions></quick-actions>
      </div>

      <div class="dashboard-grid">
        <agents-status
          .agentCount=${this.systemStatus?.agentCount || 0}>
        </agents-status>

        <performance-card
          title="Memory Usage"
          .value=${this.systemStatus?.memoryUsage || 0}
          unit="%"
          status="good">
        </performance-card>

        <performance-card
          title="Active Sessions"
          .value=${this.systemStatus?.activeSessionsCount || 0}
          unit="sessions"
          status="good">
        </performance-card>
      </div>
    `;
  }

  private renderSessionsSection() {
    return html`
      <div class="section-header">
        <h2>Session Management</h2>
        <p>Create, monitor, and manage AutoGen conversation sessions</p>
      </div>

      <div class="sessions-content">
        <div class="sessions-toolbar">
          <button class="primary-btn" @click=${this.handleCreateSession}>
            ➕ New Session
          </button>
          <button class="secondary-btn" @click=${this.handleRefreshSessions}>
            🔄 Refresh
          </button>
        </div>

        <div class="sessions-grid">
          <div class="sessions-section">
            <h3>Running Sessions</h3>
            <div class="session-list">
              <div class="session-item">
                <div class="session-info">
                  <span class="session-name">Research Assistant</span>
                  <span class="session-status running">Running</span>
                </div>
                <div class="session-actions">
                  <button>View</button>
                  <button>Stop</button>
                </div>
              </div>
            </div>
          </div>

          <div class="sessions-section">
            <h3>Recent Sessions</h3>
            <div class="session-list">
              <div class="session-item">
                <div class="session-info">
                  <span class="session-name">Code Review</span>
                  <span class="session-status completed">Completed</span>
                </div>
                <div class="session-actions">
                  <button>View</button>
                  <button>Archive</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  private renderMemorySection() {
    return html`
      <div class="section-header">
        <h2>Memory Analytics</h2>
        <p>Explore and manage your three-tier Qdrant memory system</p>
      </div>

      <div class="memory-analytics">
        <div class="memory-overview">
          <div class="memory-tier-card">
            <h3>General Memory</h3>
            <div class="memory-stats">
              <span class="memory-count">${this.systemStatus?.memoryTiers?.general || 0}</span>
              <span class="memory-label">entries</span>
            </div>
          </div>

          <div class="memory-tier-card">
            <h3>Project Memory</h3>
            <div class="memory-stats">
              <span class="memory-count">${this.systemStatus?.memoryTiers?.project || 0}</span>
              <span class="memory-label">entries</span>
            </div>
          </div>

          <div class="memory-tier-card">
            <h3>Lessons Learned</h3>
            <div class="memory-stats">
              <span class="memory-count">${this.systemStatus?.memoryTiers?.lessons || 0}</span>
              <span class="memory-label">entries</span>
            </div>
          </div>
        </div>

        <div class="memory-actions">
          <button class="primary-btn" @click=${this.handleAddMemory}>
            ➕ Add Memory Entry
          </button>
          <button class="secondary-btn" @click=${this.handleExportMemory}>
            📥 Export Memory
          </button>
        </div>
      </div>
    `;
  }

  private renderAgentsSection() {
    return html`
      <div class="section-header">
        <h2>Agent Management</h2>
        <p>Configure and monitor your AutoGen agents</p>
      </div>

      <div class="agents-content">
        <div class="agents-toolbar">
          <button class="primary-btn" @click=${this.handleCreateAgent}>
            🤖 New Agent
          </button>
          <button class="secondary-btn" @click=${this.handleImportAgent}>
            📥 Import Config
          </button>
        </div>

        <div class="agents-grid">
          <div class="agent-card">
            <div class="agent-info">
              <h4>Research Assistant</h4>
              <span class="agent-type">UserProxy</span>
              <span class="agent-status active">Active</span>
            </div>
            <div class="agent-metrics">
              <span>Messages: 147</span>
              <span>Success Rate: 94%</span>
            </div>
            <div class="agent-actions">
              <button>Edit</button>
              <button>Clone</button>
              <button>Export</button>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  private renderSettingsSection() {
    return html`
      <div class="section-header">
        <h2>Settings</h2>
        <p>Configure your AutoGen MCP extension preferences</p>
      </div>

      <div class="settings-content">
        <div class="settings-group">
          <h3>Server Configuration</h3>
          <div class="setting-item">
            <label>Server URL</label>
            <input type="text" value="http://localhost:9000" />
          </div>
          <div class="setting-item">
            <label>Auto-start Server</label>
            <input type="checkbox" checked />
          </div>
        </div>

        <div class="settings-group">
          <h3>Dashboard Preferences</h3>
          <div class="setting-item">
            <label>Refresh Interval</label>
            <select>
              <option value="10">10 seconds</option>
              <option value="30" selected>30 seconds</option>
              <option value="60">1 minute</option>
            </select>
          </div>
        </div>

        <div class="settings-actions">
          <button class="primary-btn" @click=${this.handleSaveSettings}>
            💾 Save Settings
          </button>
          <button class="secondary-btn" @click=${this.handleResetSettings}>
            🔄 Reset to Defaults
          </button>
        </div>
      </div>
    `;
  }

  // Event handlers for new functionality
  private handleCreateSession() {
    vscode.postMessage({ command: 'createSession' });
  }

  private handleRefreshSessions() {
    vscode.postMessage({ command: 'refreshSessions' });
  }

  private handleAddMemory() {
    vscode.postMessage({ command: 'addMemory' });
  }

  private handleExportMemory() {
    vscode.postMessage({ command: 'exportMemory' });
  }

  private handleCreateAgent() {
    vscode.postMessage({ command: 'createAgent' });
  }

  private handleImportAgent() {
    vscode.postMessage({ command: 'importAgent' });
  }

  private handleSaveSettings() {
    vscode.postMessage({ command: 'saveSettings' });
  }

  private handleResetSettings() {
    vscode.postMessage({ command: 'resetSettings' });
  }
}

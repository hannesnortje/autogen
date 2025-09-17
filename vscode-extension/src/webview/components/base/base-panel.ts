import { html, css, CSSResultGroup } from 'lit';
import { property, state } from 'lit/decorators.js';
import { BaseComponent } from './base-component.js';

/**
 * Base panel component for main dashboard panels
 * Provides common panel functionality, header, actions, and content area
 */
export abstract class BasePanel extends BaseComponent {
  /**
   * Panel title displayed in header
   */
  @property({ type: String })
  title = '';

  /**
   * Panel subtitle or description
   */
  @property({ type: String })
  subtitle = '';

  /**
   * Whether the panel can be refreshed
   */
  @property({ type: Boolean })
  refreshable = true;

  /**
   * Whether the panel can be collapsed
   */
  @property({ type: Boolean })
  collapsible = false;

  /**
   * Collapsed state
   */
  @state()
  protected _collapsed = false;

  /**
   * Panel-specific styles
   */
  static panelStyles = css`
    :host {
      display: block;
      background-color: var(--vscode-editor-background);
      border: 1px solid var(--vscode-panel-border);
      border-radius: 4px;
      overflow: hidden;
    }

    .panel-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 16px 20px;
      background-color: var(--vscode-titleBar-inactiveBackground);
      border-bottom: 1px solid var(--vscode-panel-border);
    }

    .panel-title-section {
      flex: 1;
      min-width: 0;
    }

    .panel-title {
      font-size: 18px;
      font-weight: 600;
      margin: 0;
      color: var(--vscode-titleBar-activeForeground);
    }

    .panel-subtitle {
      font-size: 13px;
      margin: 4px 0 0 0;
      color: var(--vscode-descriptionForeground);
      opacity: 0.8;
    }

    .panel-actions {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .panel-content {
      padding: 20px;
      min-height: 200px;
    }

    .panel-content.collapsed {
      display: none;
    }

    .action-button {
      background: none;
      border: none;
      color: var(--vscode-titleBar-activeForeground);
      cursor: pointer;
      padding: 6px;
      border-radius: 3px;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .action-button:hover {
      background-color: var(--vscode-toolbar-hoverBackground);
    }

    .action-button:disabled {
      opacity: 0.4;
      cursor: not-allowed;
    }

    .expand-icon {
      transition: transform 0.2s ease;
    }

    .expand-icon.collapsed {
      transform: rotate(-90deg);
    }

    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 40px 20px;
      text-align: center;
      opacity: 0.6;
    }

    .empty-state-icon {
      font-size: 48px;
      margin-bottom: 16px;
      opacity: 0.5;
    }

    .empty-state-title {
      font-size: 16px;
      font-weight: 500;
      margin: 0 0 8px 0;
    }

    .empty-state-description {
      font-size: 14px;
      margin: 0 0 16px 0;
      max-width: 300px;
    }
  `;

  static get styles(): CSSResultGroup {
    return [super.styles, this.panelStyles];
  }

  /**
   * Abstract method to render panel content
   * Must be implemented by extending classes
   */
  protected abstract renderContent(): any;

  /**
   * Render panel actions (refresh, collapse, etc.)
   * Can be overridden by extending classes
   */
  protected renderActions() {
    return html`
      ${this.refreshable ? html`
        <button
          class="action-button"
          title="Refresh"
          @click="${this._handleRefresh}"
          ?disabled="${this._loading}"
        >
          🔄
        </button>
      ` : ''}

      ${this.collapsible ? html`
        <button
          class="action-button"
          title="${this._collapsed ? 'Expand' : 'Collapse'}"
          @click="${this._toggleCollapsed}"
        >
          <span class="expand-icon ${this._collapsed ? 'collapsed' : ''}">
            ▼
          </span>
        </button>
      ` : ''}
    `;
  }

  /**
   * Render empty state when no content is available
   * Can be overridden by extending classes
   */
  protected renderEmptyState(
    title = 'No data available',
    description = 'There is nothing to display at the moment.',
    icon = '📭'
  ) {
    return html`
      <div class="empty-state">
        <div class="empty-state-icon">${icon}</div>
        <div class="empty-state-title">${title}</div>
        <div class="empty-state-description">${description}</div>
        ${this.renderEmptyStateActions()}
      </div>
    `;
  }

  /**
   * Render actions for empty state
   * Can be overridden by extending classes
   */
  protected renderEmptyStateActions() {
    return html``;
  }

  /**
   * Main render method
   */
  render() {
    return html`
      <div class="panel-header">
        <div class="panel-title-section">
          <h2 class="panel-title">${this.title}</h2>
          ${this.subtitle ? html`
            <p class="panel-subtitle">${this.subtitle}</p>
          ` : ''}
        </div>
        <div class="panel-actions">
          ${this.renderActions()}
        </div>
      </div>

      <div class="panel-content ${this._collapsed ? 'collapsed' : ''}">
        ${this.renderError()}
        ${this._loading ? this.renderLoading() : this.renderContent()}
      </div>
    `;
  }

  /**
   * Handle refresh action
   * Can be overridden by extending classes
   */
  protected async _handleRefresh() {
    this.dispatchCustomEvent('panel-refresh', {
      panelType: this.tagName.toLowerCase()
    });

    // Override this method in extending classes to implement actual refresh logic
    await this.onRefresh();
  }

  /**
   * Refresh hook for extending classes
   */
  protected async onRefresh(): Promise<void> {
    // Default implementation - can be overridden
  }

  /**
   * Toggle collapsed state
   */
  protected _toggleCollapsed() {
    this._collapsed = !this._collapsed;
    this.dispatchCustomEvent('panel-toggle', {
      panelType: this.tagName.toLowerCase(),
      collapsed: this._collapsed
    });
  }

  /**
   * Programmatically set collapsed state
   */
  setCollapsed(collapsed: boolean) {
    this._collapsed = collapsed;
    this.requestUpdate();
  }

  /**
   * Get current collapsed state
   */
  get collapsed(): boolean {
    return this._collapsed;
  }
}

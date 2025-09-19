import { LitElement, html, css, CSSResultGroup } from 'lit';
import { property, state } from 'lit/decorators.js';

/**
 * Base component class for all AutoGen Lit 3 components
 * Provides common functionality and VS Code theme integration
 */
export abstract class BaseComponent extends LitElement {
  /**
   * Loading state for the component
   */
  @state()
  protected _loading = false;

  /**
   * Error state for the component
   */
  @state()
  protected _error: string | null = null;

  /**
   * Common VS Code theme styles
   */
  static baseStyles = css`
    :host {
      font-family: var(--vscode-font-family);
      font-size: var(--vscode-font-size);
      font-weight: var(--vscode-font-weight);
      color: var(--vscode-foreground);
      background-color: var(--vscode-editor-background);
    }

    .loading {
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
      opacity: 0.7;
    }

    .error {
      padding: 16px;
      margin: 8px 0;
      background-color: var(--vscode-inputValidation-errorBackground);
      border: 1px solid var(--vscode-inputValidation-errorBorder);
      border-radius: 4px;
      color: var(--vscode-inputValidation-errorForeground);
    }

    .hidden {
      display: none !important;
    }

    .btn {
      background-color: var(--vscode-button-background);
      color: var(--vscode-button-foreground);
      border: none;
      padding: 8px 16px;
      border-radius: 4px;
      cursor: pointer;
      font-size: var(--vscode-font-size);
      font-family: var(--vscode-font-family);
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: background-color 0.1s ease;
    }

    .btn:hover {
      background-color: var(--vscode-button-hoverBackground);
    }

    .btn:disabled {
      opacity: 0.4;
      cursor: not-allowed;
    }

    .btn.secondary {
      background-color: var(--vscode-button-secondaryBackground);
      color: var(--vscode-button-secondaryForeground);
    }

    .btn.secondary:hover {
      background-color: var(--vscode-button-secondaryHoverBackground);
    }

    .input {
      background-color: var(--vscode-input-background);
      color: var(--vscode-input-foreground);
      border: 1px solid var(--vscode-input-border);
      border-radius: 2px;
      padding: 6px 8px;
      font-size: var(--vscode-font-size);
      font-family: var(--vscode-font-family);
      width: 100%;
      box-sizing: border-box;
    }

    .input:focus {
      outline: none;
      border-color: var(--vscode-inputOption-activeBorder);
      box-shadow: 0 0 0 1px var(--vscode-inputOption-activeBorder);
    }

    .input::placeholder {
      color: var(--vscode-input-placeholderForeground);
    }
  `;

  /**
   * Combine base styles with component-specific styles
   */
  static get styles(): CSSResultGroup {
    return [this.baseStyles];
  }

  /**
   * Set loading state
   */
  protected setLoading(loading: boolean) {
    this._loading = loading;
    this.requestUpdate();
  }

  /**
   * Set error state
   */
  protected setError(error: string | null) {
    this._error = error;
    this.requestUpdate();
  }

  /**
   * Clear error state
   */
  protected clearError() {
    this._error = null;
    this.requestUpdate();
  }

  /**
   * Dispatch a custom event with proper typing
   */
  protected dispatchCustomEvent<T = any>(
    type: string,
    detail?: T,
    options?: CustomEventInit
  ) {
    const event = new CustomEvent(type, {
      detail,
      bubbles: true,
      composed: true,
      ...options
    });
    this.dispatchEvent(event);
  }

  /**
   * Render loading spinner
   */
  protected renderLoading() {
    return html`
      <div class="loading">
        <span>Loading...</span>
      </div>
    `;
  }

  /**
   * Render error message
   */
  protected renderError() {
    if (!this._error) return html``;

    return html`
      <div class="error">
        <strong>Error:</strong> ${this._error}
        <button class="btn secondary" @click="${this.clearError}" style="margin-left: 8px; padding: 4px 8px;">
          Dismiss
        </button>
      </div>
    `;
  }

  /**
   * Handle promise with loading and error states
   */
  protected async handleAsync<T>(
    promise: Promise<T>,
    errorPrefix = 'Operation failed'
  ): Promise<T | null> {
    try {
      this.setLoading(true);
      this.clearError();
      const result = await promise;
      return result;
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      this.setError(`${errorPrefix}: ${message}`);
      return null;
    } finally {
      this.setLoading(false);
    }
  }

  /**
   * Lifecycle: Component connected to DOM
   */
  connectedCallback() {
    super.connectedCallback();
    this.addEventListener('error', this._handleGlobalError.bind(this));
  }

  /**
   * Lifecycle: Component disconnected from DOM
   */
  disconnectedCallback() {
    super.disconnectedCallback();
    this.removeEventListener('error', this._handleGlobalError.bind(this));
  }

  /**
   * Global error handler
   */
  private _handleGlobalError(event: ErrorEvent) {
    console.error('Component error:', event.error);
    this.setError(`Unexpected error: ${event.error?.message || 'Unknown error'}`);
  }
}

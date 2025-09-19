import { html, css, CSSResultGroup } from 'lit';
import { property, state, query } from 'lit/decorators.js';
import { BaseComponent } from './base-component.js';

/**
 * Form validation result interface
 */
export interface ValidationResult {
  valid: boolean;
  errors: Record<string, string>;
}

/**
 * Base form component for all AutoGen forms
 * Provides form validation, submission handling, and consistent styling
 */
export abstract class BaseForm extends BaseComponent {
  /**
   * Form title
   */
  @property({ type: String })
  title = '';

  /**
   * Form subtitle or description
   */
  @property({ type: String })
  subtitle = '';

  /**
   * Whether form is in readonly mode
   */
  @property({ type: Boolean })
  readonly = false;

  /**
   * Form data (generic object)
   */
  @state()
  protected _formData: Record<string, any> = {};

  /**
   * Form validation errors
   */
  @state()
  protected _validationErrors: Record<string, string> = {};

  /**
   * Whether form has been submitted (for validation display)
   */
  @state()
  protected _submitted = false;

  /**
   * Whether form is currently submitting
   */
  @state()
  protected _submitting = false;

  /**
   * Form element reference
   */
  @query('form')
  protected _formElement!: HTMLFormElement;

  /**
   * Form-specific styles
   */
  static formStyles = css`
    :host {
      display: block;
      max-width: 600px;
    }

    .form-container {
      background-color: var(--vscode-editor-background);
      border: 1px solid var(--vscode-panel-border);
      border-radius: 4px;
      padding: 24px;
    }

    .form-header {
      margin-bottom: 24px;
      padding-bottom: 16px;
      border-bottom: 1px solid var(--vscode-panel-border);
    }

    .form-title {
      font-size: 20px;
      font-weight: 600;
      margin: 0 0 8px 0;
      color: var(--vscode-titleBar-activeForeground);
    }

    .form-subtitle {
      font-size: 14px;
      margin: 0;
      color: var(--vscode-descriptionForeground);
      opacity: 0.8;
    }

    .form-content {
      display: flex;
      flex-direction: column;
      gap: 20px;
    }

    .form-group {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .form-group.inline {
      flex-direction: row;
      align-items: center;
      gap: 12px;
    }

    .form-group.inline label {
      min-width: 120px;
      margin-bottom: 0;
    }

    .form-label {
      font-size: 13px;
      font-weight: 500;
      color: var(--vscode-foreground);
      margin-bottom: 4px;
    }

    .form-label.required::after {
      content: ' *';
      color: var(--vscode-errorForeground);
    }

    .form-input {
      background-color: var(--vscode-input-background);
      color: var(--vscode-input-foreground);
      border: 1px solid var(--vscode-input-border);
      border-radius: 2px;
      padding: 8px 12px;
      font-size: var(--vscode-font-size);
      font-family: var(--vscode-font-family);
      transition: border-color 0.1s ease;
    }

    .form-input:focus {
      outline: none;
      border-color: var(--vscode-inputOption-activeBorder);
      box-shadow: 0 0 0 1px var(--vscode-inputOption-activeBorder);
    }

    .form-input::placeholder {
      color: var(--vscode-input-placeholderForeground);
    }

    .form-input.error {
      border-color: var(--vscode-inputValidation-errorBorder);
      background-color: var(--vscode-inputValidation-errorBackground);
    }

    .form-input:disabled,
    .form-input[readonly] {
      opacity: 0.6;
      cursor: not-allowed;
      background-color: var(--vscode-input-background);
    }

    .form-textarea {
      min-height: 80px;
      resize: vertical;
      font-family: var(--vscode-font-family);
    }

    .form-select {
      background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3e%3cpath fill='%23666' d='M7 10l5 5 5-5z'/%3e%3c/svg%3e");
      background-repeat: no-repeat;
      background-position: right 8px center;
      background-size: 16px;
      padding-right: 32px;
      appearance: none;
    }

    .form-checkbox {
      width: auto;
      margin-right: 8px;
    }

    .form-error {
      font-size: 12px;
      color: var(--vscode-inputValidation-errorForeground);
      margin-top: 4px;
    }

    .form-help {
      font-size: 12px;
      color: var(--vscode-descriptionForeground);
      opacity: 0.8;
      margin-top: 4px;
    }

    .form-actions {
      display: flex;
      gap: 12px;
      justify-content: flex-end;
      margin-top: 24px;
      padding-top: 16px;
      border-top: 1px solid var(--vscode-panel-border);
    }

    .form-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 20px;
    }

    .form-section {
      margin-bottom: 24px;
    }

    .form-section-title {
      font-size: 16px;
      font-weight: 500;
      margin: 0 0 16px 0;
      color: var(--vscode-titleBar-activeForeground);
    }
  `;

  static get styles(): CSSResultGroup {
    return [super.styles, this.formStyles];
  }

  /**
   * Abstract method to render form fields
   * Must be implemented by extending classes
   */
  protected abstract renderFormFields(): any;

  /**
   * Abstract method to validate form data
   * Must be implemented by extending classes
   */
  protected abstract validateForm(): ValidationResult;

  /**
   * Abstract method to handle form submission
   * Must be implemented by extending classes
   */
  protected abstract onSubmit(formData: Record<string, any>): Promise<void>;

  /**
   * Main render method
   */
  render() {
    return html`
      <div class="form-container">
        ${this.title || this.subtitle ? html`
          <div class="form-header">
            ${this.title ? html`<h2 class="form-title">${this.title}</h2>` : ''}
            ${this.subtitle ? html`<p class="form-subtitle">${this.subtitle}</p>` : ''}
          </div>
        ` : ''}

        ${this.renderError()}

        <form @submit="${this._handleSubmit}" novalidate>
          <div class="form-content">
            ${this.renderFormFields()}
          </div>
          ${this.renderFormActions()}
        </form>
      </div>
    `;
  }

  /**
   * Render form actions (submit, cancel, etc.)
   * Can be overridden by extending classes
   */
  protected renderFormActions() {
    return html`
      <div class="form-actions">
        <button
          type="button"
          class="btn secondary"
          @click="${this._handleCancel}"
          ?disabled="${this._submitting}"
        >
          Cancel
        </button>
        <button
          type="submit"
          class="btn"
          ?disabled="${this._submitting || this.readonly}"
        >
          ${this._submitting ? 'Submitting...' : 'Submit'}
        </button>
      </div>
    `;
  }

  /**
   * Helper to render a form group with label, input, and error/help text
   */
  protected renderFormGroup(
    id: string,
    label: string,
    input: any,
    options: {
      required?: boolean;
      error?: string;
      help?: string;
      inline?: boolean;
    } = {}
  ) {
    const { required = false, error, help, inline = false } = options;
    const errorText = error || this._validationErrors[id];

    return html`
      <div class="form-group ${inline ? 'inline' : ''}">
        <label for="${id}" class="form-label ${required ? 'required' : ''}">
          ${label}
        </label>
        ${input}
        ${errorText ? html`<div class="form-error">${errorText}</div>` : ''}
        ${help ? html`<div class="form-help">${help}</div>` : ''}
      </div>
    `;
  }

  /**
   * Helper to create form input element
   */
  protected createInput(
    id: string,
    type: string = 'text',
    options: {
      placeholder?: string;
      required?: boolean;
      disabled?: boolean;
      value?: any;
    } = {}
  ) {
    const { placeholder = '', required = false, disabled = false, value = '' } = options;
    const hasError = this._submitted && this._validationErrors[id];

    return html`
      <input
        id="${id}"
        name="${id}"
        type="${type}"
        class="form-input ${hasError ? 'error' : ''}"
        placeholder="${placeholder}"
        ?required="${required}"
        ?disabled="${disabled || this.readonly}"
        .value="${value || this._formData[id] || ''}"
        @input="${this._handleInputChange}"
        @blur="${this._handleInputBlur}"
      />
    `;
  }

  /**
   * Helper to create textarea element
   */
  protected createTextarea(
    id: string,
    options: {
      placeholder?: string;
      required?: boolean;
      disabled?: boolean;
      rows?: number;
      value?: string;
    } = {}
  ) {
    const { placeholder = '', required = false, disabled = false, rows = 4, value = '' } = options;
    const hasError = this._submitted && this._validationErrors[id];

    return html`
      <textarea
        id="${id}"
        name="${id}"
        class="form-input form-textarea ${hasError ? 'error' : ''}"
        placeholder="${placeholder}"
        rows="${rows}"
        ?required="${required}"
        ?disabled="${disabled || this.readonly}"
        .value="${value || this._formData[id] || ''}"
        @input="${this._handleInputChange}"
        @blur="${this._handleInputBlur}"
      ></textarea>
    `;
  }

  /**
   * Helper to create select element
   */
  protected createSelect(
    id: string,
    options: Array<{ value: string; label: string }>,
    selectOptions: {
      required?: boolean;
      disabled?: boolean;
      placeholder?: string;
      value?: string;
    } = {}
  ) {
    const { required = false, disabled = false, placeholder = '', value = '' } = selectOptions;
    const hasError = this._submitted && this._validationErrors[id];

    return html`
      <select
        id="${id}"
        name="${id}"
        class="form-input form-select ${hasError ? 'error' : ''}"
        ?required="${required}"
        ?disabled="${disabled || this.readonly}"
        .value="${value || this._formData[id] || ''}"
        @change="${this._handleInputChange}"
      >
        ${placeholder ? html`<option value="">${placeholder}</option>` : ''}
        ${options.map(option => html`
          <option value="${option.value}" ?selected="${(value || this._formData[id]) === option.value}">
            ${option.label}
          </option>
        `)}
      </select>
    `;
  }

  /**
   * Handle input change events
   */
  protected _handleInputChange(event: Event) {
    const target = event.target as HTMLInputElement;
    const { name, value, type, checked } = target;

    this._formData = {
      ...this._formData,
      [name]: type === 'checkbox' ? checked : value
    };

    // Clear validation error for this field
    if (this._validationErrors[name]) {
      this._validationErrors = {
        ...this._validationErrors,
        [name]: ''
      };
      delete this._validationErrors[name];
    }

    this.requestUpdate();
  }

  /**
   * Handle input blur events (for validation)
   */
  protected _handleInputBlur(event: Event) {
    if (!this._submitted) return;

    const target = event.target as HTMLInputElement;
    const validation = this.validateForm();

    if (validation.errors[target.name]) {
      this._validationErrors = {
        ...this._validationErrors,
        [target.name]: validation.errors[target.name]
      };
      this.requestUpdate();
    }
  }

  /**
   * Handle form submission
   */
  protected async _handleSubmit(event: Event) {
    event.preventDefault();
    this._submitted = true;

    const validation = this.validateForm();
    this._validationErrors = validation.errors;

    if (!validation.valid) {
      this.requestUpdate();
      return;
    }

    try {
      this._submitting = true;
      await this.onSubmit(this._formData);
      this.dispatchCustomEvent('form-submitted', this._formData);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      this.setError(`Submission failed: ${message}`);
    } finally {
      this._submitting = false;
      this.requestUpdate();
    }
  }

  /**
   * Handle form cancellation
   */
  protected _handleCancel() {
    this.dispatchCustomEvent('form-cancelled');
  }

  /**
   * Set form data programmatically
   */
  setFormData(data: Record<string, any>) {
    this._formData = { ...data };
    this._validationErrors = {};
    this._submitted = false;
    this.requestUpdate();
  }

  /**
   * Get current form data
   */
  getFormData(): Record<string, any> {
    return { ...this._formData };
  }

  /**
   * Reset form to initial state
   */
  reset() {
    this._formData = {};
    this._validationErrors = {};
    this._submitted = false;
    this._submitting = false;
    this.clearError();
    this.requestUpdate();

    // Reset native form
    if (this._formElement) {
      this._formElement.reset();
    }
  }

  /**
   * Validate form programmatically
   */
  validate(): boolean {
    this._submitted = true;
    const validation = this.validateForm();
    this._validationErrors = validation.errors;
    this.requestUpdate();
    return validation.valid;
  }
}

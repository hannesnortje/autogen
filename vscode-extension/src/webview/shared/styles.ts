import { css } from 'lit';

/**
 * Shared CSS styles for AutoGen extension components
 * Provides consistent styling and VS Code theme integration
 */

/**
 * VS Code theme CSS custom properties
 * These are automatically populated by VS Code's webview context
 */
export const vscodeThemeVariables = css`
  :host {
    /* Fonts */
    --vscode-font-family: var(--vscode-font-family, 'Segoe WPC', 'Segoe UI', sans-serif);
    --vscode-font-size: var(--vscode-font-size, 13px);
    --vscode-font-weight: var(--vscode-font-weight, normal);
    --vscode-editor-font-family: var(--vscode-editor-font-family, 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace);

    /* Colors - Background */
    --vscode-foreground: var(--vscode-foreground, #cccccc);
    --vscode-background: var(--vscode-background, #1e1e1e);
    --vscode-editor-background: var(--vscode-editor-background, #1e1e1e);
    --vscode-editor-foreground: var(--vscode-editor-foreground, #d4d4d4);

    /* Colors - UI Elements */
    --vscode-titleBar-activeForeground: var(--vscode-titleBar-activeForeground, #cccccc);
    --vscode-titleBar-inactiveBackground: var(--vscode-titleBar-inactiveBackground, #3c3c3c);
    --vscode-descriptionForeground: var(--vscode-descriptionForeground, #cccccc99);

    /* Colors - Buttons */
    --vscode-button-background: var(--vscode-button-background, #0e639c);
    --vscode-button-foreground: var(--vscode-button-foreground, #ffffff);
    --vscode-button-hoverBackground: var(--vscode-button-hoverBackground, #1177bb);
    --vscode-button-secondaryBackground: var(--vscode-button-secondaryBackground, #5a5d5e);
    --vscode-button-secondaryForeground: var(--vscode-button-secondaryForeground, #ffffff);
    --vscode-button-secondaryHoverBackground: var(--vscode-button-secondaryHoverBackground, #666868);

    /* Colors - Input */
    --vscode-input-background: var(--vscode-input-background, #3c3c3c);
    --vscode-input-foreground: var(--vscode-input-foreground, #cccccc);
    --vscode-input-border: var(--vscode-input-border, #3c3c3c);
    --vscode-input-placeholderForeground: var(--vscode-input-placeholderForeground, #cccccc80);
    --vscode-inputOption-activeBorder: var(--vscode-inputOption-activeBorder, #007acc);

    /* Colors - Validation */
    --vscode-inputValidation-errorBackground: var(--vscode-inputValidation-errorBackground, #5a1d1d);
    --vscode-inputValidation-errorBorder: var(--vscode-inputValidation-errorBorder, #be1100);
    --vscode-inputValidation-errorForeground: var(--vscode-inputValidation-errorForeground, #f48771);
    --vscode-inputValidation-warningBackground: var(--vscode-inputValidation-warningBackground, #352a05);
    --vscode-inputValidation-warningBorder: var(--vscode-inputValidation-warningBorder, #cc6d00);
    --vscode-inputValidation-warningForeground: var(--vscode-inputValidation-warningForeground, #ffcc00);

    /* Colors - Panel */
    --vscode-panel-background: var(--vscode-panel-background, #1e1e1e);
    --vscode-panel-border: var(--vscode-panel-border, #454545);
    --vscode-panelTitle-activeForeground: var(--vscode-panelTitle-activeForeground, #e7e7e7);
    --vscode-panelTitle-inactiveForeground: var(--vscode-panelTitle-inactiveForeground, #e7e7e799);

    /* Colors - List & Tree */
    --vscode-list-activeSelectionBackground: var(--vscode-list-activeSelectionBackground, #094771);
    --vscode-list-activeSelectionForeground: var(--vscode-list-activeSelectionForeground, #ffffff);
    --vscode-list-hoverBackground: var(--vscode-list-hoverBackground, #2a2d2e);
    --vscode-list-focusBackground: var(--vscode-list-focusBackground, #062f4a);

    /* Colors - Status */
    --vscode-errorForeground: var(--vscode-errorForeground, #f48771);
    --vscode-warningForeground: var(--vscode-warningForeground, #ffcc00);
    --vscode-charts-green: var(--vscode-charts-green, #89d185);
    --vscode-charts-red: var(--vscode-charts-red, #f48771);
    --vscode-charts-yellow: var(--vscode-charts-yellow, #ffcc00);
    --vscode-charts-blue: var(--vscode-charts-blue, #75beff);

    /* Colors - Toolbar */
    --vscode-toolbar-hoverBackground: var(--vscode-toolbar-hoverBackground, #5a5d5e14);
    --vscode-toolbar-activeBackground: var(--vscode-toolbar-activeBackground, #5a5d5e28);

    /* Colors - Badge */
    --vscode-badge-background: var(--vscode-badge-background, #4d4d4d);
    --vscode-badge-foreground: var(--vscode-badge-foreground, #ffffff);

    /* Colors - Progress */
    --vscode-progressBar-background: var(--vscode-progressBar-background, #0e639c);
  }
`;

/**
 * Common layout utilities
 */
export const layoutStyles = css`
  .flex {
    display: flex;
  }

  .flex-column {
    display: flex;
    flex-direction: column;
  }

  .flex-row {
    display: flex;
    flex-direction: row;
  }

  .flex-center {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .flex-between {
    display: flex;
    justify-content: space-between;
  }

  .flex-start {
    display: flex;
    justify-content: flex-start;
  }

  .flex-end {
    display: flex;
    justify-content: flex-end;
  }

  .flex-wrap {
    flex-wrap: wrap;
  }

  .flex-nowrap {
    flex-wrap: nowrap;
  }

  .flex-grow {
    flex-grow: 1;
  }

  .flex-shrink {
    flex-shrink: 1;
  }

  .align-center {
    align-items: center;
  }

  .align-start {
    align-items: flex-start;
  }

  .align-end {
    align-items: flex-end;
  }

  .gap-xs { gap: 4px; }
  .gap-sm { gap: 8px; }
  .gap-md { gap: 12px; }
  .gap-lg { gap: 16px; }
  .gap-xl { gap: 24px; }
`;

/**
 * Spacing utilities
 */
export const spacingStyles = css`
  .m-0 { margin: 0; }
  .m-xs { margin: 4px; }
  .m-sm { margin: 8px; }
  .m-md { margin: 12px; }
  .m-lg { margin: 16px; }
  .m-xl { margin: 24px; }

  .mt-0 { margin-top: 0; }
  .mt-xs { margin-top: 4px; }
  .mt-sm { margin-top: 8px; }
  .mt-md { margin-top: 12px; }
  .mt-lg { margin-top: 16px; }
  .mt-xl { margin-top: 24px; }

  .mb-0 { margin-bottom: 0; }
  .mb-xs { margin-bottom: 4px; }
  .mb-sm { margin-bottom: 8px; }
  .mb-md { margin-bottom: 12px; }
  .mb-lg { margin-bottom: 16px; }
  .mb-xl { margin-bottom: 24px; }

  .ml-0 { margin-left: 0; }
  .ml-xs { margin-left: 4px; }
  .ml-sm { margin-left: 8px; }
  .ml-md { margin-left: 12px; }
  .ml-lg { margin-left: 16px; }
  .ml-xl { margin-left: 24px; }

  .mr-0 { margin-right: 0; }
  .mr-xs { margin-right: 4px; }
  .mr-sm { margin-right: 8px; }
  .mr-md { margin-right: 12px; }
  .mr-lg { margin-right: 16px; }
  .mr-xl { margin-right: 24px; }

  .p-0 { padding: 0; }
  .p-xs { padding: 4px; }
  .p-sm { padding: 8px; }
  .p-md { padding: 12px; }
  .p-lg { padding: 16px; }
  .p-xl { padding: 24px; }

  .pt-0 { padding-top: 0; }
  .pt-xs { padding-top: 4px; }
  .pt-sm { padding-top: 8px; }
  .pt-md { padding-top: 12px; }
  .pt-lg { padding-top: 16px; }
  .pt-xl { padding-top: 24px; }

  .pb-0 { padding-bottom: 0; }
  .pb-xs { padding-bottom: 4px; }
  .pb-sm { padding-bottom: 8px; }
  .pb-md { padding-bottom: 12px; }
  .pb-lg { padding-bottom: 16px; }
  .pb-xl { padding-bottom: 24px; }

  .pl-0 { padding-left: 0; }
  .pl-xs { padding-left: 4px; }
  .pl-sm { padding-left: 8px; }
  .pl-md { padding-left: 12px; }
  .pl-lg { padding-left: 16px; }
  .pl-xl { padding-left: 24px; }

  .pr-0 { padding-right: 0; }
  .pr-xs { padding-right: 4px; }
  .pr-sm { padding-right: 8px; }
  .pr-md { padding-right: 12px; }
  .pr-lg { padding-right: 16px; }
  .pr-xl { padding-right: 24px; }
`;

/**
 * Typography utilities
 */
export const typographyStyles = css`
  .text-xs { font-size: 11px; }
  .text-sm { font-size: 12px; }
  .text-base { font-size: var(--vscode-font-size, 13px); }
  .text-lg { font-size: 14px; }
  .text-xl { font-size: 16px; }
  .text-2xl { font-size: 18px; }
  .text-3xl { font-size: 20px; }
  .text-4xl { font-size: 24px; }

  .font-light { font-weight: 300; }
  .font-normal { font-weight: normal; }
  .font-medium { font-weight: 500; }
  .font-semibold { font-weight: 600; }
  .font-bold { font-weight: bold; }

  .text-left { text-align: left; }
  .text-center { text-align: center; }
  .text-right { text-align: right; }

  .text-truncate {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .text-wrap {
    white-space: normal;
    word-wrap: break-word;
  }

  .text-nowrap {
    white-space: nowrap;
  }

  .text-uppercase {
    text-transform: uppercase;
  }

  .text-lowercase {
    text-transform: lowercase;
  }

  .text-capitalize {
    text-transform: capitalize;
  }
`;

/**
 * State and interaction utilities
 */
export const stateStyles = css`
  .hidden {
    display: none !important;
  }

  .invisible {
    visibility: hidden;
  }

  .opacity-0 { opacity: 0; }
  .opacity-25 { opacity: 0.25; }
  .opacity-50 { opacity: 0.5; }
  .opacity-75 { opacity: 0.75; }
  .opacity-100 { opacity: 1; }

  .pointer-events-none {
    pointer-events: none;
  }

  .pointer-events-auto {
    pointer-events: auto;
  }

  .cursor-pointer {
    cursor: pointer;
  }

  .cursor-not-allowed {
    cursor: not-allowed;
  }

  .cursor-default {
    cursor: default;
  }

  .select-none {
    user-select: none;
  }

  .select-text {
    user-select: text;
  }

  .select-all {
    user-select: all;
  }
`;

/**
 * Common component styles
 */
export const componentStyles = css`
  /* Card-like containers */
  .card {
    background-color: var(--vscode-editor-background);
    border: 1px solid var(--vscode-panel-border);
    border-radius: 4px;
    overflow: hidden;
  }

  .card-header {
    padding: 16px 20px;
    border-bottom: 1px solid var(--vscode-panel-border);
    background-color: var(--vscode-titleBar-inactiveBackground);
  }

  .card-body {
    padding: 20px;
  }

  .card-footer {
    padding: 16px 20px;
    border-top: 1px solid var(--vscode-panel-border);
    background-color: var(--vscode-titleBar-inactiveBackground);
  }

  /* Dividers */
  .divider {
    height: 1px;
    background-color: var(--vscode-panel-border);
    margin: 16px 0;
  }

  .divider-vertical {
    width: 1px;
    background-color: var(--vscode-panel-border);
    margin: 0 16px;
  }

  /* Status indicators */
  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
    margin-right: 6px;
  }

  .status-dot.success {
    background-color: var(--vscode-charts-green);
  }

  .status-dot.error {
    background-color: var(--vscode-charts-red);
  }

  .status-dot.warning {
    background-color: var(--vscode-charts-yellow);
  }

  .status-dot.info {
    background-color: var(--vscode-charts-blue);
  }

  .status-dot.inactive {
    background-color: var(--vscode-descriptionForeground);
    opacity: 0.5;
  }

  /* Loading spinner */
  .spinner {
    display: inline-block;
    width: 16px;
    height: 16px;
    border: 2px solid var(--vscode-panel-border);
    border-radius: 50%;
    border-top-color: var(--vscode-progressBar-background);
    animation: spin 1s ease-in-out infinite;
  }

  .spinner-large {
    width: 24px;
    height: 24px;
    border-width: 3px;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  /* Transitions */
  .transition {
    transition: all 0.15s ease-in-out;
  }

  .transition-colors {
    transition: color 0.15s ease-in-out, background-color 0.15s ease-in-out, border-color 0.15s ease-in-out;
  }

  .transition-opacity {
    transition: opacity 0.15s ease-in-out;
  }

  .transition-transform {
    transition: transform 0.15s ease-in-out;
  }
`;

/**
 * All shared styles combined
 */
export const sharedStyles = css`
  ${vscodeThemeVariables}
  ${layoutStyles}
  ${spacingStyles}
  ${typographyStyles}
  ${stateStyles}
  ${componentStyles}
`;

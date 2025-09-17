import { css } from 'lit';

/**
 * VS Code theme integration for AutoGen extension
 * Handles theme detection, switching, and provides theme-aware utilities
 */

/**
 * Theme types supported by VS Code
 */
export enum VSCodeTheme {
  DARK = 'dark',
  LIGHT = 'light',
  HIGH_CONTRAST_DARK = 'hc-black',
  HIGH_CONTRAST_LIGHT = 'hc-light'
}

/**
 * Theme detection utility
 */
export class ThemeManager {
  private static _instance: ThemeManager;
  private _currentTheme: VSCodeTheme = VSCodeTheme.DARK;
  private _observers: Set<(theme: VSCodeTheme) => void> = new Set();

  private constructor() {
    this.detectTheme();
    this.setupThemeObserver();
  }

  static getInstance(): ThemeManager {
    if (!this._instance) {
      this._instance = new ThemeManager();
    }
    return this._instance;
  }

  /**
   * Get current theme
   */
  get currentTheme(): VSCodeTheme {
    return this._currentTheme;
  }

  /**
   * Check if current theme is dark
   */
  get isDark(): boolean {
    return this._currentTheme === VSCodeTheme.DARK ||
           this._currentTheme === VSCodeTheme.HIGH_CONTRAST_DARK;
  }

  /**
   * Check if current theme is light
   */
  get isLight(): boolean {
    return this._currentTheme === VSCodeTheme.LIGHT ||
           this._currentTheme === VSCodeTheme.HIGH_CONTRAST_LIGHT;
  }

  /**
   * Check if current theme is high contrast
   */
  get isHighContrast(): boolean {
    return this._currentTheme === VSCodeTheme.HIGH_CONTRAST_DARK ||
           this._currentTheme === VSCodeTheme.HIGH_CONTRAST_LIGHT;
  }

  /**
   * Detect current theme from body class or CSS variables
   */
  private detectTheme() {
    // Check body classes first
    const body = document.body;

    if (body.classList.contains('vscode-dark')) {
      this._currentTheme = VSCodeTheme.DARK;
    } else if (body.classList.contains('vscode-light')) {
      this._currentTheme = VSCodeTheme.LIGHT;
    } else if (body.classList.contains('vscode-high-contrast')) {
      this._currentTheme = VSCodeTheme.HIGH_CONTRAST_DARK;
    } else if (body.classList.contains('vscode-high-contrast-light')) {
      this._currentTheme = VSCodeTheme.HIGH_CONTRAST_LIGHT;
    } else {
      // Fallback: detect from CSS variables
      const backgroundColor = getComputedStyle(document.documentElement)
        .getPropertyValue('--vscode-editor-background').trim();

      if (backgroundColor) {
        // Convert hex/rgb to determine if dark/light
        const isLightBackground = this.isLightColor(backgroundColor);
        this._currentTheme = isLightBackground ? VSCodeTheme.LIGHT : VSCodeTheme.DARK;
      }
    }
  }

  /**
   * Setup theme change observer
   */
  private setupThemeObserver() {
    // Watch for changes in body class
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
          const oldTheme = this._currentTheme;
          this.detectTheme();
          if (oldTheme !== this._currentTheme) {
            this.notifyThemeChange();
          }
        }
      });
    });

    observer.observe(document.body, {
      attributes: true,
      attributeFilter: ['class']
    });

    // Also watch for CSS variable changes
    const style = document.documentElement;
    const styleObserver = new MutationObserver(() => {
      const oldTheme = this._currentTheme;
      this.detectTheme();
      if (oldTheme !== this._currentTheme) {
        this.notifyThemeChange();
      }
    });

    styleObserver.observe(style, {
      attributes: true,
      attributeFilter: ['style']
    });
  }

  /**
   * Determine if a color is light or dark
   */
  private isLightColor(color: string): boolean {
    // Convert color to RGB values
    let r: number, g: number, b: number;

    if (color.startsWith('#')) {
      // Hex color
      const hex = color.slice(1);
      r = parseInt(hex.substr(0, 2), 16);
      g = parseInt(hex.substr(2, 2), 16);
      b = parseInt(hex.substr(4, 2), 16);
    } else if (color.startsWith('rgb')) {
      // RGB/RGBA color
      const values = color.match(/\d+/g);
      if (values && values.length >= 3) {
        r = parseInt(values[0]);
        g = parseInt(values[1]);
        b = parseInt(values[2]);
      } else {
        return false; // Default to dark if can't parse
      }
    } else {
      return false; // Default to dark for unknown formats
    }

    // Calculate luminance
    const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
    return luminance > 0.5;
  }

  /**
   * Subscribe to theme changes
   */
  subscribe(callback: (theme: VSCodeTheme) => void): () => void {
    this._observers.add(callback);

    // Return unsubscribe function
    return () => {
      this._observers.delete(callback);
    };
  }

  /**
   * Notify all observers of theme change
   */
  private notifyThemeChange() {
    this._observers.forEach(callback => {
      try {
        callback(this._currentTheme);
      } catch (error) {
        console.error('Error in theme change callback:', error);
      }
    });
  }
}

/**
 * Theme-specific CSS styles
 */
export const themeStyles = css`
  /* Dark theme specific styles */
  :host(.theme-dark) {
    --autogen-shadow-light: rgba(0, 0, 0, 0.3);
    --autogen-shadow-medium: rgba(0, 0, 0, 0.5);
    --autogen-shadow-heavy: rgba(0, 0, 0, 0.7);
    --autogen-overlay: rgba(0, 0, 0, 0.5);
    --autogen-glass: rgba(255, 255, 255, 0.05);
  }

  /* Light theme specific styles */
  :host(.theme-light) {
    --autogen-shadow-light: rgba(0, 0, 0, 0.1);
    --autogen-shadow-medium: rgba(0, 0, 0, 0.15);
    --autogen-shadow-heavy: rgba(0, 0, 0, 0.25);
    --autogen-overlay: rgba(0, 0, 0, 0.3);
    --autogen-glass: rgba(0, 0, 0, 0.03);
  }

  /* High contrast theme specific styles */
  :host(.theme-high-contrast) {
    --autogen-shadow-light: rgba(0, 0, 0, 0.8);
    --autogen-shadow-medium: rgba(0, 0, 0, 0.9);
    --autogen-shadow-heavy: rgba(0, 0, 0, 1);
    --autogen-overlay: rgba(0, 0, 0, 0.8);
    --autogen-glass: transparent;
  }

  /* Common shadow utilities */
  .shadow-sm {
    box-shadow: 0 1px 2px var(--autogen-shadow-light);
  }

  .shadow-md {
    box-shadow: 0 2px 4px var(--autogen-shadow-medium);
  }

  .shadow-lg {
    box-shadow: 0 4px 8px var(--autogen-shadow-medium);
  }

  .shadow-xl {
    box-shadow: 0 8px 16px var(--autogen-shadow-heavy);
  }

  .shadow-inner {
    box-shadow: inset 0 1px 2px var(--autogen-shadow-light);
  }

  /* Glass effect */
  .glass {
    background-color: var(--autogen-glass);
    backdrop-filter: blur(8px);
    border: 1px solid var(--vscode-panel-border);
  }

  /* Overlay */
  .overlay {
    background-color: var(--autogen-overlay);
  }
`;

/**
 * Theme-aware mixin for components
 */
export const themeMixin = css`
  ${themeStyles}

  /* Automatic theme class application based on VS Code theme */
  :host {
    /* Will be dynamically updated by ThemeManager */
  }
`;

/**
 * Utility function to apply theme class to component
 */
export function applyThemeClass(element: HTMLElement) {
  const themeManager = ThemeManager.getInstance();

  const updateThemeClass = (theme: VSCodeTheme) => {
    // Remove existing theme classes
    element.classList.remove('theme-dark', 'theme-light', 'theme-high-contrast');

    // Add current theme class
    switch (theme) {
      case VSCodeTheme.DARK:
        element.classList.add('theme-dark');
        break;
      case VSCodeTheme.LIGHT:
        element.classList.add('theme-light');
        break;
      case VSCodeTheme.HIGH_CONTRAST_DARK:
      case VSCodeTheme.HIGH_CONTRAST_LIGHT:
        element.classList.add('theme-high-contrast');
        break;
    }
  };

  // Apply current theme
  updateThemeClass(themeManager.currentTheme);

  // Subscribe to theme changes
  const unsubscribe = themeManager.subscribe(updateThemeClass);

  // Return cleanup function
  return unsubscribe;
}

/**
 * Reactive theme property decorator for Lit components
 */
export function themeProperty() {
  return function(target: any, propertyKey: string) {
    const themeManager = ThemeManager.getInstance();

    // Define getter/setter
    Object.defineProperty(target, propertyKey, {
      get() {
        return themeManager.currentTheme;
      },
      enumerable: true,
      configurable: true
    });

    // Setup theme change subscription in connectedCallback
    const originalConnectedCallback = target.connectedCallback;
    target.connectedCallback = function() {
      if (originalConnectedCallback) {
        originalConnectedCallback.call(this);
      }

      // Subscribe to theme changes and trigger re-render
      this._themeUnsubscribe = themeManager.subscribe(() => {
        this.requestUpdate(propertyKey);
      });

      // Apply theme class
      this._themeClassUnsubscribe = applyThemeClass(this);
    };

    // Cleanup in disconnectedCallback
    const originalDisconnectedCallback = target.disconnectedCallback;
    target.disconnectedCallback = function() {
      if (originalDisconnectedCallback) {
        originalDisconnectedCallback.call(this);
      }

      if (this._themeUnsubscribe) {
        this._themeUnsubscribe();
      }

      if (this._themeClassUnsubscribe) {
        this._themeClassUnsubscribe();
      }
    };
  };
}

/**
 * Export theme manager instance for global use
 */
export const themeManager = ThemeManager.getInstance();

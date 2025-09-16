import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';

@customElement('dashboard-footer')
export class DashboardFooter extends LitElement {
  static styles = css`
    :host {
      display: block;
      margin-top: 30px;
    }

    .footer {
      padding: 20px;
      background-color: var(--vscode-editorWidget-background);
      border-radius: 8px;
      border: 1px solid var(--vscode-editorWidget-border);
      text-align: center;
    }

    .footer-content {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
    }

    .footer-section {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 12px;
      color: var(--vscode-descriptionForeground);
    }

    .footer-icon {
      width: 14px;
      height: 14px;
      fill: currentColor;
    }

    .version-info {
      font-weight: 500;
    }

    .status-info {
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background-color: var(--vscode-testing-iconPassed);
    }

    .footer-links {
      display: flex;
      gap: 16px;
      flex-wrap: wrap;
    }

    .footer-link {
      color: var(--vscode-textLink-foreground);
      text-decoration: none;
      font-size: 12px;
      cursor: pointer;
    }

    .footer-link:hover {
      color: var(--vscode-textLink-activeForeground);
      text-decoration: underline;
    }

    .copyright {
      margin-top: 16px;
      font-size: 11px;
      color: var(--vscode-descriptionForeground);
      opacity: 0.7;
    }

    @media (max-width: 600px) {
      .footer-content {
        flex-direction: column;
        text-align: center;
      }
    }
  `;

  @state()
  private currentTime = new Date();

  connectedCallback() {
    super.connectedCallback();
    // Update time every minute
    setInterval(() => {
      this.currentTime = new Date();
    }, 60000);
  }

  private handleLinkClick(action: string) {
    if (typeof vscode !== 'undefined') {
      vscode.postMessage({
        command: action
      });
    }
  }

  private formatTime(date: Date): string {
    return date.toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    });
  }

  render() {
    return html`
      <div class="footer">
        <div class="footer-content">
          <div class="footer-section">
            <svg class="footer-icon" viewBox="0 0 16 16">
              <path d="M8 16A8 8 0 1 0 8 0a8 8 0 0 0 0 16zm.93-9.412-1 4.705c-.07.34-.504.653-.804.653-.3 0-.734-.313-.804-.653l-1-4.705c-.17-.827.648-1.538 1.317-1.538h1.975c.67 0 1.487.711 1.316 1.538z"/>
            </svg>
            <span class="version-info">AutoGen MCP v2.0.0</span>
          </div>

          <div class="footer-section status-info">
            <span class="status-dot"></span>
            <span>Dashboard Active • ${this.formatTime(this.currentTime)}</span>
          </div>

          <div class="footer-links">
            <a class="footer-link" @click=${() => this.handleLinkClick('openDocumentation')}>
              Documentation
            </a>
            <a class="footer-link" @click=${() => this.handleLinkClick('openGithub')}>
              GitHub
            </a>
            <a class="footer-link" @click=${() => this.handleLinkClick('reportIssue')}>
              Report Issue
            </a>
            <a class="footer-link" @click=${() => this.handleLinkClick('openSettings')}>
              Settings
            </a>
          </div>
        </div>

        <div class="copyright">
          © 2025 AutoGen MCP Dashboard. Built with Lit 3 and VS Code Extensions API.
        </div>
      </div>
    `;
  }
}

// VS Code webview API types
declare const vscode: {
  postMessage(message: any): void;
};

import * as vscode from 'vscode';

/**
 * AutoGen Agile Assistant Extension
 * Main extension entry point that initializes the AutoGen integration
 */

let outputChannel: vscode.OutputChannel;

/**
 * Extension activation function
 * Called when the extension is first activated
 */
export function activate(context: vscode.ExtensionContext) {
    console.log('AutoGen Agile Assistant is now active');

    // Create output channel for logging
    outputChannel = vscode.window.createOutputChannel('AutoGen Agile');
    outputChannel.appendLine('AutoGen Agile Assistant activated');

    // Register commands
    registerCommands(context);

    // Initialize extension state
    initializeExtension(context);

    // Show welcome message for first activation
    showWelcomeMessage(context);
}

/**
 * Extension deactivation function
 * Called when the extension is deactivated
 */
export function deactivate() {
    console.log('AutoGen Agile Assistant is now deactivated');
    if (outputChannel) {
        outputChannel.dispose();
    }
}

/**
 * Register all extension commands
 */
function registerCommands(context: vscode.ExtensionContext) {
    // Open Dashboard command
    const openDashboardCommand = vscode.commands.registerCommand('autoGenAgile.openDashboard', () => {
        outputChannel.appendLine('Opening AutoGen Dashboard...');
        vscode.window.showInformationMessage('AutoGen Dashboard will be available in the next step!');
    });

    // Refresh Sidebar command
    const refreshSidebarCommand = vscode.commands.registerCommand('autoGenAgile.refreshSidebar', () => {
        outputChannel.appendLine('Refreshing AutoGen Sidebar...');
        vscode.window.showInformationMessage('AutoGen Sidebar refresh requested');
    });

    context.subscriptions.push(openDashboardCommand, refreshSidebarCommand);
}

/**
 * Initialize extension with basic state
 */
function initializeExtension(context: vscode.ExtensionContext) {
    // Set context for conditional view visibility
    vscode.commands.executeCommand('setContext', 'workspaceHasAutoGenConfig', true);

    // Log configuration
    const config = vscode.workspace.getConfiguration('autoGenAgile');
    const mcpServerUrl = config.get<string>('mcpServerUrl', 'ws://localhost:9000');
    const enableAutoRefresh = config.get<boolean>('enableAutoRefresh', true);
    const refreshInterval = config.get<number>('refreshInterval', 30000);

    outputChannel.appendLine(`Configuration loaded:`);
    outputChannel.appendLine(`  - MCP Server URL: ${mcpServerUrl}`);
    outputChannel.appendLine(`  - Auto Refresh: ${enableAutoRefresh}`);
    outputChannel.appendLine(`  - Refresh Interval: ${refreshInterval}ms`);
}

/**
 * Show welcome message for new users
 */
function showWelcomeMessage(context: vscode.ExtensionContext) {
    const hasShownWelcome = context.globalState.get('hasShownWelcome', false);

    if (!hasShownWelcome) {
        vscode.window.showInformationMessage(
            'Welcome to AutoGen Agile Assistant! 🚀',
            'Open Dashboard',
            'Learn More'
        ).then((selection: string | undefined) => {
            switch (selection) {
                case 'Open Dashboard':
                    vscode.commands.executeCommand('autoGenAgile.openDashboard');
                    break;
                case 'Learn More':
                    vscode.env.openExternal(vscode.Uri.parse('https://github.com/hannesnortje/autogen'));
                    break;
            }
        });

        context.globalState.update('hasShownWelcome', true);
    }
}

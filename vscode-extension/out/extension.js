"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
/**
 * AutoGen Agile Assistant Extension
 * Main extension entry point that initializes the AutoGen integration
 */
let outputChannel;
/**
 * Extension activation function
 * Called when the extension is first activated
 */
function activate(context) {
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
function deactivate() {
    console.log('AutoGen Agile Assistant is now deactivated');
    if (outputChannel) {
        outputChannel.dispose();
    }
}
/**
 * Register all extension commands
 */
function registerCommands(context) {
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
function initializeExtension(context) {
    // Set context for conditional view visibility
    vscode.commands.executeCommand('setContext', 'workspaceHasAutoGenConfig', true);
    // Log configuration
    const config = vscode.workspace.getConfiguration('autoGenAgile');
    const mcpServerUrl = config.get('mcpServerUrl', 'ws://localhost:9000');
    const enableAutoRefresh = config.get('enableAutoRefresh', true);
    const refreshInterval = config.get('refreshInterval', 30000);
    outputChannel.appendLine(`Configuration loaded:`);
    outputChannel.appendLine(`  - MCP Server URL: ${mcpServerUrl}`);
    outputChannel.appendLine(`  - Auto Refresh: ${enableAutoRefresh}`);
    outputChannel.appendLine(`  - Refresh Interval: ${refreshInterval}ms`);
}
/**
 * Show welcome message for new users
 */
function showWelcomeMessage(context) {
    const hasShownWelcome = context.globalState.get('hasShownWelcome', false);
    if (!hasShownWelcome) {
        vscode.window.showInformationMessage('Welcome to AutoGen Agile Assistant! 🚀', 'Open Dashboard', 'Learn More').then((selection) => {
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
//# sourceMappingURL=extension.js.map

import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs/promises';

export interface AutogenWorkspaceConfig {
    autogen: {
        serverPath: string;
        workingDirectory: string;
        port?: number;
        timeout?: number;
    };
}

export class SimpleWorkspaceConfiguration {
    private outputChannel: vscode.OutputChannel;

    constructor(outputChannel: vscode.OutputChannel) {
        this.outputChannel = outputChannel;
    }

    /**
     * Initialize workspace configurations for all open workspace folders
     */
    async initializeWorkspaces(): Promise<void> {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders) {
            this.outputChannel.appendLine('No workspace folders open');
            return;
        }

        for (const folder of workspaceFolders) {
            await this.configureWorkspace(folder.uri.fsPath);
        }
    }

    /**
     * Configure a workspace by creating .vscode/settings.json with AutoGen configuration
     */
    async configureWorkspace(workspacePath: string): Promise<void> {
        try {
            const vscodeDir = path.join(workspacePath, '.vscode');
            const settingsPath = path.join(vscodeDir, 'settings.json');

            // Create .vscode directory if it doesn't exist
            try {
                await fs.access(vscodeDir);
            } catch {
                await fs.mkdir(vscodeDir, { recursive: true });
                this.outputChannel.appendLine(`Created .vscode directory at ${vscodeDir}`);
            }

            // Check if settings.json already exists and has AutoGen config
            let settings: any = {};
            try {
                const existingSettings = await fs.readFile(settingsPath, 'utf8');
                settings = JSON.parse(existingSettings);

                if (settings.autogen) {
                    this.outputChannel.appendLine(`AutoGen configuration already exists for ${workspacePath}`);
                    return;
                }
            } catch {
                // File doesn't exist or is invalid JSON, proceed with new settings
            }

            // Create AutoGen configuration
            const autoGenConfig: AutogenWorkspaceConfig = {
                autogen: {
                    serverPath: '/media/hannesn/storage/Code/autogen', // Always use the main AutoGen project
                    workingDirectory: workspacePath, // This is the workspace being configured
                    port: 9000,
                    timeout: 30000
                }
            };

            // Merge with existing settings
            const finalSettings = { ...settings, ...autoGenConfig };

            // Write settings.json
            await fs.writeFile(settingsPath, JSON.stringify(finalSettings, null, 4));

            this.outputChannel.appendLine(`Configured AutoGen workspace at ${workspacePath}`);
            this.outputChannel.appendLine(`Server path: ${autoGenConfig.autogen.serverPath}`);
            this.outputChannel.appendLine(`Working directory: ${autoGenConfig.autogen.workingDirectory}`);

        } catch (error) {
            this.outputChannel.appendLine(`Error configuring workspace ${workspacePath}: ${error}`);
        }
    }

    /**
     * Save workspace configuration with specific settings
     */
    async saveWorkspaceConfig(workspacePath: string, config: AutogenWorkspaceConfig): Promise<void> {
        try {
            const vscodeDir = path.join(workspacePath, '.vscode');
            const settingsPath = path.join(vscodeDir, 'settings.json');

            // Read existing settings
            let settings: any = {};
            try {
                const existingSettings = await fs.readFile(settingsPath, 'utf8');
                settings = JSON.parse(existingSettings);
            } catch {
                // File doesn't exist, start with empty object
            }

            // Merge configurations
            const finalSettings = { ...settings, ...config };

            // Ensure .vscode directory exists
            await fs.mkdir(vscodeDir, { recursive: true });

            // Write updated settings
            await fs.writeFile(settingsPath, JSON.stringify(finalSettings, null, 4));

            this.outputChannel.appendLine(`Saved AutoGen configuration for ${workspacePath}`);

        } catch (error) {
            this.outputChannel.appendLine(`Error saving workspace config: ${error}`);
        }
    }

    /**
     * Get workspace configuration for a given path
     */
    async getWorkspaceConfig(workspacePath: string): Promise<AutogenWorkspaceConfig | null> {
        try {
            const settingsPath = path.join(workspacePath, '.vscode', 'settings.json');
            const settingsContent = await fs.readFile(settingsPath, 'utf8');
            const settings = JSON.parse(settingsContent);

            if (settings.autogen) {
                return { autogen: settings.autogen };
            }
        } catch (error) {
            this.outputChannel.appendLine(`Error reading workspace config: ${error}`);
        }

        return null;
    }

    /**
     * Find AutoGen server in the workspace or use default path
     */
    private findAutoGenServer(workspacePath: string): string {
        // Try common AutoGen server locations
        const possiblePaths = [
            path.join(workspacePath, 'autogen', 'server.py'),
            path.join(workspacePath, 'server.py'),
            path.join(workspacePath, 'src', 'server.py'),
            path.join(workspacePath, 'autogen-server', 'server.py'),
        ];

        // Check if any of these paths exist (synchronously for now)
        for (const serverPath of possiblePaths) {
            try {
                require('fs').accessSync(serverPath);
                return serverPath;
            } catch {
                // Continue searching
            }
        }

        // Return default path if no server found
        return path.join(workspacePath, 'autogen', 'server.py');
    }

    /**
     * Check if workspace has AutoGen configuration
     */
    async hasAutoGenConfig(workspacePath: string): Promise<boolean> {
        const config = await this.getWorkspaceConfig(workspacePath);
        return config !== null;
    }
}

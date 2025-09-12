import * as assert from 'assert';
import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { WorkspaceManager, ProjectInfo } from '../services/workspaceManager';
import { FileWatcher } from '../services/fileWatcher';
import { FileOperations } from '../services/fileOperations';
import { GitIntegration } from '../services/gitIntegration';

suite('Workspace Integration Tests', () => {
    let workspaceManager: WorkspaceManager;
    let fileWatcher: FileWatcher;
    let fileOperations: FileOperations;
    let gitIntegration: GitIntegration;
    let testWorkspaceFolder: vscode.WorkspaceFolder;
    let tempDir: string;

    suiteSetup(async () => {
        // Create temporary test workspace
        tempDir = path.join(__dirname, '../../test-workspace');
        await fs.promises.mkdir(tempDir, { recursive: true });

        testWorkspaceFolder = {
            uri: vscode.Uri.file(tempDir),
            name: 'test-workspace',
            index: 0
        };

        // Initialize services
        workspaceManager = new WorkspaceManager();
        fileOperations = new FileOperations();
        gitIntegration = new GitIntegration();

        // FileWatcher requires a mock RealtimeClient
        const mockRealtimeClient = {
            broadcast: () => {},
            sendToSession: () => {},
            getActiveConnections: () => 0,
            isConnected: () => false
        } as any;

        fileWatcher = new FileWatcher(mockRealtimeClient);
    });

    suiteTeardown(async () => {
        // Clean up test workspace
        try {
            await fs.promises.rmdir(tempDir, { recursive: true });
        } catch {
            // Ignore cleanup errors
        }

        fileWatcher.dispose();
        fileOperations.dispose();
        gitIntegration.dispose();
    });

    suite('WorkspaceManager', () => {
        test('should detect Python project', async () => {
            // Create Python project files
            await fs.promises.writeFile(
                path.join(tempDir, 'pyproject.toml'),
                '[tool.poetry]\nname = "test"\n'
            );
            await fs.promises.writeFile(
                path.join(tempDir, 'requirements.txt'),
                'flask==2.0.1\n'
            );

            const projectInfo = await (workspaceManager as any).analyzeWorkspaceFolder(testWorkspaceFolder);

            assert.strictEqual(projectInfo.type, 'python');
            assert.ok(projectInfo.configFiles.includes('pyproject.toml'));
            assert.ok(projectInfo.configFiles.includes('requirements.txt'));
        });

        test('should detect TypeScript project', async () => {
            // Clean up Python files
            try {
                await fs.promises.unlink(path.join(tempDir, 'pyproject.toml'));
                await fs.promises.unlink(path.join(tempDir, 'requirements.txt'));
            } catch {
                // Files may not exist
            }

            // Create TypeScript project files
            await fs.promises.writeFile(
                path.join(tempDir, 'package.json'),
                '{"name": "test", "devDependencies": {"typescript": "^4.0.0"}}'
            );
            await fs.promises.writeFile(
                path.join(tempDir, 'tsconfig.json'),
                '{"compilerOptions": {"target": "es2020"}}'
            );

            const projectInfo = await (workspaceManager as any).analyzeWorkspaceFolder(testWorkspaceFolder);

            assert.strictEqual(projectInfo.type, 'typescript');
            assert.ok(projectInfo.configFiles.includes('package.json'));
            assert.ok(projectInfo.configFiles.includes('tsconfig.json'));
        });

        test('should initialize AutoGen configuration', async () => {
            const result = await workspaceManager.initializeAutoGen(testWorkspaceFolder);
            assert.strictEqual(result, true);

            // Check if config file was created
            const configPath = path.join(tempDir, 'autogen-mcp.json');
            const configExists = await fs.promises.access(configPath).then(() => true, () => false);
            assert.ok(configExists);

            // Verify config content
            const config = await workspaceManager.getAutoGenConfig(testWorkspaceFolder);
            assert.ok(config);
            assert.strictEqual(config.version, '1.0');
            assert.ok(config.mcp_server);
            assert.ok(config.agents);
        });
    });

    suite('FileOperations', () => {
        test('should write file with agent metadata', async () => {
            const filePath = 'test-agent-file.py';
            const content = 'print("Hello from AutoGen MCP!")';
            const agentId = 'test-agent';

            const result = await fileOperations.createAgentFile(
                testWorkspaceFolder,
                filePath,
                content,
                agentId,
                { purpose: 'test' }
            );

            assert.strictEqual(result.success, true);
            assert.strictEqual(result.filePath, filePath);

            // Check file content includes metadata
            const fullPath = path.join(tempDir, filePath);
            const fileContent = await fs.promises.readFile(fullPath, 'utf8');
            assert.ok(fileContent.includes(`Generated by AutoGen MCP Agent: ${agentId}`));
            assert.ok(fileContent.includes(content));
        });

        test('should validate file operations', async () => {
            // Test restricted path
            const result = await fileOperations.writeFile(testWorkspaceFolder, {
                filePath: 'node_modules/test.js',
                content: 'invalid'
            });

            assert.strictEqual(result.success, false);
            assert.ok(result.error?.includes('restricted'));
        });

        test('should backup existing files', async () => {
            const filePath = 'backup-test.txt';
            const originalContent = 'original content';
            const newContent = 'new content';

            // Create original file
            await fs.promises.writeFile(path.join(tempDir, filePath), originalContent);

            // Overwrite with backup enabled
            const result = await fileOperations.writeFile(testWorkspaceFolder, {
                filePath,
                content: newContent,
                backup: true
            });

            assert.strictEqual(result.success, true);
            assert.ok(result.backupPath);

            // Verify backup exists and has original content
            const backupContent = await fs.promises.readFile(result.backupPath!, 'utf8');
            assert.strictEqual(backupContent, originalContent);

            // Verify new file has new content
            const currentContent = await fs.promises.readFile(path.join(tempDir, filePath), 'utf8');
            assert.strictEqual(currentContent, newContent);
        });
    });

    suite('GitIntegration', () => {
        test('should initialize Git repository', async () => {
            const result = await gitIntegration.initializeRepository(testWorkspaceFolder);
            assert.strictEqual(result, true);

            // Check if .git directory exists
            const gitDirExists = await fs.promises.access(path.join(tempDir, '.git'))
                .then(() => true, () => false);
            assert.ok(gitDirExists);
        });

        test('should check Git repository status', async () => {
            const status = await gitIntegration.getStatus(testWorkspaceFolder);
            assert.ok(status);
            assert.strictEqual(typeof status.branch, 'string');
            assert.strictEqual(typeof status.hasChanges, 'boolean');
            assert.ok(Array.isArray(status.stagedFiles));
            assert.ok(Array.isArray(status.unstagedFiles));
            assert.ok(Array.isArray(status.untrackedFiles));
        });

        test('should create agent commit', async () => {
            // Create a test file
            const testFile = path.join(tempDir, 'agent-commit-test.txt');
            await fs.promises.writeFile(testFile, 'Test file for commit');

            const result = await gitIntegration.createAgentCommit(testWorkspaceFolder, {
                message: 'Test commit from agent',
                agentId: 'test-agent',
                files: ['agent-commit-test.txt']
            });

            assert.strictEqual(result.success, true);
            assert.ok(result.commitHash);
            assert.ok(result.message?.includes('[AutoGen MCP]'));
            assert.ok(result.message?.includes('test-agent'));
        });

        test('should create and switch to agent branch', async () => {
            const branchName = 'test-feature';
            const agentId = 'test-agent';

            const result = await gitIntegration.createAgentBranch(
                testWorkspaceFolder,
                branchName,
                agentId
            );

            assert.strictEqual(result, true);

            // Verify current branch
            const status = await gitIntegration.getStatus(testWorkspaceFolder);
            assert.ok(status?.branch.includes(branchName));
            assert.ok(status?.branch.includes(agentId));
        });

        test('should get repository statistics', async () => {
            const stats = await gitIntegration.getStats(testWorkspaceFolder);

            assert.strictEqual(stats.hasRepository, true);
            assert.ok(stats.currentBranch);
            assert.ok(typeof stats.totalCommits === 'number');
            assert.ok(typeof stats.agentCommits === 'number');
            assert.ok(stats.agentCommits! > 0); // Should have the commit we created earlier
        });
    });

    suite('FileWatcher', () => {
        test('should start and stop watching', async () => {
            fileWatcher.startWatching(testWorkspaceFolder);

            const stats = fileWatcher.getStats();
            assert.strictEqual(stats.watchedFolders, 1);
            assert.strictEqual(stats.isActive, true);

            fileWatcher.stopWatching(testWorkspaceFolder);

            const statsAfterStop = fileWatcher.getStats();
            assert.strictEqual(statsAfterStop.watchedFolders, 0);
            assert.strictEqual(statsAfterStop.isActive, false);
        });

        test('should scan workspace for existing files', async () => {
            // Create some test files
            await fs.promises.writeFile(path.join(tempDir, 'scan-test.py'), 'print("scan test")');
            await fs.promises.writeFile(path.join(tempDir, 'scan-test.md'), '# Scan Test');

            const events = await fileWatcher.scanWorkspace(testWorkspaceFolder);

            assert.ok(events.length > 0);
            assert.ok(events.some(event => event.filePath.includes('scan-test.py')));
            assert.ok(events.some(event => event.filePath.includes('scan-test.md')));

            // All events should be 'created' type from initial scan
            assert.ok(events.every(event => event.type === 'created'));
        });

        test('should ignore files based on patterns', async () => {
            // Create files that should be ignored
            const nodeModulesDir = path.join(tempDir, 'node_modules');
            await fs.promises.mkdir(nodeModulesDir, { recursive: true });
            await fs.promises.writeFile(path.join(nodeModulesDir, 'ignored.js'), 'ignored');

            const pycacheDir = path.join(tempDir, '__pycache__');
            await fs.promises.mkdir(pycacheDir, { recursive: true });
            await fs.promises.writeFile(path.join(pycacheDir, 'ignored.pyc'), 'ignored');

            const events = await fileWatcher.scanWorkspace(testWorkspaceFolder);

            // Ignored files should not appear in scan results
            assert.ok(!events.some(event => event.filePath.includes('node_modules')));
            assert.ok(!events.some(event => event.filePath.includes('__pycache__')));
        });

        test('should update configuration', () => {
            const newConfig = {
                watchedExtensions: ['.custom'],
                ignorePatterns: ['**/custom-ignore/**'],
                autoSyncToMemory: false,
                batchUpdates: false,
                batchDelay: 500
            };

            fileWatcher.updateConfig(newConfig);

            const updatedConfig = fileWatcher.getConfig();
            assert.deepStrictEqual(updatedConfig.watchedExtensions, ['.custom']);
            assert.deepStrictEqual(updatedConfig.ignorePatterns, ['**/custom-ignore/**']);
            assert.strictEqual(updatedConfig.autoSyncToMemory, false);
            assert.strictEqual(updatedConfig.batchUpdates, false);
            assert.strictEqual(updatedConfig.batchDelay, 500);
        });
    });

    suite('Integration Tests', () => {
        test('should handle complete workflow', async () => {
            // 1. Detect project type
            const projectInfo = await (workspaceManager as any).analyzeWorkspaceFolder(testWorkspaceFolder);
            assert.ok(projectInfo);

            // 2. Initialize Git if not present
            await gitIntegration.initializeRepository(testWorkspaceFolder);

            // 3. Start file watching
            fileWatcher.startWatching(testWorkspaceFolder);

            // 4. Create agent-generated file
            const result = await fileOperations.createAgentFile(
                testWorkspaceFolder,
                'integration-test.py',
                'def integration_test():\n    return "success"',
                'integration-agent'
            );
            assert.strictEqual(result.success, true);

            // 5. Commit the changes
            const commitResult = await gitIntegration.createAgentCommit(testWorkspaceFolder, {
                message: 'Add integration test file',
                agentId: 'integration-agent'
            });
            assert.strictEqual(commitResult.success, true);

            // 6. Verify file was created and committed
            const filePath = path.join(tempDir, 'integration-test.py');
            const fileExists = await fs.promises.access(filePath).then(() => true, () => false);
            assert.ok(fileExists);

            // 7. Check Git status
            const status = await gitIntegration.getStatus(testWorkspaceFolder);
            assert.ok(status);

            // 8. Clean up
            fileWatcher.stopWatching(testWorkspaceFolder);
        });

        test('should handle error conditions gracefully', async () => {
            // Test file operation with invalid path
            const invalidResult = await fileOperations.writeFile(testWorkspaceFolder, {
                filePath: '../outside-workspace.txt',
                content: 'should fail'
            });
            assert.strictEqual(invalidResult.success, false);

            // Test Git operation without staged changes
            const emptyCommitResult = await gitIntegration.createAgentCommit(testWorkspaceFolder, {
                message: 'Empty commit'
            });
            assert.strictEqual(emptyCommitResult.success, false);

            // Test workspace scanning with invalid workspace
            const invalidWorkspace: vscode.WorkspaceFolder = {
                uri: vscode.Uri.file('/nonexistent/path'),
                name: 'invalid',
                index: 0
            };

            const scanEvents = await fileWatcher.scanWorkspace(invalidWorkspace);
            assert.strictEqual(scanEvents.length, 0);
        });
    });
});

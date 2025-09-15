"""
Scrum Agents for Collaborative Project Development
=================================================

Specialized agents that work together using Scrum methodology to plan,
architect, and build projects collaboratively.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import json

from .agents import Agent


@dataclass
class UserStory:
    """Represents a user story in the project."""

    id: str
    title: str
    description: str
    acceptance_criteria: List[str]
    story_points: int
    priority: str  # "High", "Medium", "Low"
    status: str = "Backlog"  # "Backlog", "In Progress", "Done"
    assigned_to: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TechnicalDecision:
    """Represents a technical architecture decision."""

    id: str
    title: str
    context: str
    decision: str
    consequences: List[str]
    alternatives_considered: List[str]
    decided_by: str
    date: str


class ScrumMasterAgent(Agent):
    """Scrum Master agent that facilitates the scrum process."""

    def __init__(self):
        super().__init__(
            name="ScrumMaster", role="Facilitates scrum ceremonies and removes blockers"
        )
        self.user_stories: List[UserStory] = []
        self.current_sprint_stories: List[str] = []

    async def facilitate_planning_meeting(self, product_owner, tech_lead, developers):
        """Run a sprint planning meeting with all team members."""
        print("🎯 SPRINT PLANNING MEETING")
        print("=" * 50)
        print("ScrumMaster: Welcome everyone! Let's plan our Lit 3 project.")
        print()

        # Product Owner presents backlog
        backlog = await product_owner.present_backlog()

        # Tech Lead provides technical input
        technical_guidance = await tech_lead.provide_technical_guidance(backlog)

        # Developers estimate stories
        estimated_stories = []
        for dev in developers:
            estimates = await dev.estimate_stories(backlog)
            estimated_stories.extend(estimates)

        # Create sprint plan
        sprint_plan = self._create_sprint_plan(
            backlog, technical_guidance, estimated_stories
        )

        print("ScrumMaster: Sprint planning complete! Sprint backlog:")
        for story in sprint_plan:
            print(f"  📝 {story['title']} ({story['story_points']} pts)")
        print()

        return sprint_plan

    def _create_sprint_plan(self, backlog, technical_guidance, estimates):
        """Create a prioritized sprint plan."""
        # Simple sprint planning logic
        sprint_capacity = 20  # Story points
        selected_stories = []
        total_points = 0

        for story in backlog:
            if total_points + story.story_points <= sprint_capacity:
                selected_stories.append(story.to_dict())
                total_points += story.story_points

        return selected_stories

    async def run_daily_standup(self, team_members):
        """Facilitate daily standup meeting."""
        print("🌅 DAILY STANDUP")
        print("=" * 30)

        for member in team_members:
            if hasattr(member, "give_standup_update"):
                update = await member.give_standup_update()
                print(f"{member.name}: {update}")
        print()


class ProductOwnerAgent(Agent):
    """Product Owner agent that defines requirements and priorities."""

    def __init__(self):
        super().__init__(
            name="ProductOwner", role="Defines product vision and manages backlog"
        )

    async def present_backlog(self) -> List[UserStory]:
        """Present the product backlog for the Lit 3 project."""
        print("ProductOwner: Here's our Lit 3 Task Manager vision:")
        print("  🎯 Modern task management with Lit 3 web components")
        print("  🎯 Focus on reusable, accessible components")
        print("  🎯 Clean architecture with TypeScript")
        print()

        stories = [
            UserStory(
                id="US001",
                title="Task List Component",
                description="Display and manage a list of tasks",
                acceptance_criteria=[
                    "Display tasks in a clean list format",
                    "Show task status (pending/completed)",
                    "Support task filtering",
                ],
                story_points=5,
                priority="High",
            ),
            UserStory(
                id="US002",
                title="Add Task Component",
                description="Form component for adding new tasks",
                acceptance_criteria=[
                    "Input field for task title",
                    "Optional task description",
                    "Form validation",
                    "Add button functionality",
                ],
                story_points=3,
                priority="High",
            ),
            UserStory(
                id="US003",
                title="Task Item Component",
                description="Individual task component with interactions",
                acceptance_criteria=[
                    "Toggle task completion status",
                    "Edit task details inline",
                    "Delete task functionality",
                    "Visual feedback for interactions",
                ],
                story_points=4,
                priority="High",
            ),
            UserStory(
                id="US004",
                title="Navigation Component",
                description="App navigation with routing",
                acceptance_criteria=[
                    "Clean navigation bar",
                    "Active state indication",
                    "Mobile-responsive design",
                ],
                story_points=3,
                priority="Medium",
            ),
            UserStory(
                id="US005",
                title="App Shell Component",
                description="Main app layout and structure",
                acceptance_criteria=[
                    "Root application component",
                    "Layout management",
                    "Route handling integration",
                ],
                story_points=5,
                priority="High",
            ),
        ]

        print("ProductOwner: 5 user stories, 20 story points total")
        return stories


class TechLeadAgent(Agent):
    """Technical Lead agent that provides architecture guidance."""

    def __init__(self):
        super().__init__(
            name="TechLead", role="Provides technical architecture and guidance"
        )
        self.technical_decisions: List[TechnicalDecision] = []

    async def provide_technical_guidance(
        self, stories: List[UserStory]
    ) -> Dict[str, Any]:
        """Provide technical guidance for the user stories."""
        print("TechLead: Technical architecture decisions:")
        print("  🏗️  Lit 3 + TypeScript for type safety")
        print("  🏗️  Reactive properties for state management")
        print("  🏗️  Component-based architecture")
        print("  🏗️  Modern build tools: Vite + TypeScript")
        print()

        # Create technical decisions
        self.technical_decisions.append(
            TechnicalDecision(
                id="TD001",
                title="Use Lit 3 with TypeScript",
                context="Need modern web component framework with type safety",
                decision="Use Lit 3.0+ with TypeScript compilation",
                consequences=["Better DX", "Type safety", "Modern features"],
                alternatives_considered=["Pure Web Components", "Stencil"],
                decided_by=self.name,
                date=datetime.now().isoformat(),
            )
        )

        return {
            "architecture": "Component-based with Lit 3",
            "build_system": "Vite + TypeScript",
            "state_management": "Lit reactive properties",
            "testing": "Web Test Runner",
        }

    async def give_standup_update(self) -> str:
        """Provide daily standup update."""
        return "Working on component architecture design. No blockers."


class DeveloperAgent(Agent):
    """Developer agent that estimates and implements user stories."""

    def __init__(self, specialty: str = "Frontend"):
        super().__init__(
            name=f"Dev-{specialty}",
            role=f"{specialty} developer who implements features",
        )
        self.specialty = specialty

    async def estimate_stories(self, stories: List[UserStory]) -> List[Dict[str, Any]]:
        """Estimate story points for user stories."""
        estimates = []

        print(f"{self.name}: Story estimates:")
        for story in stories:
            print(f"  📊 {story.title}: {story.story_points} points")

            estimates.append(
                {
                    "story_id": story.id,
                    "estimated_by": self.name,
                    "story_points": story.story_points,
                    "confidence": "High",
                }
            )

        print()
        return estimates

    async def give_standup_update(self) -> str:
        """Provide daily standup update."""
        return f"Ready to implement {self.specialty} components. No blockers."


class ScrumTeam:
    """Orchestrates the scrum team collaboration."""

    def __init__(self):
        self.scrum_master = ScrumMasterAgent()
        self.product_owner = ProductOwnerAgent()
        self.tech_lead = TechLeadAgent()
        self.developers = [DeveloperAgent("Frontend"), DeveloperAgent("Components")]
        self.all_members = [
            self.scrum_master,
            self.product_owner,
            self.tech_lead,
        ] + self.developers

    async def run_sprint_planning(self):
        """Execute sprint planning ceremony."""
        print("🚀 SCRUM SPRINT PLANNING SESSION")
        print("=" * 60)
        print()

        sprint_plan = await self.scrum_master.facilitate_planning_meeting(
            self.product_owner, self.tech_lead, self.developers
        )

        # Daily standup
        await self.scrum_master.run_daily_standup(self.all_members)

        return sprint_plan, self.tech_lead.technical_decisions


@dataclass
class Sprint:
    """Represents a sprint in the agile process."""

    id: int
    name: str
    goal: str
    duration_weeks: int
    stories: List[UserStory]
    status: str = "Not Started"  # Not Started, In Progress, Completed
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class QATesterAgent(Agent):
    """Quality Assurance Tester agent for testing and validation."""

    def __init__(self):
        super().__init__(
            name="QATester",
            role="Quality assurance, testing, and validation specialist",
        )
        self.test_cases: List[Dict[str, Any]] = []

    async def create_test_plan(self, stories: List[UserStory]) -> List[Dict[str, Any]]:
        """Create comprehensive test plan for user stories."""
        print(f"{self.name}: Creating comprehensive test plan...")

        test_cases = []
        for story in stories:
            # Generate test cases based on acceptance criteria
            for i, criteria in enumerate(story.acceptance_criteria):
                test_case = {
                    "id": f"TC_{story.id}_{i+1}",
                    "story_id": story.id,
                    "title": f"Test: {criteria}",
                    "description": f"Verify that {criteria.lower()}",
                    "type": "Functional",
                    "priority": story.priority,
                    "status": "Not Executed",
                }
                test_cases.append(test_case)

        # Add additional test categories
        additional_tests = [
            {
                "id": "TC_PERF_001",
                "title": "Performance: File listing under 100ms",
                "description": "Verify file listing responds within 100ms",
                "type": "Performance",
                "priority": "High",
            },
            {
                "id": "TC_SEC_001",
                "title": "Security: Path traversal prevention",
                "description": "Verify system prevents ../.. path traversal",
                "type": "Security",
                "priority": "High",
            },
            {
                "id": "TC_USAB_001",
                "title": "Usability: Keyboard navigation",
                "description": "Verify all functions accessible via keyboard",
                "type": "Usability",
                "priority": "Medium",
            },
        ]
        test_cases.extend(additional_tests)

        self.test_cases = test_cases
        print(f"   ✅ Created {len(test_cases)} test cases")
        print("   📊 Coverage: Functional, Performance, Security, Usability")
        return test_cases

    async def estimate_testing_effort(self, stories: List[UserStory]) -> Dict[str, Any]:
        """Estimate testing effort for stories."""
        total_test_hours = 0
        for story in stories:
            # Estimate 2-4 hours testing per story point
            test_hours = story.story_points * 3
            total_test_hours += test_hours

        automated_tests = len(
            [tc for tc in self.test_cases if tc.get("type") != "Usability"]
        )
        manual_tests = len(
            [tc for tc in self.test_cases if tc.get("type") == "Usability"]
        )

        return {
            "total_test_hours": total_test_hours,
            "automated_tests": automated_tests,
            "manual_tests": manual_tests,
            "test_types": ["Unit", "Integration", "E2E", "Performance", "Security"],
        }

    async def give_standup_update(self) -> str:
        """Provide daily standup update."""
        return "Test planning complete. Ready for test automation setup. No blockers."


class EnhancedProductOwnerAgent(ProductOwnerAgent):
    """Enhanced Product Owner for complex projects like file systems."""

    def __init__(self, project_type: str = "file_system"):
        super().__init__()
        self.project_type = project_type

    async def present_backlog(self) -> List[UserStory]:
        """Present comprehensive product backlog based on project type."""
        if self.project_type == "file_system":
            return await self._present_file_system_backlog()
        else:
            return await super().present_backlog()

    async def _present_file_system_backlog(self) -> List[UserStory]:
        """Present comprehensive product backlog for Ranger file system."""
        print("ProductOwner: Presenting Ranger File System vision:")
        print("  🎯 Modern file manager with dual-pane interface")
        print("  🎯 Vim-like keybindings and power-user features")
        print("  🎯 Built with vanilla TypeScript for performance")
        print("  🎯 Extensible plugin architecture")
        print("  🎯 Cross-platform desktop application")
        print()

        stories = [
            # Sprint 1: Core Infrastructure
            UserStory(
                id="US001",
                title="File System Core",
                description="Core file system abstraction and operations",
                acceptance_criteria=[
                    "Read directory contents with metadata",
                    "Handle file/directory operations (copy, move, delete)",
                    "Support for different file systems (local, network)",
                    "Error handling for permission issues",
                ],
                story_points=8,
                priority="High",
            ),
            UserStory(
                id="US002",
                title="Application Shell",
                description="Main application window and layout system",
                acceptance_criteria=[
                    "Resizable dual-pane layout",
                    "Menu bar with file operations",
                    "Status bar with current path info",
                    "Responsive design for different screen sizes",
                ],
                story_points=5,
                priority="High",
            ),
            UserStory(
                id="US003",
                title="Configuration System",
                description="User settings and configuration management",
                acceptance_criteria=[
                    "JSON-based configuration file",
                    "Runtime configuration updates",
                    "Default settings with user overrides",
                    "Settings validation and error handling",
                ],
                story_points=3,
                priority="High",
            ),
            # Sprint 2: Navigation and Display
            UserStory(
                id="US004",
                title="File List Display",
                description="File listing with sorting and filtering",
                acceptance_criteria=[
                    "Display files with icons, names, sizes, dates",
                    "Sort by name, size, date, extension",
                    "Filter by file type and patterns",
                    "Virtual scrolling for large directories",
                ],
                story_points=6,
                priority="High",
            ),
            UserStory(
                id="US005",
                title="Navigation System",
                description="Directory navigation and breadcrumbs",
                acceptance_criteria=[
                    "Click navigation through directories",
                    "Breadcrumb path display and navigation",
                    "Back/forward navigation history",
                    "Bookmark favorite directories",
                ],
                story_points=4,
                priority="High",
            ),
            UserStory(
                id="US006",
                title="Dual Pane Management",
                description="Independent pane operations and synchronization",
                acceptance_criteria=[
                    "Independent navigation per pane",
                    "Active pane highlighting",
                    "Copy/move operations between panes",
                    "Pane size adjustment and layouts",
                ],
                story_points=5,
                priority="High",
            ),
            # Sprint 3: File Operations
            UserStory(
                id="US007",
                title="File Operations Core",
                description="Basic file and directory operations",
                acceptance_criteria=[
                    "Create, rename, delete files and directories",
                    "Copy and move with progress indicators",
                    "Undo/redo for reversible operations",
                    "Batch operations on multiple selections",
                ],
                story_points=7,
                priority="High",
            ),
            UserStory(
                id="US008",
                title="Selection System",
                description="File selection with keyboard and mouse",
                acceptance_criteria=[
                    "Single and multiple file selection",
                    "Keyboard selection with Shift/Ctrl",
                    "Select all/none/inverse operations",
                    "Selection persistence across operations",
                ],
                story_points=4,
                priority="High",
            ),
            # Sprint 4: Advanced Features
            UserStory(
                id="US009",
                title="Search and Find",
                description="File search with various criteria",
                acceptance_criteria=[
                    "Name-based search with wildcards",
                    "Content search in text files",
                    "Size and date range filters",
                    "Regular expression support",
                ],
                story_points=6,
                priority="Medium",
            ),
            UserStory(
                id="US010",
                title="Keyboard Shortcuts",
                description="Vim-like keyboard navigation and commands",
                acceptance_criteria=[
                    "Vim motion keys (j/k/h/l) for navigation",
                    "Command mode for advanced operations",
                    "Customizable keybinding configuration",
                    "Help system for keyboard shortcuts",
                ],
                story_points=5,
                priority="Medium",
            ),
            # Sprint 5: Polish and Extensions
            UserStory(
                id="US011",
                title="File Preview",
                description="Quick preview of file contents",
                acceptance_criteria=[
                    "Text file preview with syntax highlighting",
                    "Image preview with thumbnails",
                    "Archive content preview",
                    "Preview pane toggle and resize",
                ],
                story_points=5,
                priority="Medium",
            ),
            UserStory(
                id="US012",
                title="Plugin System",
                description="Extensible plugin architecture",
                acceptance_criteria=[
                    "Plugin loading and management system",
                    "API for file operation extensions",
                    "Theme and appearance customization",
                    "Plugin configuration interface",
                ],
                story_points=8,
                priority="Low",
            ),
        ]

        print(f"ProductOwner: Product backlog contains {len(stories)} user stories")
        total_points = sum(story.story_points for story in stories)
        print(f"ProductOwner: Total effort estimated at {total_points} story points")
        print()

        return stories


class EnhancedTechLeadAgent(TechLeadAgent):
    """Enhanced Technical Lead for file system architecture."""

    async def provide_technical_guidance(
        self, stories: List[UserStory]
    ) -> Dict[str, Any]:
        """Provide comprehensive technical architecture."""
        print("TechLead: Technical architecture for Ranger File System:")
        print("  🏗️  Vanilla TypeScript with strict typing")
        print("  🏗️  Electron for cross-platform desktop")
        print("  🏗️  Modular architecture with clean separation")
        print("  🏗️  Event-driven file system operations")
        print("  🏗️  Plugin-based extension system")
        print("  🏗️  Comprehensive testing with Jest")
        print()

        # Create technical decisions
        decisions = [
            TechnicalDecision(
                id="TD001",
                title="Vanilla TypeScript + Electron",
                context="Need cross-platform file manager with native performance",
                decision="Use Electron with vanilla TypeScript, no heavy frameworks",
                consequences=[
                    "Native performance",
                    "Full system access",
                    "Smaller bundle",
                ],
                alternatives_considered=["Tauri + Rust", "Qt + C++", "Web-based PWA"],
                decided_by=self.name,
                date=datetime.now().isoformat(),
            ),
            TechnicalDecision(
                id="TD002",
                title="Modular Architecture",
                context="Need maintainable and extensible codebase",
                decision="Domain-driven modules: FileSystem, UI, Config, Plugins",
                consequences=[
                    "Clear boundaries",
                    "Testable components",
                    "Easy extensions",
                ],
                alternatives_considered=["Monolithic structure", "MVC pattern"],
                decided_by=self.name,
                date=datetime.now().isoformat(),
            ),
            TechnicalDecision(
                id="TD003",
                title="Event-Driven Operations",
                context="Need responsive UI during file operations",
                decision="Async file operations with event emitters for UI updates",
                consequences=[
                    "Responsive UI",
                    "Cancellable operations",
                    "Progress tracking",
                ],
                alternatives_considered=["Synchronous operations", "Worker threads"],
                decided_by=self.name,
                date=datetime.now().isoformat(),
            ),
        ]

        self.technical_decisions.extend(decisions)

        return {
            "architecture": "Modular TypeScript with Electron",
            "build_system": "Vite + TypeScript + Electron Builder",
            "testing": "Jest + Playwright for E2E",
            "state_management": "Event-driven with custom state manager",
            "ui_framework": "Vanilla TypeScript with custom components",
            "decisions": [d.title for d in decisions],
        }


class EnhancedScrumTeam(ScrumTeam):
    """Enhanced scrum team for major agile projects."""

    def __init__(self, project_type: str = "file_system"):
        # Don't call super().__init__() as we need to override the team setup
        self.scrum_master = ScrumMasterAgent()
        self.product_owner = EnhancedProductOwnerAgent(project_type)
        self.tech_lead = EnhancedTechLeadAgent()
        self.qa_tester = QATesterAgent()
        self.developers = [
            DeveloperAgent("Backend"),
            DeveloperAgent("Frontend"),
            DeveloperAgent("FileSystem"),
        ]
        self.all_members = [
            self.scrum_master,
            self.product_owner,
            self.tech_lead,
            self.qa_tester,
        ] + self.developers

    async def run_major_agile_project(self, target_dir: str, project_name: str):
        """Execute a complete multi-sprint agile project."""
        from pathlib import Path
        from .agents import CoderAgent

        target_path = Path(target_dir)
        coder_agent = CoderAgent(
            name=f"{project_name}CodeGenerator",
            role=f"Generates TypeScript code for {project_name}",
        )

        print(f"🚀 {project_name.upper()} - MAJOR AGILE PROJECT")
        print("=" * 70)
        print("Multi-sprint agile development with comprehensive scrum process")
        print()

        # Phase 1: Initial Planning
        print("📋 INITIAL PROJECT PLANNING")
        print("=" * 50)

        # Get product backlog
        backlog = await self.product_owner.present_backlog()

        # Technical architecture planning
        technical_guidance = await self.tech_lead.provide_technical_guidance(backlog)

        # QA creates test plan
        test_plan = await self.qa_tester.create_test_plan(backlog)
        testing_effort = await self.qa_tester.estimate_testing_effort(backlog)

        print("QATester: Testing strategy overview:")
        print(f"  🧪 Total test cases: {len(test_plan)}")
        print(f"  ⏱️  Estimated testing: {testing_effort['total_test_hours']} hours")
        print(f"  🤖 Automated tests: {testing_effort['automated_tests']}")
        print(f"  👆 Manual tests: {testing_effort['manual_tests']}")
        print()

        # Create sprint plan
        sprints = self._create_sprint_plan(backlog)

        print("ScrumMaster: Sprint plan created!")
        for sprint in sprints:
            story_titles = [s.title for s in sprint.stories]
            print(f"  📅 {sprint.name}: {sprint.goal}")
            if story_titles:
                print(f"      Stories: {', '.join(story_titles)}")
        print()

        # Setup project structure
        await self._setup_typescript_project(target_path, technical_guidance)

        # Execute sprints
        for sprint in sprints:
            await self._run_sprint(sprint, coder_agent, target_path)

        # Project summary
        self._show_project_summary(target_path, sprints, project_name)

    def _create_sprint_plan(self, backlog: List[UserStory]) -> List[Sprint]:
        """Create comprehensive sprint plan."""
        sprints = [
            Sprint(
                id=0,
                name="Sprint 0 - Planning",
                goal="Project setup and architecture foundation",
                duration_weeks=1,
                stories=[],
            ),
            Sprint(
                id=1,
                name="Sprint 1 - Core Infrastructure",
                goal="Build file system core and application shell",
                duration_weeks=2,
                stories=[s for s in backlog if s.id in ["US001", "US002", "US003"]],
            ),
            Sprint(
                id=2,
                name="Sprint 2 - Navigation & Display",
                goal="Implement file listing and navigation system",
                duration_weeks=2,
                stories=[s for s in backlog if s.id in ["US004", "US005", "US006"]],
            ),
            Sprint(
                id=3,
                name="Sprint 3 - File Operations",
                goal="Core file operations and selection system",
                duration_weeks=2,
                stories=[s for s in backlog if s.id in ["US007", "US008"]],
            ),
            Sprint(
                id=4,
                name="Sprint 4 - Advanced Features",
                goal="Search functionality and keyboard shortcuts",
                duration_weeks=2,
                stories=[s for s in backlog if s.id in ["US009", "US010"]],
            ),
            Sprint(
                id=5,
                name="Sprint 5 - Polish & Extensions",
                goal="File preview and plugin system",
                duration_weeks=3,
                stories=[s for s in backlog if s.id in ["US011", "US012"]],
            ),
        ]
        return sprints

    async def _setup_typescript_project(self, target_path: Path, technical_guidance):
        """Create comprehensive TypeScript project structure."""
        print("🏗️  SETTING UP PROJECT STRUCTURE")
        print("-" * 50)

        # Create directory structure
        directories = [
            "src",
            "src/core",
            "src/core/filesystem",
            "src/core/config",
            "src/ui",
            "src/ui/components",
            "src/ui/views",
            "src/plugins",
            "src/types",
            "src/utils",
            "tests",
            "tests/unit",
            "tests/integration",
            "tests/e2e",
            "dist",
            "resources",
            "docs",
        ]

        for dir_name in directories:
            (target_path / dir_name).mkdir(parents=True, exist_ok=True)

        # Generate package.json
        package_json = {
            "name": "ranger-file-manager",
            "version": "1.0.0",
            "description": "Modern file manager with vim-like interface",
            "main": "dist/main.js",
            "scripts": {
                "dev": "vite --mode development",
                "build": "tsc && vite build",
                "electron": "electron dist/main.js",
                "test": "jest",
                "test:watch": "jest --watch",
                "test:e2e": "playwright test",
                "lint": "eslint src/**/*.ts",
                "package": "electron-builder",
            },
            "dependencies": {"electron": "^27.0.0", "chokidar": "^3.5.3"},
            "devDependencies": {
                "typescript": "^5.0.0",
                "vite": "^5.0.0",
                "@types/node": "^20.0.0",
                "jest": "^29.0.0",
                "@types/jest": "^29.0.0",
                "playwright": "^1.40.0",
                "eslint": "^8.0.0",
                "@typescript-eslint/eslint-plugin": "^6.0.0",
                "electron-builder": "^24.0.0",
            },
        }

        with open(target_path / "package.json", "w") as f:
            json.dump(package_json, f, indent=2)

        # Generate tsconfig.json
        tsconfig = {
            "compilerOptions": {
                "target": "ES2020",
                "module": "ESNext",
                "lib": ["ES2020", "DOM"],
                "outDir": "./dist",
                "rootDir": "./src",
                "strict": True,
                "esModuleInterop": True,
                "skipLibCheck": True,
                "forceConsistentCasingInFileNames": True,
                "moduleResolution": "node",
                "resolveJsonModule": True,
                "isolatedModules": True,
                "declaration": True,
                "declarationDir": "./dist/types",
            },
            "include": ["src/**/*"],
            "exclude": ["node_modules", "dist", "tests"],
        }

        with open(target_path / "tsconfig.json", "w") as f:
            json.dump(tsconfig, f, indent=2)

        print("✅ TypeScript project structure created")
        print(f"   📁 {target_path}")
        print("   📄 package.json, tsconfig.json")
        print("   📁 Complete modular directory structure")
        print()

    async def _run_sprint(self, sprint: Sprint, coder_agent, target_path: Path):
        """Execute a complete sprint."""
        print(f"🏃‍♂️ EXECUTING {sprint.name.upper()}")
        print("=" * 60)
        print(f"Goal: {sprint.goal}")

        if sprint.id == 0:
            print("📋 Sprint 0: Planning and setup complete!")
            return

        # Sprint planning
        print("📋 SPRINT PLANNING")
        print("-" * 30)
        print(f"ScrumMaster: Planning {sprint.name}")

        total_points = sum(s.story_points for s in sprint.stories)
        print(f"Sprint capacity: {total_points} story points")

        # Development work
        print("\n⚡ DEVELOPMENT WORK")
        print("-" * 30)

        for story in sprint.stories:
            await self._implement_story(story, coder_agent, target_path)

        print(f"\n✅ {sprint.name} completed!")
        print()

    async def _implement_story(self, story: UserStory, coder_agent, target_path: Path):
        """Implement a user story with code generation."""
        print(f"🔧 Implementing: {story.title}")

        objectives = {
            "US001": "Create TypeScript file system core class with directory reading and file operations",
            "US002": "Create TypeScript application shell class with dual-pane layout and menu system",
            "US003": "Create TypeScript configuration manager class with JSON config loading",
            "US004": "Create TypeScript file list display class with sorting and filtering",
            "US005": "Create TypeScript navigation system class with breadcrumbs and history",
            "US006": "Create TypeScript dual pane manager class for independent operations",
            "US007": "Create TypeScript file operations class with copy, move, delete operations",
            "US008": "Create TypeScript selection system class for multi-file selection",
        }

        if story.id in objectives:
            component_code = await coder_agent.generate_component(
                objective=objectives[story.id],
                component_name=story.title.replace(" ", ""),
            )

            filenames = {
                "US001": "src/core/filesystem/FileSystemCore.ts",
                "US002": "src/ui/components/ApplicationShell.ts",
                "US003": "src/core/config/ConfigurationManager.ts",
                "US004": "src/ui/components/FileListDisplay.ts",
                "US005": "src/ui/components/NavigationSystem.ts",
                "US006": "src/ui/components/DualPaneManager.ts",
                "US007": "src/core/filesystem/FileOperations.ts",
                "US008": "src/ui/components/SelectionSystem.ts",
            }

            filename = filenames.get(
                story.id, f"src/components/{story.title.replace(' ', '')}.ts"
            )
            filepath = target_path / filename

            with open(filepath, "w") as f:
                f.write(component_code)

            print(f"   ✅ Generated: {filename}")
            print(f"   📏 {len(component_code)} characters")
        else:
            print("   📋 Story planned for manual implementation")

    def _show_project_summary(
        self, target_path: Path, sprints: List[Sprint], project_name: str
    ):
        """Show project completion summary."""
        print(f"🎉 {project_name.upper()} PROJECT COMPLETE!")
        print("=" * 70)

        total_sprints = len([s for s in sprints if s.id > 0])
        total_stories = sum(len(s.stories) for s in sprints)
        total_points = sum(
            sum(story.story_points for story in s.stories) for s in sprints
        )

        print("\n📊 PROJECT METRICS:")
        print(f"   🏃‍♂️ Sprints completed: {total_sprints}")
        print(f"   📝 User stories: {total_stories}")
        print(f"   📊 Story points: {total_points}")
        print(f"   👥 Team members: {len(self.all_members)}")

        print("\n🚀 NEXT STEPS:")
        print(f"   cd {target_path}")
        print("   npm install")
        print("   npm run dev")
        print("   npm run electron")


async def create_agile_project(
    target_dir: str, project_name: str, project_type: str = "file_system"
):
    """Create and execute a comprehensive agile project.

    Args:
        target_dir: Directory where project will be created
        project_name: Name of the project (e.g., 'Ranger File System')
        project_type: Type of project ('file_system', 'web_app', etc.)
    """
    team = EnhancedScrumTeam(project_type)
    await team.run_major_agile_project(target_dir, project_name)
    return team


# Keep the old function name for backward compatibility
async def create_major_agile_project(
    target_dir: str, project_name: str, project_type: str = "file_system"
):
    """Legacy function name - use create_agile_project instead."""
    return await create_agile_project(target_dir, project_name, project_type)

#!/usr/bin/env python3
"""
Lit 3 Scrum Project Builder
==========================

Runs a scrum session with agents and builds a Lit 3 project in the Test folder.
The agents collaborate to plan, design, and generate the project code.
"""

import asyncio
import json
from pathlib import Path

from autogen_mcp.scrum_agents import ScrumTeam
from autogen_mcp.agents import CoderAgent


class Lit3ProjectOrchestrator:
    """Orchestrates scrum planning and Lit 3 project generation."""

    def __init__(self, target_dir: str):
        self.target_dir = Path(target_dir)
        self.scrum_team = ScrumTeam()
        self.coder_agent = CoderAgent(
            name="Lit3Generator",
            role="Generates Lit 3 web components from user stories",
        )

    async def run_scrum_and_build(self):
        """Execute complete scrum to code process."""
        print("🏗️  LIT 3 SCRUM PROJECT ORCHESTRATOR")
        print("=" * 60)
        print("Multi-agent scrum planning + AI code generation")
        print()

        # Phase 1: Scrum Planning Session
        sprint_plan, technical_decisions = await self.scrum_team.run_sprint_planning()

        # Phase 2: Project Structure Setup
        await self._create_project_structure()

        # Phase 3: Component Generation from User Stories
        await self._generate_components_from_stories(sprint_plan)

        # Phase 4: Project Summary
        self._show_completion_summary()

        return sprint_plan, technical_decisions

    async def _create_project_structure(self):
        """Set up the Lit 3 project structure."""
        print("📁 CREATING PROJECT STRUCTURE")
        print("-" * 40)

        # Create project directories
        dirs = ["src", "src/components", "src/styles", "public"]
        for dir_name in dirs:
            (self.target_dir / dir_name).mkdir(parents=True, exist_ok=True)

        # Generate package.json
        package_json = {
            "name": "lit3-task-manager",
            "version": "1.0.0",
            "description": "Task manager built with Lit 3 via Scrum + AI",
            "type": "module",
            "scripts": {
                "dev": "vite",
                "build": "tsc && vite build",
                "preview": "vite preview",
            },
            "dependencies": {"lit": "^3.0.0"},
            "devDependencies": {"typescript": "^5.0.0", "vite": "^5.0.0"},
        }

        with open(self.target_dir / "package.json", "w") as f:
            json.dump(package_json, f, indent=2)

        # Generate tsconfig.json
        tsconfig = {
            "compilerOptions": {
                "target": "ES2020",
                "module": "ESNext",
                "lib": ["ES2020", "DOM", "DOM.Iterable"],
                "skipLibCheck": True,
                "moduleResolution": "bundler",
                "strict": True,
                "experimentalDecorators": True,
                "useDefineForClassFields": False,
            },
            "include": ["src/**/*"],
        }

        with open(self.target_dir / "tsconfig.json", "w") as f:
            json.dump(tsconfig, f, indent=2)

        # Generate vite config
        vite_config = """import { defineConfig } from 'vite';

export default defineConfig({
  build: {
    lib: {
      entry: 'src/main.ts',
      formats: ['es']
    }
  }
});"""

        with open(self.target_dir / "vite.config.js", "w") as f:
            f.write(vite_config)

        print("✅ Project structure created")
        print(f"   📁 {self.target_dir}")
        print("   📄 package.json, tsconfig.json, vite.config.js")
        print()

    async def _generate_components_from_stories(self, sprint_plan):
        """Generate Lit 3 components from user stories."""
        print("⚡ GENERATING COMPONENTS FROM USER STORIES")
        print("-" * 50)

        # Map stories to component generation objectives
        component_specs = {
            "Task List Component": {
                "objective": "Create a Lit web component for task list display with filtering capabilities",
                "filename": "task-list.ts",
            },
            "Add Task Component": {
                "objective": "Create a Lit web component form for adding new tasks",
                "filename": "add-task.ts",
            },
            "Task Item Component": {
                "objective": "Create a Lit web component for individual task items with edit/delete actions",
                "filename": "task-item.ts",
            },
            "Navigation Component": {
                "objective": "Create a Lit web component navigation bar for app routing",
                "filename": "app-nav.ts",
            },
            "App Shell Component": {
                "objective": "Create a Lit web component app shell for main application layout",
                "filename": "app-shell.ts",
            },
        }

        for story in sprint_plan:
            story_title = story["title"]
            if story_title in component_specs:
                spec = component_specs[story_title]

                print(f"🔧 Generating: {story_title}")
                print(f"   📝 From story: {story['description'][:50]}...")

                # Generate component using CoderAgent
                component_code = await self.coder_agent.generate_component(
                    objective=spec["objective"],
                    component_name=story_title.replace(" ", ""),
                )

                # Save to file
                comp_path = self.target_dir / "src" / "components" / spec["filename"]
                with open(comp_path, "w") as f:
                    f.write(component_code)

                print(f"   ✅ Generated: src/components/{spec['filename']}")
                print(f"   📏 {len(component_code)} characters")
                print()

        # Generate main entry point
        await self._generate_main_app()

    async def _generate_main_app(self):
        """Generate the main application entry point."""
        main_ts = """import { html, css, LitElement } from 'lit';
import { customElement } from 'lit/decorators.js';

// Import components
import './components/app-shell';
import './components/app-nav';
import './components/task-list';
import './components/add-task';
import './components/task-item';

@customElement('task-manager-app')
export class TaskManagerApp extends LitElement {
  static styles = css`
    :host {
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      font-family: system-ui, sans-serif;
    }
  `;

  render() {
    return html`
      <app-shell>
        <app-nav slot="nav"></app-nav>
        <main slot="content">
          <add-task></add-task>
          <task-list></task-list>
        </main>
      </app-shell>
    `;
  }
}"""

        with open(self.target_dir / "src" / "main.ts", "w") as f:
            f.write(main_ts)

        # Generate index.html
        index_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lit 3 Task Manager (Scrum Generated)</title>
</head>
<body>
    <task-manager-app></task-manager-app>
    <script type="module" src="/src/main.ts"></script>
</body>
</html>"""

        with open(self.target_dir / "index.html", "w") as f:
            f.write(index_html)

        print("🎯 Generated application files:")
        print("   📄 src/main.ts")
        print("   📄 index.html")
        print()

    def _show_completion_summary(self):
        """Show project completion summary."""
        print("🎉 SCRUM + LIT 3 PROJECT COMPLETE!")
        print("=" * 50)
        print()
        print("📊 PROJECT SUMMARY:")
        print(f"   📁 Location: {self.target_dir}")
        print("   🏗️  Architecture: Lit 3 + TypeScript + Vite")
        print("   👥 Planned by: 4 Scrum agents")
        print("   📦 Components: 5 generated")
        print("   🎯 Stories: 5 implemented")
        print()
        print("🚀 NEXT STEPS:")
        print(f"   cd {self.target_dir}")
        print("   npm install")
        print("   npm run dev")
        print()


async def main():
    """Main entry point."""
    target_dir = "/media/hannesn/storage/Code/Test/lit3-task-manager"

    orchestrator = Lit3ProjectOrchestrator(target_dir)
    await orchestrator.run_scrum_and_build()

    print("🎯 SCRUM-DRIVEN LIT 3 PROJECT GENERATION COMPLETE!")


if __name__ == "__main__":
    asyncio.run(main())

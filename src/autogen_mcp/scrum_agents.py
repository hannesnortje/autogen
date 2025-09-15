"""
Scrum Agents for Collaborative Project Development
=================================================

Specialized agents that work together using Scrum methodology to plan,
architect, and build projects collaboratively.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

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

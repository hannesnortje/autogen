"""
Agent scaffolding for AutoGen MCP integration.
Defines agent roles, base class, and registration logic.
"""

from typing import Any, Dict, List, Optional


class Agent:
    def __init__(self, name: str, role: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.role = role
        self.config = config or {}
        self.state: Dict[str, Any] = {}

    def act(self, observation: Any) -> Any:
        """
        Override in subclasses: perform agent action given an observation.
        """
        raise NotImplementedError

    def observe(self, event: Any):
        """
        Override in subclasses: update agent state with new event.
        """
        pass


# Registry for agent types
def register_agent(role: str):
    def decorator(cls):
        AGENT_REGISTRY[role] = cls
        return cls

    return decorator


AGENT_REGISTRY: Dict[str, type] = {}


@register_agent("Agile")
class AgileAgent(Agent):
    def act(self, observation: Any) -> Any:
        # TODO: Implement Agile agent logic
        return f"[Agile] Observed: {observation}"


@register_agent("Planner")
class PlannerAgent(Agent):
    def act(self, observation: Any) -> Any:
        # TODO: Implement Planner agent logic
        return f"[Planner] Observed: {observation}"


@register_agent("Architect")
class ArchitectAgent(Agent):
    def act(self, observation: Any) -> Any:
        # TODO: Implement Architect agent logic
        return f"[Architect] Observed: {observation}"


@register_agent("Coder")
class CoderAgent(Agent):
    def act(self, observation: Any) -> Any:
        # TODO: Implement Coder agent logic
        return f"[Coder] Observed: {observation}"


@register_agent("Reviewer")
class ReviewerAgent(Agent):
    def act(self, observation: Any) -> Any:
        # TODO: Implement Reviewer agent logic
        return f"[Reviewer] Observed: {observation}"


@register_agent("Tester")
class TesterAgent(Agent):
    def act(self, observation: Any) -> Any:
        # TODO: Implement Tester agent logic
        return f"[Tester] Observed: {observation}"


@register_agent("DevOps")
class DevOpsAgent(Agent):
    def act(self, observation: Any) -> Any:
        # TODO: Implement DevOps agent logic
        return f"[DevOps] Observed: {observation}"


@register_agent("Doc")
class DocAgent(Agent):
    def act(self, observation: Any) -> Any:
        # TODO: Implement Doc agent logic
        return f"[Doc] Observed: {observation}"


def create_agent(
    role: str, name: str, config: Optional[Dict[str, Any]] = None
) -> Agent:
    cls = AGENT_REGISTRY.get(role)
    if not cls:
        raise ValueError(f"Unknown agent role: {role}")
    return cls(name=name, role=role, config=config)


# Utility: list all available agent roles
def list_agent_roles() -> List[str]:
    return list(AGENT_REGISTRY.keys())

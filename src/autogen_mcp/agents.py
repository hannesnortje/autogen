"""
Agent scaffolding for AutoGen MCP integration.
Defines agent roles, base class, and registration logic.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from autogen_mcp.simple_agent_memory import (
    AgentMemoryService,
    AgentContext,
    ConversationTurn,
)


class Agent:
    def __init__(
        self,
        name: str,
        role: str,
        config: Optional[Dict[str, Any]] = None,
        memory_service: Optional[AgentMemoryService] = None,
    ):
        self.name = name
        self.role = role
        self.config = config or {}
        self.state: Dict[str, Any] = {}
        self.memory_service = memory_service
        self.agent_id = str(uuid.uuid4())
        self.current_conversation_id: Optional[str] = None
        self.turn_counter = 0

    def start_conversation(
        self, session_id: str, initial_objective: Optional[str] = None
    ) -> str:
        """
        Start a new conversation session with memory tracking.
        Returns conversation_id for tracking this conversation thread.
        """
        if self.memory_service:
            self.current_conversation_id = self.memory_service.start_agent_conversation(
                agent_id=self.agent_id,
                agent_name=self.name,
                agent_role=self.role,
                session_id=session_id,
                initial_objective=initial_objective,
            )
            self.turn_counter = 0
        else:
            self.current_conversation_id = str(uuid.uuid4())

        return self.current_conversation_id

    def act_with_memory(
        self,
        observation: Any,
        session_id: str,
        reasoning: Optional[str] = None,
        decisions_made: Optional[List[str]] = None,
        resources_used: Optional[List[str]] = None,
    ) -> Any:
        """
        Perform agent action with automatic memory recording.
        This wraps the core act() method with memory integration.
        """
        # Ensure we have a conversation started
        if not self.current_conversation_id:
            self.start_conversation(session_id)

        self.turn_counter += 1

        # Get context from memory if available
        context_from_memory = []
        if self.memory_service:
            context_from_memory = self.memory_service.get_agent_context(
                agent_role=self.role,
                conversation_id=self.current_conversation_id,
                query=str(observation) if observation else None,
                max_results=5,
            )

        # Perform the agent's core action
        response = self.act(observation, context_from_memory)

        # Record this turn in memory
        if self.memory_service and self.current_conversation_id:
            context = AgentContext(
                agent_id=self.agent_id,
                agent_name=self.name,
                agent_role=self.role,
                session_id=session_id,
                conversation_id=self.current_conversation_id,
                turn_number=self.turn_counter,
                timestamp=datetime.now(timezone.utc),
            )

            turn = ConversationTurn(
                context=context,
                input_message=str(observation),
                output_message=str(response),
                reasoning=reasoning,
                decisions_made=decisions_made or [],
                resources_used=resources_used or [],
            )

            self.memory_service.record_agent_turn(turn)

        return response

    def act(
        self, observation: Any, context: Optional[List[Dict[str, Any]]] = None
    ) -> Any:
        """
        Override in subclasses: perform agent action given an observation.
        Context parameter now provides memory-retrieved context.
        """
        raise NotImplementedError

    def observe(self, event: Any):
        """
        Override in subclasses: update agent state with new event.
        """
        pass

    def make_decision(self, decision: str, reasoning: str, context: str) -> str:
        """
        Record a significant decision made by the agent.
        """
        if self.memory_service:
            return self.memory_service.record_agent_decision(
                agent_id=self.agent_id,
                agent_name=self.name,
                agent_role=self.role,
                decision=decision,
                reasoning=reasoning,
                context=context,
                conversation_id=self.current_conversation_id,
            )
        return ""

    def end_conversation(self, summary: Optional[str] = None) -> Optional[str]:
        """
        End the current conversation and record summary.
        """
        if self.memory_service and self.current_conversation_id:
            event_id = self.memory_service.end_agent_conversation(
                self.current_conversation_id, summary
            )
            self.current_conversation_id = None
            self.turn_counter = 0
            return event_id
        return None

    def get_performance_insights(self) -> Dict[str, Any]:
        """
        Get performance insights for this agent from memory.
        """
        if self.memory_service:
            return self.memory_service.get_agent_performance_insights(self.role)
        return {"error": "No memory service available"}


# Registry for agent types
def register_agent(role: str):
    def decorator(cls):
        AGENT_REGISTRY[role] = cls
        return cls

    return decorator


AGENT_REGISTRY: Dict[str, type] = {}


@register_agent("Agile")
class AgileAgent(Agent):
    def act(
        self, observation: Any, context: Optional[List[Dict[str, Any]]] = None
    ) -> Any:
        # Use context from memory to inform decision making
        context_info = ""
        if context:
            recent_decisions = [
                c.get("content", "")
                for c in context
                if "decision" in c.get("content", "").lower()
            ]
            if recent_decisions:
                context_info = (
                    f" (Previous decisions: {len(recent_decisions)} recorded)"
                )

        response = f"[Agile] Orchestrating: {observation}{context_info}"

        # Record this as a decision if it's substantive
        if self.memory_service and len(str(observation)) > 20:
            self.make_decision(
                decision=f"Orchestrate response to: {observation}",
                reasoning="As Agile agent, coordinating team response",
                context=f"Observation: {observation}, Available context: {len(context or [])}",
            )

        return response


@register_agent("Planner")
class PlannerAgent(Agent):
    def act(
        self, observation: Any, context: Optional[List[Dict[str, Any]]] = None
    ) -> Any:
        # Look for previous planning patterns
        planning_context = ""
        if context:
            plans = [
                c.get("content", "")
                for c in context
                if "plan" in c.get("content", "").lower()
            ]
            if plans:
                planning_context = f" (Building on {len(plans)} previous plans)"

        response = f"[Planner] Breaking down: {observation}{planning_context}"

        # Record planning decisions
        if self.memory_service:
            self.make_decision(
                decision=f"Create plan breakdown for: {observation}",
                reasoning="Systematic decomposition of complex requirements",
                context=f"Input: {observation}, Planning history: {len(context or [])}",
            )

        return response


@register_agent("Architect")
class ArchitectAgent(Agent):
    def act(
        self, observation: Any, context: Optional[List[Dict[str, Any]]] = None
    ) -> Any:
        # Look for architectural patterns and decisions
        arch_context = ""
        if context:
            arch_items = [
                c.get("content", "")
                for c in context
                if any(
                    term in c.get("content", "").lower()
                    for term in ["architecture", "design", "structure", "pattern"]
                )
            ]
            if arch_items:
                arch_context = (
                    f" (Referencing {len(arch_items)} architectural patterns)"
                )

        response = f"[Architect] Designing: {observation}{arch_context}"

        if self.memory_service:
            self.make_decision(
                decision=f"Architectural approach for: {observation}",
                reasoning="System design considerations and pattern application",
                context=f"Requirements: {observation}, Architectural context: {len(context or [])}",
            )

        return response


@register_agent("Coder")
class CoderAgent(Agent):
    def act(
        self, observation: Any, context: Optional[List[Dict[str, Any]]] = None
    ) -> Any:
        # Look for code patterns and implementation approaches
        code_context = ""
        if context:
            code_items = [
                c.get("content", "")
                for c in context
                if any(
                    term in c.get("content", "").lower()
                    for term in ["code", "implementation", "function", "class"]
                )
            ]
            if code_items:
                code_context = f" (Using {len(code_items)} code patterns)"

        response = f"[Coder] Implementing: {observation}{code_context}"

        if self.memory_service:
            self.make_decision(
                decision=f"Implementation strategy for: {observation}",
                reasoning="Code structure and implementation methodology",
                context=f"Specification: {observation}, Code context: {len(context or [])}",
            )

        return response


@register_agent("Reviewer")
class ReviewerAgent(Agent):
    def act(
        self, observation: Any, context: Optional[List[Dict[str, Any]]] = None
    ) -> Any:
        # Look for review patterns and quality standards
        review_context = ""
        if context:
            reviews = [
                c.get("content", "")
                for c in context
                if any(
                    term in c.get("content", "").lower()
                    for term in ["review", "quality", "standard", "issue"]
                )
            ]
            if reviews:
                review_context = f" (Applying {len(reviews)} quality patterns)"

        response = f"[Reviewer] Reviewing: {observation}{review_context}"

        if self.memory_service:
            self.make_decision(
                decision=f"Quality assessment for: {observation}",
                reasoning="Code quality and standards compliance evaluation",
                context=f"Review target: {observation}, Quality context: {len(context or [])}",
            )

        return response


@register_agent("Tester")
class TesterAgent(Agent):
    def act(
        self, observation: Any, context: Optional[List[Dict[str, Any]]] = None
    ) -> Any:
        # Look for testing strategies and patterns
        test_context = ""
        if context:
            tests = [
                c.get("content", "")
                for c in context
                if any(
                    term in c.get("content", "").lower()
                    for term in ["test", "validation", "scenario", "case"]
                )
            ]
            if tests:
                test_context = f" (Leveraging {len(tests)} test patterns)"

        response = f"[Tester] Testing: {observation}{test_context}"

        if self.memory_service:
            self.make_decision(
                decision=f"Test strategy for: {observation}",
                reasoning="Comprehensive testing approach and validation methodology",
                context=f"Test target: {observation}, Testing context: {len(context or [])}",
            )

        return response


@register_agent("DevOps")
class DevOpsAgent(Agent):
    def act(
        self, observation: Any, context: Optional[List[Dict[str, Any]]] = None
    ) -> Any:
        # Look for deployment and infrastructure patterns
        devops_context = ""
        if context:
            devops_items = [
                c.get("content", "")
                for c in context
                if any(
                    term in c.get("content", "").lower()
                    for term in ["deploy", "infrastructure", "pipeline", "build"]
                )
            ]
            if devops_items:
                devops_context = f" (Using {len(devops_items)} DevOps patterns)"

        response = f"[DevOps] Deploying: {observation}{devops_context}"

        if self.memory_service:
            self.make_decision(
                decision=f"Infrastructure approach for: {observation}",
                reasoning="Deployment strategy and infrastructure considerations",
                context=f"Requirements: {observation}, DevOps context: {len(context or [])}",
            )

        return response


@register_agent("Doc")
class DocAgent(Agent):
    def act(
        self, observation: Any, context: Optional[List[Dict[str, Any]]] = None
    ) -> Any:
        # Look for documentation patterns and standards
        doc_context = ""
        if context:
            docs = [
                c.get("content", "")
                for c in context
                if any(
                    term in c.get("content", "").lower()
                    for term in ["documentation", "readme", "guide", "api"]
                )
            ]
            if docs:
                doc_context = f" (Following {len(docs)} doc patterns)"

        response = f"[Doc] Documenting: {observation}{doc_context}"

        if self.memory_service:
            self.make_decision(
                decision=f"Documentation approach for: {observation}",
                reasoning="Documentation strategy and information architecture",
                context=f"Subject: {observation}, Documentation context: {len(context or [])}",
            )

        return response


def create_agent(
    role: str,
    name: str,
    config: Optional[Dict[str, Any]] = None,
    memory_service: Optional[AgentMemoryService] = None,
) -> Agent:
    cls = AGENT_REGISTRY.get(role)
    if not cls:
        raise ValueError(f"Unknown agent role: {role}")
    return cls(name=name, role=role, config=config, memory_service=memory_service)


# Utility: list all available agent roles
def list_agent_roles() -> List[str]:
    return list(AGENT_REGISTRY.keys())

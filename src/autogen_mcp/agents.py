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
        # Check if this is an agile project request
        observation_str = str(observation).lower()
        if any(
            term in observation_str
            for term in [
                "agile project",
                "ranger file system",
                "multi-sprint",
                "scrum project",
                "file manager project",
                "comprehensive project",
            ]
        ):
            # This is an agile project request - delegate to CoderAgent
            return {
                "agent": "Agile",
                "action": "agile_project_request",
                "observation": observation,
                "message": f"[Agile] Detected agile project request. Coordinating development for: {observation}",
                "delegate_to": "coder_agile_project",
                "project_type": (
                    "file_system" if "file" in observation_str else "web_app"
                ),
            }  # Use context from memory to inform decision making
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
    async def generate_component(self, objective: str, component_name: str) -> str:
        """Public method to generate components across multiple frameworks."""
        # Detect framework and route to appropriate generator
        framework = self._detect_framework(objective)

        if framework == "react":
            # Extract tags for React component generation
            tags = self._extract_tags_from_objective(objective)
            return self._generate_react_component(tags, component_name, objective)
        elif framework == "lit":
            # Extract tags for Lit component generation
            tags = self._extract_tags_from_objective(objective)
            return self._generate_lit_component(tags, component_name, objective)
        elif framework == "cpp":
            # Extract tags for C++ class generation
            tags = self._extract_tags_from_objective(objective)
            return self._generate_cpp_class(tags, component_name, objective)
        else:
            # Default to Vue component
            return self._generate_vue_component(objective, component_name)

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

        # Generate actual Vue 3 component based on the objective
        objective_str = str(observation)

        # Extract component name from objective (fallback to generic name)
        import re

        component_match = re.search(r"(\w+)\s*component", objective_str.lower())
        component_name = (
            component_match.group(1).title() if component_match else "MyComponent"
        )

        # Generate specific Vue 3 component based on objective content
        vue_content = self._generate_vue_component(objective_str, component_name)

        # Return structured response with file content
        response = {
            "agent": "Coder",
            "action": "file_creation",
            "files": [
                {
                    "filename": f"{component_name}.vue",
                    "content": vue_content,
                    "type": "vue_component",
                }
            ],
            "message": (
                f"[Coder] Created Vue 3 component: {component_name}.vue "
                f"for {objective_str}{code_context}"
            ),
        }

        if self.memory_service:
            self.make_decision(
                decision=f"Implementation strategy for: {observation}",
                reasoning=(
                    "Generated Vue 3 component with template, script setup, "
                    "and scoped styles"
                ),
                context=(
                    f"Specification: {observation}, "
                    f"Generated: {component_name}.vue, "
                    f"Code context: {len(context or [])}"
                ),
            )

        return response

    def _generate_vue_component(self, objective: str, component_name: str) -> str:
        """Generate Vue 3 component based on objective using dynamic pattern retrieval."""
        try:
            # Search for relevant component patterns in Qdrant
            pattern = self._find_component_pattern(objective, component_name)
            if pattern:
                return self._generate_from_pattern(pattern, objective, component_name)

            # Fallback for legacy patterns if no pattern found
            return self._generate_legacy_component(objective, component_name)

        except Exception:
            # Ultimate fallback
            return self._generate_generic_component(component_name)

    def _find_component_pattern(
        self, objective: str, component_name: str
    ) -> Optional[Dict[str, Any]]:
        """Search Qdrant for matching component patterns across multiple frameworks."""
        try:
            from autogen_mcp.embeddings import EmbeddingService
            from autogen_mcp.memory_collections import MemoryScope

            # Detect framework/language from objective
            framework = self._detect_framework(objective)

            # Create search query combining objective and component name
            search_query = f"{framework} component pattern {objective} {component_name}"

            # Get embedding service and collection manager from memory if available
            if hasattr(self, "memory") and self.memory:
                embedding_service = EmbeddingService()
                vector = embedding_service.encode_one(search_query)

                # Search in global knowledge collection for component patterns
                collection_name = self.memory.collection_manager.get_collection_name(
                    MemoryScope.GLOBAL
                )

                # First try framework-specific patterns
                results = self.memory.collection_manager.qdrant.search(
                    collection=collection_name,
                    vector=vector,
                    limit=5,
                    score_threshold=0.6,
                    filter={
                        "must": [
                            {
                                "key": "category",
                                "match": {"value": f"{framework}-component-pattern"},
                            },
                            {"key": "language", "match": {"value": framework}},
                        ]
                    },
                )

                # If no framework-specific results, try broader search
                if not results or len(results) == 0:
                    results = self.memory.collection_manager.qdrant.search(
                        collection=collection_name,
                        vector=vector,
                        limit=5,
                        score_threshold=0.5,
                        filter={
                            "should": [
                                {
                                    "key": "category",
                                    "match": {"value": "vue-component-pattern"},
                                },
                                {
                                    "key": "category",
                                    "match": {"value": "react-component-pattern"},
                                },
                                {
                                    "key": "category",
                                    "match": {"value": "lit-component-pattern"},
                                },
                                {
                                    "key": "category",
                                    "match": {"value": "cpp-class-pattern"},
                                },
                            ]
                        },
                    )

                # Return the best matching pattern with framework info
                if results and len(results) > 0:
                    best_result = results[0]
                    return {
                        "content": best_result.payload.get("content", ""),
                        "tags": best_result.payload.get("tags", []),
                        "language": best_result.payload.get("language", framework),
                        "category": best_result.payload.get("category", ""),
                        "score": best_result.score,
                    }

        except Exception:
            # If pattern search fails, continue to legacy patterns
            pass

        return None

    def _detect_framework(self, objective: str) -> str:
        """Detect the target framework/language from the objective."""
        objective_lower = objective.lower()

        # Check for explicit framework mentions
        if any(
            term in objective_lower for term in ["react", "jsx", "hooks", "next.js"]
        ):
            return "react"
        elif any(
            term in objective_lower for term in ["lit", "web component", "lit-element"]
        ):
            return "lit"
        elif any(
            term in objective_lower
            for term in ["c++", "cpp", "class", "header", "template"]
        ):
            return "cpp"
        elif any(
            term in objective_lower
            for term in ["vue", "composition api", "script setup"]
        ):
            return "vue"
        else:
            # Default fallback - could be made smarter with more context
            return "vue"

    def _extract_tags_from_objective(self, objective: str) -> List[str]:
        """Extract component type tags from the objective."""
        tags = []
        objective_lower = objective.lower()

        if "hero" in objective_lower:
            tags.append("hero")
        if "header" in objective_lower or "nav" in objective_lower:
            tags.append("header")
        if "card" in objective_lower:
            tags.append("card")
        if "form" in objective_lower:
            tags.append("form")
        if "about" in objective_lower:
            tags.append("about")
        if "raii" in objective_lower:
            tags.append("raii")
        if "observer" in objective_lower:
            tags.append("observer")
        if "template" in objective_lower:
            tags.append("template")
        if "singleton" in objective_lower:
            tags.append("singleton")

        return tags if tags else ["generic"]

    def _generate_from_pattern(
        self, pattern: Dict[str, Any], objective: str, component_name: str
    ) -> str:
        """Generate component using retrieved pattern from Qdrant for any framework."""
        pattern.get("content", "")
        tags = pattern.get("tags", [])
        language = pattern.get("language", "vue")
        pattern.get("category", "")

        # Route to appropriate generator based on language
        if language == "react":
            return self._generate_react_component(tags, component_name, objective)
        elif language == "lit":
            return self._generate_lit_component(tags, component_name, objective)
        elif language == "cpp":
            return self._generate_cpp_class(tags, component_name, objective)
        elif language == "vue":
            return self._generate_vue_from_tags(tags, component_name)
        else:
            return self._generate_generic_component(component_name)

    def _generate_react_component(
        self, tags: List[str], component_name: str, objective: str
    ) -> str:
        """Generate React component based on pattern tags."""
        if "hero" in tags:
            return self._generate_react_hero(component_name)
        elif "about" in tags:
            return self._generate_react_about(component_name)
        elif "header" in tags or "navigation" in tags:
            return self._generate_react_header(component_name)
        elif "form" in tags:
            return self._generate_react_form(component_name)
        else:
            return self._generate_react_generic(component_name, objective)

    def _generate_lit_component(
        self, tags: List[str], component_name: str, objective: str
    ) -> str:
        """Generate Lit 3 web component based on pattern tags."""
        if "hero" in tags:
            return self._generate_lit_hero(component_name)
        elif "card" in tags:
            return self._generate_lit_card(component_name)
        elif "form" in tags:
            return self._generate_lit_form(component_name)
        else:
            return self._generate_lit_generic(component_name, objective)

    def _generate_cpp_class(
        self, tags: List[str], component_name: str, objective: str
    ) -> str:
        """Generate C++ class based on pattern tags."""
        if "raii" in tags:
            return self._generate_cpp_raii(component_name)
        elif "observer" in tags:
            return self._generate_cpp_observer(component_name)
        elif "template" in tags:
            return self._generate_cpp_template(component_name)
        elif "singleton" in tags:
            return self._generate_cpp_singleton(component_name)
        else:
            return self._generate_cpp_generic(component_name, objective)

    def _generate_vue_from_tags(self, tags: List[str], component_name: str) -> str:
        """Generate Vue component based on pattern tags (existing logic)."""
        if "hero" in tags:
            return self._generate_hero_component(component_name)
        elif "about" in tags:
            return self._generate_about_component(component_name)
        elif "footer" in tags:
            return self._generate_footer_component(component_name)
        elif "app" in tags or "layout" in tags:
            return self._generate_app_component(component_name)
        elif "header" in tags or "navigation" in tags:
            return self._generate_header_component(component_name)
        elif "todo" in tags:
            return self._generate_todo_component_from_pattern(component_name, "todo")
        else:
            return self._generate_generic_component(component_name)

    # React Component Generators
    def _generate_react_hero(self, component_name: str) -> str:
        """Generate React Hero component."""
        return f"""import React from 'react';
import './Hero.css';

const {component_name} = ({{ title = "Welcome to Our Platform", subtitle = "Build amazing things together" }}) => {{
  return (
    <section className="hero">
      <div className="hero-background"></div>
      <div className="container">
        <div className="hero-content">
          <h1 className="hero-title">{{title}}</h1>
          <p className="hero-subtitle">{{subtitle}}</p>
          <div className="hero-buttons">
            <button className="btn btn-primary">Get Started</button>
            <button className="btn btn-secondary">Learn More</button>
          </div>
        </div>
      </div>
    </section>
  );
}};

export default {component_name};"""

    def _generate_react_header(self, component_name: str) -> str:
        """Generate React Header/Navigation component."""
        return f"""import React, {{ useState, useEffect }} from 'react';
import './Header.css';

const {component_name} = () => {{
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {{
    const handleScroll = () => {{
      setIsScrolled(window.scrollY > 100);
    }};

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }}, []);

  return (
    <header className={{`header ${{isScrolled ? 'scrolled' : ''}}`}}>
      <nav className="navbar">
        <div className="container">
          <div className="nav-brand">
            <h1>Brand</h1>
          </div>

          <ul className={{`nav-menu ${{isMenuOpen ? 'active' : ''}}`}}>
            <li><a href="#home">Home</a></li>
            <li><a href="#about">About</a></li>
            <li><a href="#services">Services</a></li>
            <li><a href="#contact">Contact</a></li>
          </ul>

          <button
            className="mobile-toggle"
            onClick={{() => setIsMenuOpen(!isMenuOpen)}}
          >
            ☰
          </button>
        </div>
      </nav>
    </header>
  );
}};

export default {component_name};"""

    def _generate_react_generic(self, component_name: str, objective: str) -> str:
        """Generate generic React component."""
        return f"""import React, {{ useState }} from 'react';

const {component_name} = () => {{
  const [count, setCount] = useState(0);

  return (
    <div className="{component_name.lower()}-container">
      <h2>{component_name}</h2>
      <p>React component for: {objective}</p>
      <button onClick={{() => setCount(count + 1)}}>
        Clicked {{count}} times
      </button>
    </div>
  );
}};

export default {component_name};"""

    # Lit 3 Component Generators
    def _generate_lit_hero(self, component_name: str) -> str:
        """Generate Lit 3 Hero web component."""
        component_tag = (
            component_name.lower().replace("component", "").replace("_", "-")
        )
        return f"""import {{ LitElement, html, css }} from 'lit';
import {{ property }} from 'lit/decorators.js';

export class {component_name} extends LitElement {{
  @property() title = 'Welcome to Our Platform';
  @property() subtitle = 'Build amazing things together';
  @property() backgroundImage = '';

  static styles = css`
    :host {{
      display: block;
      min-height: 100vh;
      position: relative;
      overflow: hidden;
    }}

    .hero {{
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      text-align: center;
      padding: 2rem;
    }}

    .hero-title {{
      font-size: 3rem;
      font-weight: bold;
      margin-bottom: 1rem;
    }}

    .hero-subtitle {{
      font-size: 1.2rem;
      margin-bottom: 2rem;
      opacity: 0.9;
    }}

    .btn {{
      padding: 12px 24px;
      margin: 0 0.5rem;
      border: none;
      border-radius: 25px;
      cursor: pointer;
      font-weight: 600;
      transition: transform 0.3s ease;
    }}

    .btn:hover {{
      transform: translateY(-2px);
    }}

    .btn-primary {{
      background: white;
      color: #667eea;
    }}

    .btn-secondary {{
      background: transparent;
      color: white;
      border: 2px solid white;
    }}
  `;

  render() {{
    return html`
      <section class="hero">
        <div class="hero-content">
          <h1 class="hero-title">${{this.title}}</h1>
          <p class="hero-subtitle">${{this.subtitle}}</p>
          <div class="hero-buttons">
            <button class="btn btn-primary" @click="${{this._handlePrimaryClick}}">
              Get Started
            </button>
            <button class="btn btn-secondary" @click="${{this._handleSecondaryClick}}">
              Learn More
            </button>
          </div>
        </div>
      </section>
    `;
  }}

  _handlePrimaryClick() {{
    this.dispatchEvent(new CustomEvent('primary-action', {{ bubbles: true }}));
  }}

  _handleSecondaryClick() {{
    this.dispatchEvent(new CustomEvent('secondary-action', {{ bubbles: true }}));
  }}
}}

customElements.define('{component_tag}-hero', {component_name});"""

    def _generate_lit_generic(self, component_name: str, objective: str) -> str:
        """Generate generic Lit 3 web component."""
        component_tag = (
            component_name.lower().replace("component", "").replace("_", "-")
        )
        return f"""import {{ LitElement, html, css }} from 'lit';
import {{ property }} from 'lit/decorators.js';

export class {component_name} extends LitElement {{
  @property() title = '{component_name}';

  static styles = css`
    :host {{
      display: block;
      padding: 2rem;
      border: 1px solid #ddd;
      border-radius: 8px;
    }}

    .container {{
      text-align: center;
    }}

    button {{
      padding: 0.5rem 1rem;
      background: #667eea;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
    }}
  `;

  render() {{
    return html`
      <div class="container">
        <h2>${{this.title}}</h2>
        <p>Web component for: {objective}</p>
        <button @click="${{this._handleClick}}">Click me</button>
      </div>
    `;
  }}

  _handleClick() {{
    this.dispatchEvent(new CustomEvent('component-clicked', {{ bubbles: true }}));
  }}
}}

customElements.define('{component_tag}', {component_name});"""

    # C++ Class Generators
    def _generate_cpp_raii(self, component_name: str) -> str:
        """Generate C++ RAII class."""
        return f"""#pragma once
#include <memory>
#include <stdexcept>

class {component_name} {{
private:
    std::unique_ptr<ResourceType> resource_;

public:
    // Constructor - acquire resource
    explicit {component_name}(const std::string& resource_name) {{
        resource_ = std::make_unique<ResourceType>(resource_name);
        if (!resource_) {{
            throw std::runtime_error("Failed to acquire resource");
        }}
    }}

    // Destructor - automatically release resource
    ~{component_name}() = default;

    // Disable copy (use move semantics instead)
    {component_name}(const {component_name}&) = delete;
    {component_name}& operator=(const {component_name}&) = delete;

    // Enable move semantics
    {component_name}({component_name}&&) noexcept = default;
    {component_name}& operator=({component_name}&&) noexcept = default;

    // Access the resource
    ResourceType* get() const noexcept {{
        return resource_.get();
    }}

    // Check if resource is valid
    bool is_valid() const noexcept {{
        return resource_ != nullptr;
    }}

    // Release ownership of the resource
    std::unique_ptr<ResourceType> release() noexcept {{
        return std::move(resource_);
    }}
}};"""

    def _generate_cpp_generic(self, component_name: str, objective: str) -> str:
        """Generate generic C++ class."""
        return f"""#pragma once
#include <iostream>
#include <string>

class {component_name} {{
private:
    std::string name_;

public:
    // Constructor
    explicit {component_name}(const std::string& name) : name_(name) {{}}

    // Destructor
    virtual ~{component_name}() = default;

    // Copy constructor
    {component_name}(const {component_name}& other) : name_(other.name_) {{}}

    // Copy assignment operator
    {component_name}& operator=(const {component_name}& other) {{
        if (this != &other) {{
            name_ = other.name_;
        }}
        return *this;
    }}

    // Move constructor
    {component_name}({component_name}&& other) noexcept : name_(std::move(other.name_)) {{}}

    // Move assignment operator
    {component_name}& operator=({component_name}&& other) noexcept {{
        if (this != &other) {{
            name_ = std::move(other.name_);
        }}
        return *this;
    }}

    // Getter
    const std::string& get_name() const noexcept {{
        return name_;
    }}

    // Setter
    void set_name(const std::string& name) {{
        name_ = name;
    }}

    // Purpose: {objective}
    void execute() {{
        std::cout << "Executing " << name_ << std::endl;
    }}
}};"""

    # Missing method implementations
    def _generate_react_about(self, component_name: str) -> str:
        return self._generate_react_generic(component_name, "About section")

    def _generate_react_form(self, component_name: str) -> str:
        return self._generate_react_generic(component_name, "Form component")

    def _generate_lit_card(self, component_name: str) -> str:
        return self._generate_lit_generic(component_name, "Card component")

    def _generate_lit_form(self, component_name: str) -> str:
        return self._generate_lit_generic(component_name, "Form component")

    def _generate_cpp_observer(self, component_name: str) -> str:
        return self._generate_cpp_generic(component_name, "Observer pattern")

    def _generate_cpp_template(self, component_name: str) -> str:
        return self._generate_cpp_generic(component_name, "Template class")

    def _generate_cpp_singleton(self, component_name: str) -> str:
        return self._generate_cpp_generic(component_name, "Singleton pattern")

    def _generate_legacy_component(self, objective: str, component_name: str) -> str:
        """Generate Vue component using legacy hardcoded patterns for backward compatibility."""
        objective_lower = objective.lower()

        # Legacy TodoApp component patterns (keeping for backward compatibility)
        if "todoapp" in objective_lower and "manage" in objective_lower:
            return """<template>
  <div class="todo-app">
    <h1>Todo App</h1>
    <AddTodo @add-todo="addTodo" />
    <div class="todo-list" v-if="todos.length">
      <TodoItem
        v-for="todo in todos"
        :key="todo.id"
        :todo="todo"
        @toggle="toggleTodo"
        @delete="deleteTodo"
      />
    </div>
    <p v-else class="empty-state">No todos yet. Add one above!</p>
    <div class="stats">
      <span>{{ completedCount }}/{{ todos.length }} completed</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import TodoItem from './TodoItem.vue'
import AddTodo from './AddTodo.vue'

// State
const todos = ref([])
const nextId = ref(1)

// Computed
const completedCount = computed(() =>
  todos.value.filter(todo => todo.completed).length
)

// Methods
const addTodo = (text) => {
  todos.value.push({
    id: nextId.value++,
    text: text.trim(),
    completed: false
  })
}

const toggleTodo = (id) => {
  const todo = todos.value.find(t => t.id === id)
  if (todo) todo.completed = !todo.completed
}

const deleteTodo = (id) => {
  todos.value = todos.value.filter(t => t.id !== id)
}
</script>

<style scoped>
.todo-app {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
  font-family: Arial, sans-serif;
}

.todo-list {
  margin: 20px 0;
}

.empty-state {
  text-align: center;
  color: #666;
  font-style: italic;
  padding: 20px;
}

.stats {
  text-align: center;
  margin-top: 20px;
  color: #666;
}
</style>"""

        # TodoItem component
        elif "todoitem" in objective_lower and "individual" in objective_lower:
            return """<template>
  <div class="todo-item" :class="{ completed: todo.completed }">
    <div class="todo-content">
      <button
        @click="$emit('toggle', todo.id)"
        class="toggle-btn"
        :class="{ completed: todo.completed }"
      >
        ✓
      </button>
      <span class="todo-text" :class="{ completed: todo.completed }">
        {{ todo.text }}
      </span>
    </div>
    <button @click="$emit('delete', todo.id)" class="delete-btn">
      ×
    </button>
  </div>
</template>

<script setup>
defineProps(['todo'])
defineEmits(['toggle', 'delete'])
</script>

<style scoped>
.todo-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 15px;
  border: 1px solid #ddd;
  border-radius: 6px;
  margin-bottom: 8px;
  background: white;
  transition: all 0.2s;
}

.todo-item:hover {
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.todo-item.completed {
  opacity: 0.6;
  background: #f9f9f9;
}

.todo-content {
  display: flex;
  align-items: center;
  gap: 10px;
}

.toggle-btn {
  width: 24px;
  height: 24px;
  border: 2px solid #ddd;
  border-radius: 50%;
  background: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: transparent;
}

.toggle-btn.completed {
  background: #42b883;
  border-color: #42b883;
  color: white;
}

.todo-text {
  font-size: 16px;
}

.todo-text.completed {
  text-decoration: line-through;
}

.delete-btn {
  background: #ff4757;
  color: white;
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  cursor: pointer;
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.delete-btn:hover {
  background: #ff3742;
}
</style>"""

        # AddTodo component
        elif "addtodo" in objective_lower and "input field" in objective_lower:
            return """<template>
  <form @submit.prevent="handleSubmit" class="add-todo-form">
    <div class="input-group">
      <input
        v-model="newTodo"
        type="text"
        placeholder="Add a new todo..."
        class="todo-input"
        :class="{ error: hasError }"
        maxlength="100"
      />
      <button
        type="submit"
        class="add-btn"
        :disabled="!newTodo.trim()"
      >
        Add
      </button>
    </div>
    <p v-if="hasError" class="error-message">
      {{ errorMessage }}
    </p>
  </form>
</template>

<script setup>
import { ref } from 'vue'

const emit = defineEmits(['add-todo'])

// State
const newTodo = ref('')
const hasError = ref(false)
const errorMessage = ref('')

// Methods
const handleSubmit = () => {
  const text = newTodo.value.trim()

  // Validation
  if (!text) {
    showError('Please enter a todo item')
    return
  }

  if (text.length < 3) {
    showError('Todo must be at least 3 characters long')
    return
  }

  // Success - emit the new todo
  emit('add-todo', text)
  newTodo.value = ''
  clearError()
}

const showError = (message) => {
  hasError.value = true
  errorMessage.value = message
  setTimeout(clearError, 3000)
}

const clearError = () => {
  hasError.value = false
  errorMessage.value = ''
}
</script>

<style scoped>
.add-todo-form {
  margin-bottom: 20px;
}

.input-group {
  display: flex;
  gap: 10px;
}

.todo-input {
  flex: 1;
  padding: 12px 15px;
  border: 2px solid #ddd;
  border-radius: 6px;
  font-size: 16px;
  transition: border-color 0.2s;
}

.todo-input:focus {
  outline: none;
  border-color: #42b883;
}

.todo-input.error {
  border-color: #ff4757;
}

.add-btn {
  padding: 12px 20px;
  background: #42b883;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  cursor: pointer;
  transition: background 0.2s;
}

.add-btn:hover:not(:disabled) {
  background: #369870;
}

.add-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.error-message {
  color: #ff4757;
  margin-top: 5px;
  font-size: 14px;
}
</style>"""
        # Website App component
        elif "app" in component_name.lower() and (
            "portfolio" in objective_lower
            or "website" in objective_lower
            or "navigation" in objective_lower
        ):
            return """<template>
  <div id="app">
    <Header />
    <router-view />
    <Footer />
  </div>
</template>

<script setup>
import Header from './components/Header.vue'
import Footer from './components/Footer.vue'
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  line-height: 1.6;
  color: #333;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}
</style>"""

        # Website Hero component
        elif "hero" in component_name.lower() and (
            "portfolio" in objective_lower or "website" in objective_lower
        ):
            return """<template>
  <section class="hero">
    <div class="hero-background"></div>
    <div class="container">
      <div class="hero-content">
        <h1 class="hero-title">
          <span class="gradient-text">Full Stack Developer</span>
          <br>Building Digital Solutions
        </h1>
        <p class="hero-subtitle">
          Passionate about creating modern web applications with cutting-edge
          technologies. Specialized in Vue.js, Node.js, and cloud architecture.
        </p>
        <div class="hero-buttons">
          <button class="btn btn-primary">View Projects</button>
          <button class="btn btn-secondary">Contact Me</button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { onMounted } from 'vue'

onMounted(() => {
  // Add scroll animations or other effects
  console.log('Hero component loaded')
})
</script>

<style scoped>
.hero {
  min-height: 100vh;
  display: flex;
  align-items: center;
  position: relative;
  overflow: hidden;
}

.hero-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  opacity: 0.9;
}

.hero-background::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="50" cy="50" r="1" fill="white" opacity="0.1"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
  animation: float 6s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-20px); }
}

.container {
  position: relative;
  z-index: 2;
}

.hero-content {
  text-align: center;
  color: white;
}

.hero-title {
  font-size: 3.5rem;
  font-weight: 700;
  margin-bottom: 1.5rem;
  line-height: 1.2;
}

.gradient-text {
  background: linear-gradient(45deg, #fff, #f0f0f0);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  font-size: 1.25rem;
  margin-bottom: 2rem;
  opacity: 0.9;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

.hero-buttons {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
}

.btn {
  padding: 12px 32px;
  font-size: 1.1rem;
  border: none;
  border-radius: 50px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: 600;
}

.btn-primary {
  background: white;
  color: #667eea;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(0,0,0,0.2);
}

.btn-secondary {
  background: transparent;
  color: white;
  border: 2px solid white;
}

.btn-secondary:hover {
  background: white;
  color: #667eea;
}

@media (max-width: 768px) {
  .hero-title {
    font-size: 2.5rem;
  }

  .hero-subtitle {
    font-size: 1.1rem;
  }

  .hero-buttons {
    flex-direction: column;
    align-items: center;
  }
}
</style>"""

        # Website About component
        elif "about" in component_name.lower() and (
            "portfolio" in objective_lower or "website" in objective_lower
        ):
            return """<template>
  <section class="about">
    <div class="container">
      <div class="about-header">
        <h2 class="section-title">About Me</h2>
        <p class="section-subtitle">Passionate developer with 5+ years of experience</p>
      </div>

      <div class="about-content">
        <div class="about-image">
          <img src="/api/placeholder/300/300" alt="Profile Photo" class="profile-img">
        </div>

        <div class="about-text">
          <h3>Full Stack Developer & Tech Enthusiast</h3>
          <p>
            I'm a passionate full-stack developer specializing in modern web technologies.
            With over 5 years of experience, I've helped startups and enterprises build
            scalable applications that users love.
          </p>

          <div class="skills">
            <h4>Technical Skills</h4>
            <div class="skill-bars">
              <div class="skill">
                <span class="skill-name">Vue.js / React</span>
                <div class="skill-bar">
                  <div class="skill-progress" style="width: 90%"></div>
                </div>
              </div>
              <div class="skill">
                <span class="skill-name">Node.js / Express</span>
                <div class="skill-bar">
                  <div class="skill-progress" style="width: 85%"></div>
                </div>
              </div>
              <div class="skill">
                <span class="skill-name">Python / Django</span>
                <div class="skill-bar">
                  <div class="skill-progress" style="width: 80%"></div>
                </div>
              </div>
              <div class="skill">
                <span class="skill-name">AWS / Docker</span>
                <div class="skill-bar">
                  <div class="skill-progress" style="width: 75%"></div>
                </div>
              </div>
            </div>
          </div>

          <div class="achievements">
            <div class="achievement">
              <h4>50+</h4>
              <p>Projects Completed</p>
            </div>
            <div class="achievement">
              <h4>5+</h4>
              <p>Years Experience</p>
            </div>
            <div class="achievement">
              <h4>99%</h4>
              <p>Client Satisfaction</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { onMounted } from 'vue'

onMounted(() => {
  // Animate skill bars on scroll
  const observeSkills = () => {
    const skillBars = document.querySelectorAll('.skill-progress')
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.style.width = entry.target.style.width
        }
      })
    })

    skillBars.forEach(bar => observer.observe(bar))
  }

  observeSkills()
})
</script>

<style scoped>
.about {
  padding: 100px 0;
  background: #f8f9ff;
}

.about-header {
  text-align: center;
  margin-bottom: 60px;
}

.section-title {
  font-size: 2.5rem;
  font-weight: 700;
  color: #2d3748;
  margin-bottom: 1rem;
}

.section-subtitle {
  font-size: 1.2rem;
  color: #718096;
}

.about-content {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 60px;
  align-items: start;
}

.profile-img {
  width: 100%;
  height: 300px;
  object-fit: cover;
  border-radius: 20px;
  box-shadow: 0 20px 40px rgba(0,0,0,0.1);
}

.about-text h3 {
  font-size: 1.8rem;
  color: #2d3748;
  margin-bottom: 1.5rem;
}

.about-text p {
  font-size: 1.1rem;
  line-height: 1.8;
  color: #4a5568;
  margin-bottom: 2rem;
}

.skills {
  margin-bottom: 2rem;
}

.skills h4 {
  font-size: 1.3rem;
  color: #2d3748;
  margin-bottom: 1.5rem;
}

.skill {
  margin-bottom: 1rem;
}

.skill-name {
  display: block;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #4a5568;
}

.skill-bar {
  width: 100%;
  height: 8px;
  background: #e2e8f0;
  border-radius: 4px;
  overflow: hidden;
}

.skill-progress {
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 4px;
  transition: width 1s ease-in-out;
}

.achievements {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 2rem;
  margin-top: 2rem;
}

.achievement {
  text-align: center;
  padding: 1.5rem;
  background: white;
  border-radius: 15px;
  box-shadow: 0 5px 15px rgba(0,0,0,0.08);
}

.achievement h4 {
  font-size: 2rem;
  font-weight: 700;
  color: #667eea;
  margin-bottom: 0.5rem;
}

.achievement p {
  color: #718096;
  font-weight: 500;
}

@media (max-width: 768px) {
  .about-content {
    grid-template-columns: 1fr;
    gap: 40px;
  }

  .achievements {
    grid-template-columns: 1fr;
  }
}
</style>"""

        # Website Footer component
        elif "footer" in component_name.lower() and (
            "portfolio" in objective_lower or "website" in objective_lower
        ):
            return """<template>
  <footer class="footer">
    <div class="container">
      <div class="footer-content">
        <div class="footer-section">
          <h3 class="footer-title">TechHub</h3>
          <p class="footer-description">
            Building the future with code, one project at a time.
          </p>
          <div class="social-links">
            <a href="#" class="social-link" aria-label="GitHub">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
              </svg>
            </a>
            <a href="#" class="social-link" aria-label="LinkedIn">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
              </svg>
            </a>
            <a href="#" class="social-link" aria-label="Twitter">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z"/>
              </svg>
            </a>
          </div>
        </div>

        <div class="footer-section">
          <h4 class="footer-section-title">Quick Links</h4>
          <ul class="footer-links">
            <li><a href="#home">Home</a></li>
            <li><a href="#about">About</a></li>
            <li><a href="#projects">Projects</a></li>
            <li><a href="#blog">Blog</a></li>
            <li><a href="#contact">Contact</a></li>
          </ul>
        </div>

        <div class="footer-section">
          <h4 class="footer-section-title">Services</h4>
          <ul class="footer-links">
            <li><a href="#">Web Development</a></li>
            <li><a href="#">Mobile Apps</a></li>
            <li><a href="#">UI/UX Design</a></li>
            <li><a href="#">Consulting</a></li>
          </ul>
        </div>

        <div class="footer-section">
          <h4 class="footer-section-title">Contact</h4>
          <div class="contact-info">
            <p>📧 hello@techhub.dev</p>
            <p>📱 +1 (555) 123-4567</p>
            <p>📍 San Francisco, CA</p>
          </div>
        </div>
      </div>

      <div class="footer-bottom">
        <p>&copy; 2024 TechHub. All rights reserved. Built with ❤️ and Vue.js</p>
      </div>
    </div>
  </footer>
</template>

<script setup>
// Footer component logic
</script>

<style scoped>
.footer {
  background: #1a202c;
  color: #e2e8f0;
  padding: 60px 0 20px;
}

.footer-content {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: 40px;
  margin-bottom: 40px;
}

.footer-title {
  font-size: 2rem;
  font-weight: 700;
  color: #667eea;
  margin-bottom: 1rem;
}

.footer-description {
  color: #a0aec0;
  margin-bottom: 2rem;
  line-height: 1.6;
}

.social-links {
  display: flex;
  gap: 1rem;
}

.social-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: #2d3748;
  color: #e2e8f0;
  border-radius: 50%;
  transition: all 0.3s ease;
}

.social-link:hover {
  background: #667eea;
  transform: translateY(-2px);
}

.footer-section-title {
  font-size: 1.2rem;
  font-weight: 600;
  margin-bottom: 1.5rem;
  color: white;
}

.footer-links {
  list-style: none;
}

.footer-links li {
  margin-bottom: 0.75rem;
}

.footer-links a {
  color: #a0aec0;
  text-decoration: none;
  transition: color 0.3s ease;
}

.footer-links a:hover {
  color: #667eea;
}

.contact-info p {
  color: #a0aec0;
  margin-bottom: 0.5rem;
}

.footer-bottom {
  border-top: 1px solid #2d3748;
  padding-top: 20px;
  text-align: center;
}

.footer-bottom p {
  color: #718096;
  font-size: 0.9rem;
}

@media (max-width: 768px) {
  .footer-content {
    grid-template-columns: 1fr;
    gap: 30px;
  }

  .social-links {
    justify-content: center;
  }
}
</style>"""

        # Generic component fallback
        else:
            return f"""<template>
  <div class="{component_name.lower()}-container">
    <h2>{component_name}</h2>
    <p>Vue 3 component for: {objective}</p>
    <div class="content">
      <button @click="handleClick" class="primary-btn">
        Click me
      </button>
      <p v-if="clicked">Button was clicked!</p>
    </div>
  </div>
</template>

<script setup>
import {{ ref }} from 'vue'

const clicked = ref(false)

const handleClick = () => {{
  clicked.value = true
  console.log('{component_name} button clicked')
}}
</script>

<style scoped>
.{component_name.lower()}-container {{
  padding: 20px;
  border-radius: 8px;
  background: #f5f5f5;
  max-width: 500px;
  margin: 0 auto;
}}

.primary-btn {{
  background: #42b883;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
}}

.primary-btn:hover {{
  background: #369870;
}}
</style>"""

    def _generate_hero_component(self, component_name: str) -> str:
        """Generate Hero component with professional styling."""
        return """<template>
  <section class="hero">
    <div class="hero-background"></div>
    <div class="container">
      <div class="hero-content">
        <h1 class="hero-title">
          <span class="gradient-text">Full Stack Developer</span>
          <br>Building Digital Solutions
        </h1>
        <p class="hero-subtitle">
          Passionate about creating modern web applications with cutting-edge
          technologies. Specialized in Vue.js, Node.js, and cloud architecture.
        </p>
        <div class="hero-buttons">
          <button class="btn btn-primary">View Projects</button>
          <button class="btn btn-secondary">Contact Me</button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { onMounted } from 'vue'

onMounted(() => {
  console.log('Hero component loaded')
})
</script>

<style scoped>
.hero {
  min-height: 100vh;
  display: flex;
  align-items: center;
  position: relative;
  overflow: hidden;
}

.hero-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  opacity: 0.9;
}

.container {
  position: relative;
  z-index: 2;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.hero-content {
  text-align: center;
  color: white;
}

.hero-title {
  font-size: 3.5rem;
  font-weight: 700;
  margin-bottom: 1.5rem;
  line-height: 1.2;
}

.gradient-text {
  background: linear-gradient(45deg, #fff, #f0f0f0);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.btn {
  padding: 12px 32px;
  font-size: 1.1rem;
  border: none;
  border-radius: 50px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: 600;
  margin: 0 0.5rem;
}

.btn-primary {
  background: white;
  color: #667eea;
}

.btn-secondary {
  background: transparent;
  color: white;
  border: 2px solid white;
}
</style>"""

    def _generate_about_component(self, component_name: str) -> str:
        """Generate About component with skills and achievements."""
        return """<template>
  <section class="about">
    <div class="container">
      <div class="about-header">
        <h2 class="section-title">About Me</h2>
        <p class="section-subtitle">Passionate developer with 5+ years of experience</p>
      </div>

      <div class="about-content">
        <div class="about-text">
          <h3>Full Stack Developer & Tech Enthusiast</h3>
          <p>
            I'm a passionate full-stack developer specializing in modern web technologies.
            With over 5 years of experience, I've helped startups and enterprises build
            scalable applications that users love.
          </p>

          <div class="skills">
            <h4>Technical Skills</h4>
            <div class="skill-bars">
              <div class="skill">
                <span class="skill-name">Vue.js / React</span>
                <div class="skill-bar">
                  <div class="skill-progress" style="width: 90%"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { onMounted } from 'vue'

onMounted(() => {
  console.log('About component loaded')
})
</script>

<style scoped>
.about {
  padding: 100px 0;
  background: #f8f9ff;
}

.section-title {
  font-size: 2.5rem;
  font-weight: 700;
  color: #2d3748;
  margin-bottom: 1rem;
  text-align: center;
}
</style>"""

    def _generate_footer_component(self, component_name: str) -> str:
        """Generate Footer component with social links."""
        return """<template>
  <footer class="footer">
    <div class="container">
      <div class="footer-content">
        <div class="footer-section">
          <h3 class="footer-title">TechHub</h3>
          <p class="footer-description">
            Building the future with code, one project at a time.
          </p>
        </div>
      </div>

      <div class="footer-bottom">
        <p>&copy; 2024 TechHub. All rights reserved.</p>
      </div>
    </div>
  </footer>
</template>

<style scoped>
.footer {
  background: #1a202c;
  color: #e2e8f0;
  padding: 60px 0 20px;
}

.footer-title {
  font-size: 2rem;
  font-weight: 700;
  color: #667eea;
  margin-bottom: 1rem;
}
</style>"""

    def _generate_app_component(self, component_name: str) -> str:
        """Generate App component with layout structure."""
        return """<template>
  <div id="app">
    <Header />
    <router-view />
    <Footer />
  </div>
</template>

<script setup>
import Header from './components/Header.vue'
import Footer from './components/Footer.vue'
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
</style>"""

    def _generate_header_component(self, component_name: str) -> str:
        """Generate Header/Navigation component."""
        return """<template>
  <header class="header">
    <nav class="navbar">
      <div class="container">
        <div class="nav-brand">
          <h1>TechHub</h1>
        </div>
        <ul class="nav-menu">
          <li><a href="#home">Home</a></li>
          <li><a href="#about">About</a></li>
          <li><a href="#projects">Projects</a></li>
          <li><a href="#contact">Contact</a></li>
        </ul>
      </div>
    </nav>
  </header>
</template>

<style scoped>
.header {
  background: white;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  position: sticky;
  top: 0;
  z-index: 100;
}
</style>"""

    def _generate_todo_component_from_pattern(
        self, component_name: str, objective: str
    ) -> str:
        """Generate Todo component based on pattern matching."""
        if "todoapp" in objective.lower():
            return self._generate_legacy_todo_app()
        elif "todoitem" in objective.lower():
            return self._generate_legacy_todo_item()
        elif "addtodo" in objective.lower():
            return self._generate_legacy_add_todo()
        else:
            return self._generate_generic_component(component_name)

    def _generate_legacy_todo_app(self) -> str:
        """Generate legacy TodoApp component for backward compatibility."""
        return """<template>
  <div class="todo-app">
    <h1>Todo App</h1>
    <AddTodo @add-todo="addTodo" />
    <div class="todo-list" v-if="todos.length">
      <TodoItem
        v-for="todo in todos"
        :key="todo.id"
        :todo="todo"
        @toggle="toggleTodo"
        @delete="deleteTodo"
      />
    </div>
    <p v-else class="empty-state">No todos yet. Add one above!</p>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import TodoItem from './TodoItem.vue'
import AddTodo from './AddTodo.vue'

const todos = ref([])
const nextId = ref(1)

const addTodo = (text) => {
  todos.value.push({
    id: nextId.value++,
    text,
    completed: false
  })
}

const toggleTodo = (id) => {
  const todo = todos.value.find(t => t.id === id)
  if (todo) todo.completed = !todo.completed
}

const deleteTodo = (id) => {
  const index = todos.value.findIndex(t => t.id === id)
  if (index > -1) todos.value.splice(index, 1)
}
</script>

<style scoped>
.todo-app {
  max-width: 600px;
  margin: 2rem auto;
  padding: 2rem;
}
</style>"""

    def _generate_legacy_todo_item(self) -> str:
        """Generate legacy TodoItem component for backward compatibility."""
        return """<template>
  <div class="todo-item" :class="{ completed: todo.completed }">
    <input
      type="checkbox"
      :checked="todo.completed"
      @change="$emit('toggle', todo.id)"
    />
    <span class="todo-text">{{ todo.text }}</span>
    <button @click="$emit('delete', todo.id)" class="delete-btn">×</button>
  </div>
</template>

<script setup>
defineProps(['todo'])
defineEmits(['toggle', 'delete'])
</script>

<style scoped>
.todo-item {
  display: flex;
  align-items: center;
  padding: 0.5rem;
  border-bottom: 1px solid #eee;
}

.completed .todo-text {
  text-decoration: line-through;
  opacity: 0.6;
}
</style>"""

    def _generate_legacy_add_todo(self) -> str:
        """Generate legacy AddTodo component for backward compatibility."""
        return """<template>
  <form @submit.prevent="addTodo" class="add-todo">
    <input
      v-model="newTodo"
      placeholder="What needs to be done?"
      required
    />
    <button type="submit">Add Todo</button>
  </form>
</template>

<script setup>
import { ref } from 'vue'

const emit = defineEmits(['add-todo'])
const newTodo = ref('')

const addTodo = () => {
  if (newTodo.value.trim()) {
    emit('add-todo', newTodo.value.trim())
    newTodo.value = ''
  }
}
</script>

<style scoped>
.add-todo {
  display: flex;
  margin-bottom: 2rem;
  gap: 1rem;
}
</style>"""

    def _generate_generic_component(self, component_name: str) -> str:
        """Generate generic Vue component as ultimate fallback."""
        return f"""<template>
  <div class="{component_name.lower()}-container">
    <h2>{component_name}</h2>
    <p>Vue 3 component ready for customization</p>
    <button @click="handleClick" class="primary-btn">
      Click me
    </button>
    <p v-if="clicked">Button was clicked!</p>
  </div>
</template>

<script setup>
import {{ ref }} from 'vue'

const clicked = ref(false)

const handleClick = () => {{
  clicked.value = true
}}
</script>

<style scoped>
.{component_name.lower()}-container {{
  padding: 2rem;
  border: 1px solid #ddd;
  border-radius: 8px;
}}
</style>"""

    async def create_agile_project(
        self, target_dir: str, project_name: str, project_type: str = "file_system"
    ):
        """Create a comprehensive agile project.

        This method integrates the enhanced scrum agents directly into
        autogen's CoderAgent to execute agile projects with full
        scrum methodology, multiple sprints, and comprehensive development.
        """
        from autogen_mcp.scrum_agents import create_major_agile_project

        # Store the current project request in memory if available
        if self.memory_service:
            self.make_decision(
                decision=f"Agile project creation: {project_name}",
                reasoning=f"Initiating {project_type} project with full scrum process",
                context=f"Target: {target_dir}, Type: {project_type}",
            )

        print(f"[CoderAgent] Initiating agile project: {project_name}")
        print(f"[CoderAgent] Project type: {project_type}")
        print(f"[CoderAgent] Target directory: {target_dir}")

        # Execute the agile project
        team = await create_major_agile_project(
            target_dir=target_dir, project_name=project_name, project_type=project_type
        )

        # Return structured response
        return {
            "agent": "Coder",
            "action": "agile_project",
            "project_name": project_name,
            "project_type": project_type,
            "target_dir": target_dir,
            "team_size": len(team.all_members),
            "message": f"[CoderAgent] Completed agile project: {project_name}",
            "success": True,
        }


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

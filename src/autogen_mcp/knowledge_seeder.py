"""
Knowledge seeding for global memory collection.

Pre-populates the global collection with foundational knowledge including:
- PDCA (Plan-Do-Check-Act) principles
- OOP (Object-Oriented Programming) best practices
- Coding standards and security rules
- Reusable solution patterns
"""

from __future__ import annotations

from typing import Dict, List

from autogen_mcp.memory_collections import CollectionManager, MemoryEvent, MemoryScope
from autogen_mcp.embeddings import EmbeddingService
from autogen_mcp.observability import get_logger


class KnowledgeSeeder:
    """Seeds global knowledge collection with foundational principles and patterns."""

    def __init__(self, collection_manager: CollectionManager):
        self.collection_manager = collection_manager
        self.embedding_service = EmbeddingService()
        self.logger = get_logger("autogen.knowledge_seeder")

    def get_global_knowledge(self) -> List[Dict[str, any]]:
        """Get all foundational knowledge to seed in global collection."""
        return [
            # PDCA Principles
            {
                "content": """Plan-Do-Check-Act (PDCA) Cycle: A continuous improvement methodology.
                Plan: Identify opportunities and plan for change.
                Do: Implement the change on a small scale.
                Check: Use data to analyze the results and determine success.
                Act: If successful, implement change on wider scale; if not, refine.""",
                "category": "methodology",
                "tags": ["pdca", "continuous-improvement", "process"],
                "importance": 0.9,
                "domain": "software-development",
                "language": "general",
            },
            # OOP Principles
            {
                "content": """Object-Oriented Programming (OOP) Four Pillars:
                1. Encapsulation: Bundle data and methods that work on data within classes
                2. Inheritance: Create new classes based on existing classes
                3. Polymorphism: Objects of different types can be treated as same type
                4. Abstraction: Hide complex implementation details behind simple interfaces""",
                "category": "programming-paradigm",
                "tags": [
                    "oop",
                    "encapsulation",
                    "inheritance",
                    "polymorphism",
                    "abstraction",
                ],
                "importance": 0.95,
                "domain": "software-development",
                "language": "general",
            },
            # SOLID Principles
            {
                "content": """SOLID Principles for Object-Oriented Design:
                S - Single Responsibility: Class should have one reason to change
                O - Open/Closed: Open for extension, closed for modification
                L - Liskov Substitution: Derived classes must be substitutable for base
                I - Interface Segregation: Many client-specific interfaces better than one
                D - Dependency Inversion: Depend on abstractions, not concretions""",
                "category": "design-principles",
                "tags": [
                    "solid",
                    "single-responsibility",
                    "open-closed",
                    "liskov",
                    "interface-segregation",
                    "dependency-inversion",
                ],
                "importance": 0.9,
                "domain": "software-development",
                "language": "general",
            },
            # Security Rules
            {
                "content": """Security Best Practices:
                - Never store secrets in code or configuration files
                - Use environment variables or secure secret management
                - Validate all inputs and sanitize outputs
                - Use HTTPS for all communications
                - Implement proper authentication and authorization
                - Regular security updates and dependency scanning""",
                "category": "security",
                "tags": [
                    "security",
                    "secrets",
                    "authentication",
                    "https",
                    "validation",
                ],
                "importance": 0.95,
                "domain": "security",
                "language": "general",
            },
            # Code Quality Standards
            {
                "content": """Code Quality Standards:
                - Use meaningful variable and function names
                - Keep functions small and focused on single responsibility
                - Add comprehensive documentation and comments
                - Write unit tests for all business logic
                - Use consistent formatting and linting tools
                - Handle errors gracefully with proper exception handling""",
                "category": "code-quality",
                "tags": [
                    "clean-code",
                    "naming",
                    "documentation",
                    "testing",
                    "error-handling",
                ],
                "importance": 0.85,
                "domain": "software-development",
                "language": "general",
            },
            # Git Best Practices
            {
                "content": """Git Best Practices:
                - Use descriptive commit messages with imperative mood
                - Create feature branches for new work
                - Use pull requests for code review
                - Keep commits atomic and focused
                - Use conventional commit format: type(scope): description
                - Squash commits before merging to main""",
                "category": "version-control",
                "tags": ["git", "commits", "branches", "pull-requests", "code-review"],
                "importance": 0.8,
                "domain": "development-workflow",
                "language": "general",
            },
            # Testing Principles
            {
                "content": """Testing Best Practices:
                - Follow the Testing Pyramid: Unit > Integration > E2E tests
                - Write tests before or alongside code (TDD)
                - Use descriptive test names that explain behavior
                - Keep tests isolated and independent
                - Mock external dependencies in unit tests
                - Maintain high test coverage for critical paths""",
                "category": "testing",
                "tags": [
                    "testing",
                    "tdd",
                    "unit-tests",
                    "integration-tests",
                    "mocking",
                ],
                "importance": 0.85,
                "domain": "software-development",
                "language": "general",
            },
            # API Design Principles
            {
                "content": """RESTful API Design Principles:
                - Use HTTP methods correctly (GET, POST, PUT, DELETE, PATCH)
                - Design intuitive and consistent URL patterns
                - Use proper HTTP status codes
                - Implement proper error handling with meaningful messages
                - Version your APIs to maintain backward compatibility
                - Document APIs with OpenAPI/Swagger specifications""",
                "category": "api-design",
                "tags": [
                    "rest",
                    "api",
                    "http",
                    "status-codes",
                    "versioning",
                    "documentation",
                ],
                "importance": 0.8,
                "domain": "api-development",
                "language": "general",
            },
            # Database Best Practices
            {
                "content": """Database Best Practices:
                - Normalize data to reduce redundancy
                - Use proper indexing for query performance
                - Implement database migrations for schema changes
                - Use transactions for data consistency
                - Avoid N+1 query problems with eager loading
                - Backup data regularly and test restore procedures""",
                "category": "database",
                "tags": [
                    "database",
                    "normalization",
                    "indexing",
                    "migrations",
                    "transactions",
                    "performance",
                ],
                "importance": 0.8,
                "domain": "data-management",
                "language": "general",
            },
            # Python-Specific Best Practices
            {
                "content": """Python Best Practices:
                - Follow PEP 8 style guide for formatting
                - Use type hints for better code documentation
                - Prefer list comprehensions for simple transformations
                - Use context managers for resource management (with statements)
                - Handle exceptions specifically, avoid bare except clauses
                - Use virtual environments for dependency isolation""",
                "category": "language-specific",
                "tags": [
                    "python",
                    "pep8",
                    "type-hints",
                    "context-managers",
                    "exceptions",
                ],
                "importance": 0.85,
                "domain": "software-development",
                "language": "python",
            },
            # TypeScript Best Practices
            {
                "content": """TypeScript Best Practices:
                - Use strict TypeScript configuration for better type safety
                - Define interfaces for object shapes and contracts
                - Use union types and type guards for flexible yet safe code
                - Prefer const assertions for immutable data
                - Use generic types for reusable components
                - Enable strict null checks to prevent runtime errors""",
                "category": "language-specific",
                "tags": [
                    "typescript",
                    "interfaces",
                    "generics",
                    "type-safety",
                    "strict-mode",
                ],
                "importance": 0.85,
                "domain": "software-development",
                "language": "typescript",
            },
            # Agile/Scrum Principles
            {
                "content": """Agile Development Principles:
                - Individuals and interactions over processes and tools
                - Working software over comprehensive documentation
                - Customer collaboration over contract negotiation
                - Responding to change over following a plan
                - Deliver working software frequently in short iterations
                - Welcome changing requirements even late in development""",
                "category": "methodology",
                "tags": [
                    "agile",
                    "scrum",
                    "iteration",
                    "collaboration",
                    "change-management",
                ],
                "importance": 0.8,
                "domain": "project-management",
                "language": "general",
            },
            # Design Patterns
            {
                "content": """Common Design Patterns:
                - Singleton: Ensure only one instance of a class exists
                - Factory: Create objects without specifying exact classes
                - Observer: Define one-to-many dependency between objects
                - Strategy: Define family of algorithms and make them interchangeable
                - Repository: Encapsulate data access logic
                - MVC: Separate concerns into Model, View, Controller""",
                "category": "design-patterns",
                "tags": [
                    "singleton",
                    "factory",
                    "observer",
                    "strategy",
                    "repository",
                    "mvc",
                ],
                "importance": 0.8,
                "domain": "software-architecture",
                "language": "general",
            },
            # Vue.js Component Generation Patterns
            {
                "content": """Vue.js Hero Component Pattern: For creating landing page hero sections.
                Template: Full viewport height section with background, centered content, call-to-action buttons
                Script: Vue 3 Composition API with onMounted lifecycle
                Style: Gradient backgrounds, responsive typography, hover animations
                Keywords: hero, landing, banner, homepage, portfolio, website
                Use Case: Main banner section for websites, portfolios, marketing pages""",
                "category": "vue-component-pattern",
                "tags": [
                    "vue3",
                    "hero",
                    "component",
                    "website",
                    "portfolio",
                    "landing",
                ],
                "importance": 0.9,
                "domain": "frontend-development",
                "language": "vue",
            },
            {
                "content": """Vue.js About Component Pattern: For creating about/bio sections.
                Template: Grid layout with profile image, text content, skills, achievements
                Script: Intersection Observer for skill bar animations, Vue 3 Composition API
                Style: Two-column responsive layout, skill progress bars, achievement cards
                Keywords: about, bio, profile, skills, experience, team, portfolio
                Use Case: About pages, team profiles, developer portfolios, company info""",
                "category": "vue-component-pattern",
                "tags": [
                    "vue3",
                    "about",
                    "profile",
                    "skills",
                    "component",
                    "portfolio",
                ],
                "importance": 0.9,
                "domain": "frontend-development",
                "language": "vue",
            },
            {
                "content": """Vue.js Footer Component Pattern: For creating website footers.
                Template: Multi-column layout with brand, links, contact, social media
                Script: Basic Vue 3 setup, minimal JavaScript needed
                Style: Dark theme, responsive grid, social icons, hover effects
                Keywords: footer, contact, social, links, navigation, copyright
                Use Case: Website footers, contact sections, social media links""",
                "category": "vue-component-pattern",
                "tags": [
                    "vue3",
                    "footer",
                    "contact",
                    "social",
                    "navigation",
                    "website",
                ],
                "importance": 0.8,
                "domain": "frontend-development",
                "language": "vue",
            },
            {
                "content": """Vue.js App Component Pattern: For main application shell.
                Template: Router view with header/footer layout structure
                Script: Import header/footer components, Vue 3 setup
                Style: Global styles, CSS reset, container classes, flexbox layout
                Keywords: app, layout, shell, main, root, navigation, website
                Use Case: Main application wrapper, website layout, SPA shell""",
                "category": "vue-component-pattern",
                "tags": ["vue3", "app", "layout", "main", "shell", "website"],
                "importance": 0.9,
                "domain": "frontend-development",
                "language": "vue",
            },
            {
                "content": """Vue.js Header/Navigation Component Pattern: For website navigation.
                Template: Logo, navigation menu, mobile hamburger menu, CTAs
                Script: Reactive menu state, scroll effects, mobile menu toggle
                Style: Sticky navigation, responsive breakpoints, smooth transitions
                Keywords: header, navigation, nav, menu, navbar, logo, mobile
                Use Case: Website navigation, app header, menu systems""",
                "category": "vue-component-pattern",
                "tags": ["vue3", "header", "navigation", "menu", "navbar", "website"],
                "importance": 0.9,
                "domain": "frontend-development",
                "language": "vue",
            },
            {
                "content": """Vue.js Todo Component Pattern: For task management interfaces.
                Template: Input form, todo list, item actions (edit/delete/complete)
                Script: Reactive state management, CRUD operations, local storage
                Style: Clean list layout, status indicators, action buttons
                Keywords: todo, task, list, crud, management, productivity, app
                Use Case: Task management apps, todo lists, project management""",
                "category": "vue-component-pattern",
                "tags": ["vue3", "todo", "task", "crud", "list", "management", "app"],
                "importance": 0.8,
                "domain": "frontend-development",
                "language": "vue",
            },
            # React Component Patterns
            {
                "content": """React Hero Component Pattern: For landing page hero sections.
                JSX: Full viewport height section with styled-components or CSS modules
                Hooks: useState, useEffect for animations and interactions
                Props: Title, subtitle, backgroundImage, ctaButtons array
                Keywords: hero, landing, banner, homepage, portfolio, website, react
                Use Case: Main banner for React websites, Next.js apps, marketing pages""",
                "category": "react-component-pattern",
                "tags": [
                    "react",
                    "hero",
                    "component",
                    "website",
                    "portfolio",
                    "landing",
                    "jsx",
                ],
                "importance": 0.9,
                "domain": "frontend-development",
                "language": "react",
            },
            {
                "content": """React About Component Pattern: For profile/bio sections.
                JSX: Grid layout with profile card, skills section, achievements
                Hooks: useState for skill animations, useRef for intersection observer
                Props: profileData, skills array, achievements array
                Keywords: about, bio, profile, skills, experience, team, portfolio, react
                Use Case: About pages, team profiles, developer portfolios in React""",
                "category": "react-component-pattern",
                "tags": [
                    "react",
                    "about",
                    "profile",
                    "skills",
                    "component",
                    "portfolio",
                    "jsx",
                ],
                "importance": 0.9,
                "domain": "frontend-development",
                "language": "react",
            },
            {
                "content": """React Header Component Pattern: For navigation components.
                JSX: Responsive navbar with mobile hamburger menu
                Hooks: useState for menu state, useEffect for scroll detection
                Props: logo, menuItems array, brand props
                Keywords: header, navigation, nav, menu, navbar, logo, mobile, react
                Use Case: Website navigation, app header, React Router integration""",
                "category": "react-component-pattern",
                "tags": ["react", "header", "navigation", "menu", "navbar", "jsx"],
                "importance": 0.9,
                "domain": "frontend-development",
                "language": "react",
            },
            # Lit 3 Component Patterns
            {
                "content": """Lit 3 Hero Component Pattern: Web component hero section.
                Template: lit-html template with CSS-in-JS styling
                Properties: @property decorators for title, subtitle, backgroundUrl
                Events: Custom events for button interactions
                Keywords: hero, landing, banner, lit, web-component, portfolio
                Use Case: Framework-agnostic hero sections, micro-frontends""",
                "category": "lit-component-pattern",
                "tags": [
                    "lit3",
                    "hero",
                    "web-component",
                    "template",
                    "portfolio",
                    "landing",
                ],
                "importance": 0.8,
                "domain": "frontend-development",
                "language": "lit",
            },
            {
                "content": """Lit 3 Card Component Pattern: Reusable card web component.
                Template: Flexible card layout with slots for content
                Properties: @property for title, image, variant styling
                Styling: Shadow DOM with :host() selectors and CSS custom properties
                Keywords: card, component, lit, web-component, reusable, ui
                Use Case: Product cards, blog posts, profile cards, dashboards""",
                "category": "lit-component-pattern",
                "tags": ["lit3", "card", "web-component", "ui", "reusable"],
                "importance": 0.8,
                "domain": "frontend-development",
                "language": "lit",
            },
            {
                "content": """Lit 3 Form Component Pattern: Interactive form web component.
                Template: Form elements with validation and error display
                Properties: @property for form schema, validation rules
                Methods: Custom validation, form submission handling
                Keywords: form, validation, input, lit, web-component, interactive
                Use Case: Contact forms, login forms, data entry interfaces""",
                "category": "lit-component-pattern",
                "tags": ["lit3", "form", "validation", "web-component", "interactive"],
                "importance": 0.8,
                "domain": "frontend-development",
                "language": "lit",
            },
            # C++ Class Patterns
            {
                "content": """C++ RAII Class Pattern: Resource Acquisition Is Initialization.
                Header: Constructor acquires resource, destructor releases it
                Implementation: Exception-safe resource management
                Features: Copy/move semantics, smart pointers integration
                Keywords: raii, resource, memory, constructor, destructor, cpp
                Use Case: File handles, memory management, mutex locks, database connections""",
                "category": "cpp-class-pattern",
                "tags": ["cpp", "raii", "resource", "memory", "class", "constructor"],
                "importance": 0.9,
                "domain": "systems-programming",
                "language": "cpp",
            },
            {
                "content": """C++ Observer Pattern Class: Event notification system.
                Header: Abstract Observer base, Subject with observer list
                Implementation: Subscribe/unsubscribe methods, notification dispatch
                Features: Type-safe callbacks, weak pointer usage to avoid cycles
                Keywords: observer, pattern, event, notification, listener, cpp
                Use Case: Event systems, MVC architecture, GUI frameworks, signals/slots""",
                "category": "cpp-class-pattern",
                "tags": [
                    "cpp",
                    "observer",
                    "pattern",
                    "event",
                    "class",
                    "design-pattern",
                ],
                "importance": 0.8,
                "domain": "systems-programming",
                "language": "cpp",
            },
            {
                "content": """C++ Template Class Pattern: Generic programming with templates.
                Header: Template parameter declarations, SFINAE constraints
                Implementation: Template specializations, concept requirements
                Features: Type traits, perfect forwarding, variadic templates
                Keywords: template, generic, metaprogramming, concepts, cpp
                Use Case: Containers, algorithms, type-safe interfaces, libraries""",
                "category": "cpp-class-pattern",
                "tags": ["cpp", "template", "generic", "metaprogramming", "class"],
                "importance": 0.9,
                "domain": "systems-programming",
                "language": "cpp",
            },
            {
                "content": """C++ Singleton Pattern Class: Single instance management.
                Header: Private constructor, static getInstance method
                Implementation: Thread-safe initialization, copy prevention
                Features: Lazy initialization, thread safety, memory cleanup
                Keywords: singleton, pattern, instance, static, thread-safe, cpp
                Use Case: Configuration managers, logging systems, database connections""",
                "category": "cpp-class-pattern",
                "tags": [
                    "cpp",
                    "singleton",
                    "pattern",
                    "static",
                    "class",
                    "thread-safe",
                ],
                "importance": 0.7,
                "domain": "systems-programming",
                "language": "cpp",
            },
        ]

    def seed_global_knowledge(self) -> Dict[str, any]:
        """Seed the global collection with foundational knowledge."""
        self.logger.info("Starting global knowledge seeding")

        # Ensure global collection exists
        collection_name = self.collection_manager.ensure_collection(MemoryScope.GLOBAL)

        knowledge_items = self.get_global_knowledge()
        seeded_count = 0
        errors = []

        for item in knowledge_items:
            try:
                # Create memory event with proper structure
                event = MemoryEvent(
                    content=item["content"],
                    scope=MemoryScope.GLOBAL,
                    metadata={
                        "category": item["category"],
                        "importance": item["importance"],
                        "tags": item["tags"],
                        "domain": item["domain"],
                        "language": item["language"],
                        "seeded": True,
                        "seeded_at": "2025-09-12T16:00:00Z",  # Current date
                    },
                )

                # Generate embedding for the content
                event.vector = self.embedding_service.encode_one(event.content)

                # Validate event structure
                if self.collection_manager.validate_event(event):
                    # Store in Qdrant
                    self.collection_manager.qdrant.upsert_point(
                        collection=collection_name,
                        point_id=event.event_id,
                        vector=event.vector,
                        payload={
                            "content": event.content,
                            "scope": event.scope.value,
                            "timestamp": event.timestamp,
                            **event.metadata,
                        },
                    )
                    seeded_count += 1
                else:
                    errors.append(f"Validation failed for: {item['category']}")

            except Exception as e:
                error_msg = f"Failed to seed {item['category']}: {str(e)}"
                errors.append(error_msg)
                self.logger.warning(error_msg)

        result = {
            "collection": collection_name,
            "seeded_count": seeded_count,
            "total_items": len(knowledge_items),
            "errors": errors,
            "success": len(errors) == 0,
        }

        self.logger.info(
            f"Global knowledge seeding completed: {seeded_count}/{len(knowledge_items)} items",
            extra={"extra": result},
        )

        return result

    def verify_seeded_knowledge(self) -> Dict[str, any]:
        """Verify that seeded knowledge is accessible via search."""
        try:
            collection_name = self.collection_manager.get_collection_name(
                MemoryScope.GLOBAL
            )

            # Test search for PDCA
            pdca_vector = self.embedding_service.encode_one(
                "plan do check act methodology"
            )
            pdca_results = self.collection_manager.qdrant.search(
                collection=collection_name, vector=pdca_vector, limit=3
            )

            # Test search for OOP
            oop_vector = self.embedding_service.encode_one(
                "object oriented programming encapsulation inheritance"
            )
            oop_results = self.collection_manager.qdrant.search(
                collection=collection_name, vector=oop_vector, limit=3
            )

            verification = {
                "pdca_found": len(pdca_results.get("result", [])) > 0,
                "oop_found": len(oop_results.get("result", [])) > 0,
                "pdca_results_count": len(pdca_results.get("result", [])),
                "oop_results_count": len(oop_results.get("result", [])),
            }

            self.logger.info(
                "Knowledge verification completed", extra={"extra": verification}
            )
            return verification

        except Exception as e:
            error_msg = f"Knowledge verification failed: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg, "success": False}

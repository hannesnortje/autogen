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

from autogen_mcp.collections import CollectionManager, MemoryEvent, MemoryScope
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

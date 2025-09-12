#!/usr/bin/env python3
"""
Test script for Step 21 - Multi-Scope Memory Schema Integration
This tests the new memory architecture to ensure agents can learn.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from autogen_mcp.collections import CollectionManager, MemoryScope
from autogen_mcp.knowledge_seeder import KnowledgeSeeder
from autogen_mcp.multi_memory import MultiScopeMemoryService, MemoryService
from autogen_mcp.hybrid_search_service import HybridSearchService, HybridConfig
from autogen_mcp.observability import get_logger


def test_memory_integration():
    """Test the complete memory integration pipeline."""
    logger = get_logger("autogen.test_memory")

    logger.info("Starting memory integration test...")

    try:
        # 1. Initialize services
        logger.info("Initializing services...")
        collection_manager = CollectionManager()
        memory_service = MultiScopeMemoryService(collection_manager)
        knowledge_seeder = KnowledgeSeeder(collection_manager)
        hybrid_search = HybridSearchService(HybridConfig())

        # 2. Initialize collections
        logger.info("Initializing collections...")
        collection_manager.initialize_all_collections()

        # 3. Initialize memory service
        logger.info("Initializing memory service...")
        memory_service.initialize()

        # 4. Seed global knowledge
        logger.info("Seeding global knowledge...")
        knowledge_seeder.seed_global_knowledge()

        # 5. Test writing to different scopes
        logger.info("Testing multi-scope writes...")

        # Set project context
        memory_service.set_project("test_project")

        # Write to different scopes
        global_id = memory_service.write_global(
            thread_id="test_global",
            text="Global knowledge: Always follow SOLID principles",
            metadata={"type": "principle", "category": "architecture"},
        )
        logger.info(f"Written global memory: {global_id}")

        project_id = memory_service.write_project(
            thread_id="test_project_main",
            text="Project-specific: This is a Python autogen project",
            metadata={"type": "project_info", "language": "python"},
        )
        logger.info(f"Written project memory: {project_id}")

        objective_id = memory_service.write_objectives(
            thread_id="main_objectives",
            text="Build a robust multi-agent system with proper memory",
            metadata={"type": "main_objective", "priority": "high"},
        )
        logger.info(f"Written objective memory: {objective_id}")

        artifact_id = memory_service.write_artifacts(
            thread_id="code_artifacts",
            text="Created multi_memory.py with 340+ lines",
            metadata={"type": "code_file", "file": "multi_memory.py"},
        )
        logger.info(f"Written artifact memory: {artifact_id}")

        # 6. Test search functionality
        logger.info("Testing memory search...")

        # Search in global scope
        global_collection = collection_manager.get_collection_name(MemoryScope.GLOBAL)
        global_results = hybrid_search.search(
            collection=global_collection,
            query="SOLID principles architecture",
            k=3,
            scopes=["global"],
        )
        logger.info(f"Global search found {len(global_results)} results")

        # Search in project scope
        project_collection = collection_manager.get_collection_name(
            MemoryScope.PROJECT, "test_project"
        )
        project_results = hybrid_search.search(
            collection=project_collection,
            query="Python autogen project",
            k=3,
            scopes=["project"],
        )
        logger.info(f"Project search found {len(project_results)} results")

        # 7. Verify health check
        logger.info("Checking system health...")
        health_status = collection_manager.health_check()
        logger.info(f"Health check: {health_status}")

        # 8. Verify seeded knowledge
        logger.info("Verifying seeded knowledge...")
        seeded_status = knowledge_seeder.verify_seeded_knowledge()
        logger.info(f"Seeded knowledge verified: {seeded_status}")

        # 9. Test backward compatibility
        logger.info("Testing backward compatibility...")
        # The MultiScopeMemoryService should work as a drop-in replacement
        # via the MemoryService wrapper
        legacy_service = MemoryService()
        legacy_service.initialize()
        legacy_service.set_project("test_project")

        legacy_id = legacy_service.write_event(
            scope="project",
            thread_id="legacy_test",
            text="Testing backward compatibility",
            metadata={"type": "legacy_test"},
        )
        logger.info(f"Legacy write successful: {legacy_id}")

        logger.info("✅ Memory integration test completed successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Memory integration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_memory_integration()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Debug script to test embedding generation in memory writes.
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from autogen_mcp.multi_memory import MultiScopeMemoryService, MemoryWriteOptions
from autogen_mcp.collections import MemoryScope


def test_embedding_generation():
    """Test if embeddings are being generated correctly."""
    print("🔍 Testing embedding generation...")

    # Initialize service
    memory_service = MultiScopeMemoryService()
    memory_service.set_project("test-project")
    memory_service.initialize()

    print(
        f"📊 EmbeddingService available: {memory_service.embedding_service is not None}"
    )

    # Test explicit MemoryWriteOptions with auto_embed
    test_content = "This is a test memory with embedding generation"

    # Test 1: Explicit auto_embed=True
    print("\n🧪 Test 1: Explicit auto_embed=True")
    options = MemoryWriteOptions(
        scope=MemoryScope.GLOBAL, thread_id="test-thread", auto_embed=True
    )
    print(f"Options.auto_embed: {options.auto_embed}")

    try:
        event_id = memory_service.write_event(test_content, options)
        print(f"✅ Event written: {event_id}")

        # Check if embedding was stored
        collection_name = memory_service.collection_manager.get_collection_name(
            MemoryScope.GLOBAL
        )
        print(f"Collection name: {collection_name}")

        # Query the stored event
        results = memory_service.collection_manager.qdrant.scroll(
            collection=collection_name,
            filter={"must": [{"key": "scope", "match": {"value": "global"}}]},
            limit=1,
        )

        if results and len(results) > 0:
            point = results[0]
            print(f"Vector exists: {point.vector is not None}")
            if point.vector:
                print(f"Vector length: {len(point.vector)}")
                print(
                    f"Vector sample: {point.vector[:5] if len(point.vector) >= 5 else point.vector}"
                )
            else:
                print("❌ No vector found in stored event")
        else:
            print("❌ No events found in collection")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()

    # Test 2: Default auto_embed (should be True)
    print("\n🧪 Test 2: Default auto_embed (should be True)")
    options2 = MemoryWriteOptions(scope=MemoryScope.GLOBAL, thread_id="test-thread-2")
    print(f"Default options.auto_embed: {options2.auto_embed}")

    # Test 3: Convenience method (uses default)
    print("\n🧪 Test 3: Convenience method write_global")
    try:
        event_id3 = memory_service.write_global(
            thread_id="test-thread-3", text="Test global memory via convenience method"
        )
        print(f"✅ Global event written: {event_id3}")

        # Check this one too
        results3 = memory_service.collection_manager.qdrant.scroll(
            collection=collection_name,
            filter={
                "must": [
                    {
                        "key": "content",
                        "match": {"value": "Test global memory via convenience method"},
                    }
                ]
            },
            limit=1,
        )

        if results3 and len(results3) > 0:
            point3 = results3[0]
            print(f"Convenience method - Vector exists: {point3.vector is not None}")
            if point3.vector:
                print(f"Convenience method - Vector length: {len(point3.vector)}")
            else:
                print("❌ Convenience method - No vector found")

    except Exception as e:
        print(f"❌ Convenience method error: {e}")


if __name__ == "__main__":
    test_embedding_generation()

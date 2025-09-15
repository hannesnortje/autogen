#!/usr/bin/env python3
"""
Test retrieving a specific event by ID to check vectors.
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from autogen_mcp.multi_memory import MultiScopeMemoryService


def test_direct_retrieval():
    """Test writing an event and retrieving it directly by ID."""
    print("🔍 Testing direct event retrieval by ID...")

    # Initialize service
    memory_service = MultiScopeMemoryService()
    memory_service.set_project("test-project")
    memory_service.initialize()

    # Write an event
    print("\n✍️ Writing event...")
    from autogen_mcp.collections import MemoryScope

    collection_name = memory_service.collection_manager.get_collection_name(
        MemoryScope.GLOBAL
    )

    test_content = "Vector retrieval test by ID"
    event_id = memory_service.write_global(thread_id="direct-test", text=test_content)
    print(f"✅ Wrote event: {event_id}")
    print(f"Collection: {collection_name}")

    # Retrieve the specific event by ID
    print(f"\n🔍 Retrieving event {event_id} directly...")
    try:
        result = memory_service.collection_manager.qdrant.retrieve_point(
            collection=collection_name,
            point_id=event_id,
            with_payload=True,
            with_vector=True,
        )

        print(f"Retrieved result: {result}")

        # Parse the result
        if "result" in result:
            point = result["result"]

            print("\n📊 Point analysis:")
            print(f"  ID: {point.get('id', 'missing')}")

            # Check vector
            vector = point.get("vector")
            print(f"  Has vector: {vector is not None}")
            if vector is not None:
                print(f"  Vector type: {type(vector)}")
                print(f"  Vector length: {len(vector)}")
                if len(vector) > 0:
                    print(f"  Vector sample: {vector[:3]}")
                    print("  ✅ Vector stored and retrieved successfully!")
                else:
                    print("  ❌ Vector is empty")
            else:
                print("  ❌ No vector in response")

            # Check payload
            payload = point.get("payload", {})
            content = payload.get("content", "missing")
            print(f"  Content: {content}")

            if content == test_content:
                print("  ✅ Content matches!")
            else:
                print("  ❌ Content mismatch")
        else:
            print(f"❌ No 'result' in response: {result}")

    except Exception as e:
        print(f"❌ Error retrieving event: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_direct_retrieval()

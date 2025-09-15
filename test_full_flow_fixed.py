#!/usr/bin/env python3
"""
Test complete write and storage flow with vector retrieval.
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from autogen_mcp.multi_memory import MultiScopeMemoryService


def test_write_and_check():
    """Test writing an event and checking if the vector is stored."""
    print("🔍 Testing complete write and storage flow...")

    # Initialize service
    memory_service = MultiScopeMemoryService()
    memory_service.set_project("test-project")
    memory_service.initialize()

    # Write an event with explicit debugging
    print("\n✍️ Writing event with debugging...")

    # Get the collection name first
    from autogen_mcp.collections import MemoryScope

    collection_name = memory_service.collection_manager.get_collection_name(
        MemoryScope.GLOBAL
    )
    print(f"Collection name: {collection_name}")

    # Test content
    test_content = "This is a debug test for vector storage"

    # Write the event
    event_id = memory_service.write_global(
        thread_id="debug-test-2025", text=test_content
    )
    print(f"✅ Wrote event: {event_id}")

    # Check collection state immediately after
    print("\n📊 Collection state after write:")
    try:
        result_after = memory_service.collection_manager.qdrant.scroll(
            collection=collection_name, limit=10, with_vector=True
        )
        points_after = result_after.get("result", {}).get("points", [])
        print(f"Events after: {len(points_after)}")

        # Find our specific event
        our_event = None
        for point in points_after:
            if point["id"] == event_id:
                our_event = point
                break

        if our_event:
            print(f"\n🔍 Found our event {event_id}:")
            print(f"  Has vector key: {'vector' in our_event}")
            if "vector" in our_event:
                vector = our_event["vector"]
                print(f"  Vector type: {type(vector)}")
                print(f"  Vector is None: {vector is None}")
                if vector is not None:
                    print(f"  Vector length: {len(vector)}")
                    if len(vector) > 0:
                        print(f"  Vector sample: {vector[:3]}")
                        print("  ✅ Vector stored successfully!")
                    else:
                        print("  ❌ Vector is empty list")
                else:
                    print("  ❌ Vector is None")
            else:
                print("  ❌ No vector key in response")

            payload = our_event.get("payload", {})
            print(f"  Payload content: {payload.get('content', 'missing')}")
        else:
            print(f"❌ Could not find event {event_id} in results")
            # Debug: Show all event IDs
            print("Available event IDs:")
            for i, point in enumerate(points_after[:5]):
                print(f"  {i+1}: {point['id']}")

    except Exception as e:
        print(f"❌ Error checking after: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_write_and_check()

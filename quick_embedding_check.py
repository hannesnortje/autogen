#!/usr/bin/env python3
"""
Simple debug script to check if stored events have embeddings.
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from autogen_mcp.multi_memory import MultiScopeMemoryService


def check_embeddings():
    """Check if stored events have embeddings."""
    print("🔍 Checking stored event embeddings...")

    # Initialize service
    memory_service = MultiScopeMemoryService()
    memory_service.set_project("test-project")
    memory_service.initialize()

    # Write a test event
    print("\n✍️ Writing test event...")
    event_id = memory_service.write_global(
        thread_id="embedding-test", text="Test event to check embedding generation"
    )
    print(f"Event ID: {event_id}")

    # Query the collection directly
    print("\n🔍 Querying collection for recent events...")
    collection_name = "autogen_global"

    # Use the correct QdrantWrapper method
    try:
        result = memory_service.collection_manager.qdrant.scroll(
            collection=collection_name, limit=5, with_payload=True
        )

        # Extract points from the result
        points = result.get("result", {}).get("points", [])

        print(f"Found {len(points)} events")

        for i, point in enumerate(points):
            print(f"\n--- Event {i+1} ---")
            print(f"ID: {point['id']}")

            vector = point.get("vector")
            print(f"Has vector: {vector is not None}")
            if vector:
                print(f"Vector length: {len(vector)}")
                if len(vector) > 0:
                    print(f"Vector[0:3]: {vector[:3]}")
                    print("✅ Vector has content!")
                else:
                    print("❌ Vector is empty list")
            else:
                print("❌ No vector found")

            payload = point.get("payload")
            if payload:
                content = payload.get("content", "No content")
                print(f"Content: {content[:50]}...")

    except Exception as e:
        print(f"❌ Error querying: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    check_embeddings()

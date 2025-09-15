#!/usr/bin/env python3
"""
Test the search functionality now that we know embeddings work.
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from autogen_mcp.multi_memory import MultiScopeMemoryService


def test_search():
    """Test search functionality with working embeddings."""
    print("🔍 Testing search with working embeddings...")

    # Initialize service
    memory_service = MultiScopeMemoryService()
    memory_service.set_project("test-project")
    memory_service.initialize()

    # Write some test events
    print("\n✍️ Writing test events...")

    # Write multiple events to search against
    events = [
        "Python best practices for code quality",
        "Database optimization techniques",
        "Machine learning model training",
        "Web security vulnerabilities",
        "API design patterns",
    ]

    event_ids = []
    for text in events:
        event_id = memory_service.write_global(thread_id="search-test", text=text)
        event_ids.append(event_id)
        print(f"  ✅ Wrote: {text} [{event_id}]")

    # Test search
    print("\n🔍 Testing search functionality...")

    # Test 1: Search for "Python"
    print("\n🧪 Test 1: Search for 'Python programming'")
    try:
        results = memory_service.search(
            query="Python programming", scope="global", limit=3
        )
        print(f"Search results: {len(results)} found")
        for i, result in enumerate(results):
            print(
                f"  {i+1}: {result.get('content', 'no content')} (score: {result.get('score', 'no score')})"
            )

        if len(results) > 0:
            print("✅ Search returned results!")
        else:
            print("❌ Search returned 0 results")

    except Exception as e:
        print(f"❌ Search error: {e}")
        import traceback

        traceback.print_exc()

    # Test 2: Search for "database"
    print("\n🧪 Test 2: Search for 'database performance'")
    try:
        results = memory_service.search(
            query="database performance", scope="global", limit=3
        )
        print(f"Search results: {len(results)} found")
        for i, result in enumerate(results):
            print(
                f"  {i+1}: {result.get('content', 'no content')} (score: {result.get('score', 'no score')})"
            )

    except Exception as e:
        print(f"❌ Search error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_search()

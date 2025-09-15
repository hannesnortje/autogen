#!/usr/bin/env python3
"""
Debug script to investigate the search issue.

This will help us understand exactly what's in the Qdrant collections
and why the search is returning 0 results.
"""

import asyncio

from autogen_mcp.collections import CollectionManager, MemoryScope
from autogen_mcp.hybrid_search_service import HybridSearchService
from autogen_mcp.multi_memory import MultiScopeMemoryService
from autogen_mcp.qdrant_client import QdrantWrapper


async def debug_search_issue():
    """Debug the memory search issue step by step."""
    print("🔍 Starting search issue debug...")

    # Initialize services
    print("\n1️⃣ Initializing services...")
    collection_manager = CollectionManager()
    memory_service = MultiScopeMemoryService(collection_manager)
    qdrant = QdrantWrapper()
    hybrid_search = HybridSearchService()

    # Check Qdrant health
    print(f"Qdrant health: {qdrant.health()}")

    # Initialize memory service
    print("\n2️⃣ Initializing memory service...")
    init_result = memory_service.initialize(["test_project"])
    print(f"Initialize result: {init_result['status']}")

    # Check collections
    print("\n3️⃣ Checking collections...")
    collections = qdrant.list_collections()
    print(f"Collections response type: {type(collections)}")
    print(f"Collections: {collections}")

    if isinstance(collections, dict):
        collection_list = collections.get("result", {}).get("collections", [])
    else:
        collection_list = collections

    collection_names = [
        c.get("name", "unknown") if isinstance(c, dict) else str(c)
        for c in collection_list
    ]
    print(f"Available collections: {collection_names}")

    # Check each collection content
    print("\n4️⃣ Examining collection contents...")
    for scope in MemoryScope:
        collection_name = collection_manager.get_collection_name(
            scope, "test_project" if scope == MemoryScope.PROJECT else None
        )
        print(f"\n--- {scope.value} ({collection_name}) ---")

        # Get points in collection
        scroll_result = qdrant.scroll(collection_name, limit=10, with_payload=True)
        points = scroll_result.get("result", {}).get("points", [])
        print(f"Points found: {len(points)}")

        for i, point in enumerate(points[:3]):  # Show first 3 points
            print(f"Point {i+1}:")
            print(f"  ID: {point.get('id')}")
            print(f"  Payload keys: {list(point.get('payload', {}).keys())}")
            print(f"  Payload scope: {point.get('payload', {}).get('scope')}")
            print(
                f"  Content preview: {point.get('payload', {}).get('content', '')[:100]}..."
            )
            print(f"  Vector length: {len(point.get('vector', []))}")

    # Test hybrid search as currently configured
    print("\n5️⃣ Testing current hybrid search...")
    test_query = "global knowledge"
    for scope in ["global", "project", "thread"]:
        print(f"\nTesting search in scope: {scope}")

        # Try to get collection name for this scope
        memory_scope = getattr(MemoryScope, scope.upper(), None)
        if not memory_scope:
            print(f"Invalid scope: {scope}")
            continue
        collection_name = collection_manager.get_collection_name(
            memory_scope,
            "test_project" if memory_scope == MemoryScope.PROJECT else None,
        )

        print(f"Collection name: {collection_name}")

        # Try the current search method
        results = hybrid_search.search(
            collection=collection_name, query=test_query, k=5, scopes=[scope]
        )
        print(f"Search results: {len(results)}")
        for result in results:
            print(f"  - {result}")

    # Test the _dense_search method directly
    print("\n6️⃣ Testing dense search directly...")
    collection_name = "autogen_global"
    dense_results = hybrid_search._dense_search(
        collection_name, test_query, 5, "global"
    )
    print(f"Dense search results: {len(dense_results)}")
    for result in dense_results:
        print(f"  - {result}")

    # Test raw Qdrant search
    print("\n7️⃣ Testing raw Qdrant search...")
    from autogen_mcp.embeddings import EmbeddingService

    embed_service = EmbeddingService()
    query_vector = embed_service.encode_one(test_query)

    # Direct vector search
    search_result = qdrant.search(collection_name, vector=query_vector, limit=5)
    print(f"Raw vector search: {search_result.get('status')}")
    raw_results = search_result.get("result", [])
    print(f"Raw results count: {len(raw_results)}")
    for result in raw_results[:2]:
        print(
            f"  - Score: {result.get('score')}, Payload keys: {list(result.get('payload', {}).keys())}"
        )

    print("\n✅ Debug completed!")


if __name__ == "__main__":
    asyncio.run(debug_search_issue())

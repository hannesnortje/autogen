#!/usr/bin/env python3
"""
Debug the HybridSearchService directly to see what's happening.
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from autogen_mcp.multi_memory import MultiScopeMemoryService
from autogen_mcp.collections import MemoryScope


def debug_hybrid_search():
    """Debug the hybrid search service behavior."""
    print("🔍 Debugging HybridSearchService...")

    # Initialize service
    memory_service = MultiScopeMemoryService()
    memory_service.set_project("test-project")
    memory_service.initialize()

    # Write a test event
    print("\n✍️ Writing test event...")
    test_content = "Python programming best practices"
    event_id = memory_service.write_global(thread_id="hybrid-test", text=test_content)
    print(f"✅ Wrote: {test_content} [{event_id}]")

    # Get collection name
    collection_name = memory_service.collection_manager.get_collection_name(
        MemoryScope.GLOBAL
    )
    print(f"Collection name: {collection_name}")

    # Test the HybridSearchService components directly
    hybrid_search = memory_service.hybrid_search

    print("\n🔧 HybridSearchService debug:")
    print(f"  Config: {hybrid_search.config}")
    print(f"  Embedding service: {hybrid_search.embed is not None}")
    print(f"  Qdrant client: {hybrid_search.qdrant is not None}")
    print(f"  Sparse retriever: {hybrid_search._sparse is not None}")

    # Test dense search component directly
    print("\n🧪 Testing dense search component...")
    try:
        query = "Python programming"
        dense_results = hybrid_search._dense_search(
            collection=collection_name, query=query, k=5, scope="global"
        )
        print(f"Dense search results: {len(dense_results)}")
        for i, result in enumerate(dense_results):
            print(f"  {i+1}: ID={result.get('id')}, Score={result.get('score'):.4f}")
            content = result.get("metadata", {}).get("content", "no content")
            print(f"      Content: {content}")

    except Exception as e:
        print(f"❌ Dense search error: {e}")
        import traceback

        traceback.print_exc()

    # Test sparse search component
    print("\n🧪 Testing sparse search component...")
    try:
        sparse_results = hybrid_search._sparse_search(query=query, k=5, scope="global")
        print(f"Sparse search results: {len(sparse_results)}")
        for i, result in enumerate(sparse_results):
            print(f"  {i+1}: ID={result.get('id')}, Score={result.get('score'):.4f}")

    except Exception as e:
        print(f"❌ Sparse search error: {e}")
        import traceback

        traceback.print_exc()

    # Test full hybrid search
    print("\n🧪 Testing full hybrid search...")
    try:
        full_results = hybrid_search.search(
            collection=collection_name, query=query, k=5, scopes=["global"]
        )
        print(f"Full hybrid search results: {len(full_results)}")
        for i, result in enumerate(full_results):
            print(f"  {i+1}: ID={result.get('id')}, Score={result.get('score'):.4f}")

    except Exception as e:
        print(f"❌ Full hybrid search error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    debug_hybrid_search()

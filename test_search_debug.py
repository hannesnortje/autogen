#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from autogen_ui.services.memory_service import MemoryService

async def test_search():
    """Test search functionality in different collections"""
    
    print("🔍 Testing Search Functionality")
    print("=" * 50)
    
    # Initialize memory service
    service = MemoryService()
    await service.initialize(local_mode=True)
    
    # Get collections first
    collections = await service.get_collections()
    print(f"✅ Found {len(collections)} collections:")
    for collection in collections:
        name = collection["name"]
        docs = collection["documents"]
        print(f"   - {name}: {docs} documents")
    
    # Test searches in different collections
    test_queries = ["python", "code", "api", "test", "function"]
    test_collections = ["autogen_project_default", "autogen_global", "autogen_thread"]
    
    for collection in test_collections:
        if any(c["name"] == collection for c in collections):
            print(f"\n🔍 Testing searches in '{collection}':")
            for query in test_queries:
                try:
                    results = await service.search_memory(query, collection, limit=5)
                    print(f"   '{query}': {len(results)} results")
                    if results:
                        sample = results[0]
                        content = sample.get('content', '')[:100]
                        score = sample.get('score', 0)
                        print(f"     Sample (score {score:.3f}): {content}...")
                        break  # Found results, move to next collection
                except Exception as e:
                    print(f"   '{query}': ERROR - {e}")
        else:
            print(f"\n❌ Collection '{collection}' not found")

if __name__ == "__main__":
    asyncio.run(test_search())
#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from autogen_ui.services.memory_service import MemoryService

async def test_collections():
    """Test that the memory service can see all collections including project ones"""
    
    print("🔍 Testing Collection Discovery")
    print("=" * 50)
    
    # Initialize memory service
    service = MemoryService()
    await service.initialize(local_mode=True)
    
    # Get collections
    try:
        collections = await service.get_collections()
        print(f"✅ Found {len(collections)} collections:")
        
        project_collections = []
        for collection in collections:
            name = collection["name"]
            print(f"   - {name}")
            if name.startswith("autogen_project"):
                project_collections.append(name)
        
        print(f"\n📁 Project collections found: {len(project_collections)}")
        for proj_coll in project_collections:
            print(f"   - {proj_coll}")
            
        if "autogen_project_default" in project_collections:
            print("✅ Your 'autogen_project_default' collection is visible!")
            
            # Test search in this collection
            print(f"\n🔍 Testing search in 'autogen_project_default'...")
            results = await service.search_memory("test", "autogen_project_default")
            print(f"✅ Search returned {len(results)} results")
            
            if results:
                print("Sample result:")
                sample = results[0]
                print(f"   - ID: {sample.get('id', 'N/A')}")
                print(f"   - Score: {sample.get('score', 'N/A')}")
                print(f"   - Content: {sample.get('content', 'N/A')[:100]}...")
        else:
            print("❌ 'autogen_project_default' collection not found in results")
            
    except Exception as e:
        print(f"❌ Error getting collections: {e}")

if __name__ == "__main__":
    asyncio.run(test_collections())
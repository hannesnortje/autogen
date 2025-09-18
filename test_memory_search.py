#!/usr/bin/env python3
"""
Test script for PySide6 UI memory search functionality
"""

import sys
import asyncio
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from autogen_ui.services.memory_service import MemoryService  # noqa: E402


async def test_memory_service():
    """Test the memory service functionality"""
    print("🧪 Testing Memory Service")
    print("=" * 50)
    
    # Initialize memory service
    memory_service = MemoryService()
    
    # Test local mode initialization
    print("1. Testing local mode initialization...")
    try:
        await memory_service.initialize(local_mode=True)
        print("   ✅ Local mode initialization successful")
    except Exception as e:
        print(f"   ❌ Local mode initialization failed: {e}")
        return False
    
    # Test get collections
    print("2. Testing collections retrieval...")
    try:
        collections = await memory_service.get_collections()
        print(f"   ✅ Found {len(collections)} collections:")
        for collection in collections:
            name = collection.get('name', 'unknown')
            docs = collection.get('documents', 0)
            print(f"      - {name}: {docs} documents")
    except Exception as e:
        print(f"   ❌ Collections retrieval failed: {e}")
        return False
    
    # Test get stats
    print("3. Testing stats retrieval...")
    try:
        stats = await memory_service.get_stats()
        print("   ✅ Stats retrieved:")
        for key, value in stats.items():
            print(f"      - {key}: {value}")
    except Exception as e:
        print(f"   ❌ Stats retrieval failed: {e}")
        return False
    
    # Test search (should work even with empty collections)
    print("4. Testing memory search...")
    try:
        results = await memory_service.search_memory(
            query="python programming",
            scope="global",
            limit=5
        )
        print(f"   ✅ Search completed with {len(results)} results")
        if results:
            print("   Sample result:")
            result = results[0]
            print(f"      - ID: {result.get('id')}")
            print(f"      - Score: {result.get('score')}")
            content = result.get('payload', {}).get('content', '')
            if len(content) > 100:
                content = content[:100] + "..."
            print(f"      - Content: {content}")
    except Exception as e:
        print(f"   ❌ Search failed: {e}")
        return False
    
    print("\n🎉 All tests passed! Memory service is working correctly.")
    return True


async def main():
    """Main test function"""
    try:
        success = await test_memory_service()
        return 0 if success else 1
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

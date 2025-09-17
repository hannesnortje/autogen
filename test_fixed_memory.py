#!/usr/bin/env python3
"""Test the fixed memory integration"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


async def test_fixed_memory():
    """Test the fixed memory service integration"""
    print("🔧 Testing Fixed Memory Integration")
    print("=" * 50)

    try:
        from autogen_ui.services import (
            MemoryService,
            IntegrationConfig,
            IntegrationMode,
        )

        # Test direct mode with all fixes
        config = IntegrationConfig(
            mode=IntegrationMode.DIRECT,
            mcp_server_url="http://localhost:9000",
            timeout=10,
        )

        print("📡 Creating memory service...")
        memory_service = MemoryService(config)

        print("🚀 Initializing memory service...")
        success = await memory_service.initialize()
        print(f"   → Initialization: {'✅ SUCCESS' if success else '❌ FAILED'}")

        if success:
            print("🔍 Testing memory search...")
            try:
                results = await memory_service.search_memory(
                    query="test", scope="global", k=3, threshold=0.0
                )
                print(f"   → Search results: {len(results)} entries found")

                if results:
                    for i, result in enumerate(results[:2]):
                        content = str(result.get("content", ""))[:60]
                        score = result.get("score", 0)
                        print(f"   → Result {i + 1}: {content}... (score: {score:.3f})")

            except Exception as e:
                print(f"❌ Search failed: {e}")

            print("📊 Testing memory stats...")
            try:
                stats = await memory_service.get_memory_stats()
                print(f"   → Total entries: {stats.get('total_entries', 'N/A')}")
                print(f"   → Health score: {stats.get('health_score', 'N/A')}")

            except Exception as e:
                print(f"❌ Stats failed: {e}")

            print("🏥 Testing health check...")
            try:
                health = await memory_service.get_memory_health()
                print(f"   → Health status: {health.get('status', 'N/A')}")
                print(f"   → Connection: {health.get('connection', 'N/A')}")

            except Exception as e:
                print(f"❌ Health check failed: {e}")

        await memory_service.close()
        print("✅ Fixed memory integration test completed!")
        return success

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_fixed_memory())
    if result:
        print("\n🎉 All tests passed! Ready to launch UI.")
    else:
        print("\n🔧 Issues detected. Check logs above.")

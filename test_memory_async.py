#!/usr/bin/env python3
"""Simple async test for memory service"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


async def test_memory_service():
    try:
        from autogen_ui.services import (
            MemoryService,
            IntegrationConfig,
            IntegrationMode,
        )

        # Use HTTP mode to avoid direct integration issues
        config = IntegrationConfig(
            mode=IntegrationMode.HTTP,
            mcp_server_url="http://localhost:9000",
            timeout=10,
        )

        memory_service = MemoryService(config)

        print("📡 Initializing memory service...")
        await memory_service.initialize()
        print("✅ Memory service initialized")

        print("🔍 Testing memory search...")
        results = await memory_service.search_memory(
            query="test", scope="global", k=3, threshold=0.0
        )
        print(f"✅ Search completed: {len(results)} results")

        for i, result in enumerate(results[:2]):
            content = str(result.get("content", ""))[:50]
            print(
                f"   Result {i + 1}: {content}... (score: {result.get('score', 0):.3f})"
            )

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_memory_service())

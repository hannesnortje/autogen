#!/usr/bin/env python3
"""
Debug the actual embedding generation process.
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from autogen_mcp.multi_memory import MultiScopeMemoryService, MemoryWriteOptions
from autogen_mcp.collections import MemoryScope


def debug_vector_generation():
    """Debug the vector generation step by step."""
    print("🔍 Debugging vector generation...")

    # Initialize service
    memory_service = MultiScopeMemoryService()
    memory_service.set_project("test-project")
    memory_service.initialize()

    # Test the embedding service directly
    print("\n🧪 Testing EmbeddingService directly...")
    test_text = "This is a test for embedding generation"
    embedding = memory_service.embedding_service.encode_one(test_text)
    print("Direct embedding test:")
    print(f"  Text: {test_text}")
    print(f"  Embedding type: {type(embedding)}")
    print(f"  Embedding length: {len(embedding) if embedding else 0}")
    if embedding and len(embedding) > 0:
        print(f"  Embedding sample: {embedding[:3]}")
        print("✅ EmbeddingService works!")
    else:
        print("❌ EmbeddingService failed!")
        return

    # Test MemoryWriteOptions default
    print("\n🧪 Testing MemoryWriteOptions...")
    options = MemoryWriteOptions(scope=MemoryScope.GLOBAL, thread_id="debug-test")
    print(f"Default auto_embed: {options.auto_embed}")

    # Now let's manually walk through the write_event process
    print("\n🧪 Manual write_event process...")

    # Step 1: Create event
    from autogen_mcp.collections import MemoryEvent

    event = MemoryEvent(content=test_text, scope=options.scope, metadata={})
    print("Created event:")
    print(f"  Content: {event.content}")
    print(f"  Scope: {event.scope}")
    print(f"  Initial vector: {event.vector}")

    # Step 2: Check auto_embed condition
    print(f"\nChecking auto_embed condition: {options.auto_embed}")
    if options.auto_embed:
        print("✅ auto_embed is True - generating embedding...")
        event.vector = memory_service.embedding_service.encode_one(event.content)
        print("Generated vector:")
        print(f"  Type: {type(event.vector)}")
        print(f"  Length: {len(event.vector) if event.vector else 0}")
        if event.vector and len(event.vector) > 0:
            print(f"  Sample: {event.vector[:3]}")
            print("✅ Vector generated successfully!")
        else:
            print("❌ Vector generation failed!")
    else:
        print("❌ auto_embed is False!")

    # Let's also check what gets passed to upsert_point
    print(
        f"\nVector to be stored: {event.vector is not None and len(event.vector) > 0}"
    )


if __name__ == "__main__":
    debug_vector_generation()

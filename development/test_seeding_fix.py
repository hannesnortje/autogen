#!/usr/bin/env python3
"""
Test script to verify the global collection seeding fix works correctly
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def test_seeding_deduplication():
    """Test that seeding doesn't create duplicates"""

    print("🧪 Testing Global Collection Seeding Fix")
    print("=" * 50)

    try:
        from autogen_mcp.memory_collections import CollectionManager, MemoryScope
        from autogen_mcp.knowledge_seeder import KnowledgeSeeder
        from autogen_mcp.multi_memory import MultiScopeMemoryService

        print("✅ Imports successful")

        # Create collection manager
        collection_manager = CollectionManager()

        # Create knowledge seeder
        seeder = KnowledgeSeeder(collection_manager)

        # Get initial collection count
        try:
            collection_name = collection_manager.get_collection_name(MemoryScope.GLOBAL)
            initial_info = collection_manager.client.get_collection_info(
                collection_name
            )
            initial_count = initial_info.get("points_count", 0)
            print(f"📊 Initial global collection count: {initial_count}")
        except Exception as e:
            print(f"⚠️  Could not get initial count: {e}")
            initial_count = 0

        # Test first seeding
        print("\n🌱 Testing first seeding...")
        result1 = seeder.seed_global_knowledge()
        print(f"   Status: {result1.get('status', 'unknown')}")
        print(
            f"   Seeded: {result1.get('seeded_count', 0)}/{result1.get('total_items', 0)} items"
        )
        if result1.get("errors"):
            print(f"   Errors: {len(result1['errors'])}")

        # Get count after first seeding
        try:
            after_first_info = collection_manager.client.get_collection_info(
                collection_name
            )
            after_first_count = after_first_info.get("points_count", 0)
            print(f"📊 After first seeding: {after_first_count} documents")
            first_seeding_added = after_first_count - initial_count
            print(f"   Added: {first_seeding_added} documents")
        except Exception as e:
            print(f"⚠️  Could not get count after first seeding: {e}")
            after_first_count = initial_count

        # Test second seeding (should be skipped)
        print("\n🔄 Testing second seeding (should be skipped)...")
        result2 = seeder.seed_global_knowledge()
        print(f"   Status: {result2.get('status', 'unknown')}")
        print(f"   Reason: {result2.get('reason', 'unknown')}")
        print(
            f"   Seeded: {result2.get('seeded_count', 0)}/{result2.get('total_items', 0)} items"
        )

        # Get count after second seeding
        try:
            after_second_info = collection_manager.client.get_collection_info(
                collection_name
            )
            after_second_count = after_second_info.get("points_count", 0)
            print(f"📊 After second seeding: {after_second_count} documents")
            second_seeding_added = after_second_count - after_first_count
            print(f"   Added: {second_seeding_added} documents")
        except Exception as e:
            print(f"⚠️  Could not get count after second seeding: {e}")
            after_second_count = after_first_count
            second_seeding_added = 0

        # Test MultiScopeMemoryService initialization (should also skip seeding)
        print("\n🏗️  Testing MultiScopeMemoryService initialization...")
        memory_service = MultiScopeMemoryService(collection_manager)
        init_result = memory_service.initialize()
        print(f"   Status: {init_result.get('status', 'unknown')}")
        if "seeding" in init_result:
            seeding = init_result["seeding"]
            print(f"   Seeding status: {seeding.get('status', 'unknown')}")
            if seeding.get("reason"):
                print(f"   Seeding reason: {seeding['reason']}")

        # Get final count
        try:
            final_info = collection_manager.client.get_collection_info(collection_name)
            final_count = final_info.get("points_count", 0)
            print(f"📊 Final count: {final_count} documents")
            service_init_added = final_count - after_second_count
            print(f"   Added by service init: {service_init_added} documents")
        except Exception as e:
            print(f"⚠️  Could not get final count: {e}")
            service_init_added = 0

        print("\n" + "=" * 50)
        print("📊 SUMMARY:")
        print(f"   Initial documents: {initial_count}")
        print(f"   After first seeding: {after_first_count} (+{first_seeding_added})")
        print(
            f"   After second seeding: {after_second_count} (+{second_seeding_added})"
        )
        print(f"   After service init: {final_count} (+{service_init_added})")

        # Verify the fix works
        success = True
        if result2.get("status") != "skipped":
            print("❌ FAIL: Second seeding should have been skipped")
            success = False

        if second_seeding_added > 0:
            print("❌ FAIL: Second seeding should not have added documents")
            success = False

        if service_init_added > 0:
            print("❌ FAIL: Service initialization should not have added documents")
            success = False

        if success:
            print("✅ SUCCESS: Deduplication is working correctly!")
            print("   - First seeding populated the collection")
            print("   - Subsequent seedings were skipped")
            print("   - No duplicate documents were created")

        return success

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_seeding_deduplication()
    sys.exit(0 if success else 1)

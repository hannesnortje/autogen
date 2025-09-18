#!/usr/bin/env python3
"""
Test script for agent persistence functionality
Tests the complete agent lifecycle: create, save, load, delete
"""

import sys
from pathlib import Path

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from autogen_ui.config import (
    load_custom_agents,
    save_custom_agent,
    delete_custom_agent,
    load_config,
)


def test_agent_persistence():
    """Test the complete agent persistence lifecycle"""
    print("🧪 Testing Agent Persistence System")
    print("=" * 50)

    # Test 1: Load initial state
    print("\n1. Loading initial custom agents...")
    initial_agents = load_custom_agents()
    print(f"   Found {len(initial_agents)} existing agents")

    # Test 2: Create and save a test agent
    print("\n2. Creating test agent...")
    test_agent = {
        "name": "Test Agent Persistence",
        "description": "A test agent for validating persistence functionality",
        "role": "tester",
        "capabilities": {
            "code_execution": True,
            "function_calling": False,
            "human_input": True,
            "web_browsing": False,
            "file_operations": True,
        },
        "model": {
            "name": "gemini-2.0-flash",
            "temperature": 0.5,
            "max_tokens": 2048,
            "system_prompt": "You are a test agent for validation purposes.",
        },
        "memory": {
            "enabled": True,
            "scope": "conversation",
            "retrieval_limit": 10,
        },
    }

    print("   Saving test agent...")
    try:
        save_custom_agent(test_agent)
        print("   ✅ Agent saved successfully")
    except Exception as e:
        print(f"   ❌ Failed to save agent: {e}")
        return False

    # Test 3: Verify agent was saved
    print("\n3. Verifying agent was saved...")
    agents_after_save = load_custom_agents()
    saved_agent = None

    for agent in agents_after_save:
        if agent.get("name") == test_agent["name"]:
            saved_agent = agent
            break

    if saved_agent:
        print("   ✅ Agent found in storage")
        print(f"   Agent details: {saved_agent['name']} ({saved_agent['role']})")
    else:
        print("   ❌ Agent not found after saving")
        return False

    # Test 4: Update existing agent
    print("\n4. Testing agent update...")
    test_agent["description"] = "Updated description for testing"
    test_agent["model"]["temperature"] = 0.7

    try:
        save_custom_agent(test_agent)
        print("   ✅ Agent updated successfully")
    except Exception as e:
        print(f"   ❌ Failed to update agent: {e}")
        return False

    # Test 5: Verify update
    print("\n5. Verifying agent update...")
    agents_after_update = load_custom_agents()
    updated_agent = None

    for agent in agents_after_update:
        if agent.get("name") == test_agent["name"]:
            updated_agent = agent
            break

    if (
        updated_agent
        and updated_agent["description"] == "Updated description for testing"
    ):
        print("   ✅ Agent updated correctly")
    else:
        print("   ❌ Agent update failed")
        return False

    # Test 6: Test duplicate name handling
    print("\n6. Testing duplicate agent creation...")
    duplicate_agent = {
        "name": "Test Agent Persistence",  # Same name
        "description": "This should replace the first one",
        "role": "duplicate-tester",
        "capabilities": {"code_execution": False},
        "model": {
            "name": "gpt-4",
            "temperature": 0.1,
            "system_prompt": "Duplicate test",
        },
        "memory": {"enabled": False},
    }

    try:
        save_custom_agent(duplicate_agent)

        # Verify only one agent with this name exists
        final_agents = load_custom_agents()
        matching_agents = [
            a for a in final_agents if a.get("name") == test_agent["name"]
        ]

        if (
            len(matching_agents) == 1
            and matching_agents[0]["role"] == "duplicate-tester"
        ):
            print("   ✅ Duplicate name handling works (replaced existing agent)")
        else:
            print(
                f"   ❌ Duplicate handling failed: found {len(matching_agents)} matching agents"
            )
            return False
    except Exception as e:
        print(f"   ❌ Duplicate test failed: {e}")
        return False

    # Test 7: Delete agent
    print("\n7. Testing agent deletion...")
    try:
        deleted = delete_custom_agent("Test Agent Persistence")
        if deleted:
            print("   ✅ Agent deleted successfully")
        else:
            print("   ❌ Agent deletion reported failure")
            return False
    except Exception as e:
        print(f"   ❌ Failed to delete agent: {e}")
        return False

    # Test 8: Verify deletion
    print("\n8. Verifying agent deletion...")
    final_agents = load_custom_agents()
    deleted_agent = None

    for agent in final_agents:
        if agent.get("name") == "Test Agent Persistence":
            deleted_agent = agent
            break

    if deleted_agent is None:
        print("   ✅ Agent successfully removed from storage")
    else:
        print("   ❌ Agent still exists after deletion")
        return False

    # Test 9: Test configuration file integrity
    print("\n9. Testing configuration file integrity...")
    try:
        config = load_config()
        if "agents" in config and "custom_agents" in config["agents"]:
            print("   ✅ Configuration structure is valid")
            print(f"   Current agent count: {len(config['agents']['custom_agents'])}")
        else:
            print("   ❌ Configuration structure is invalid")
            return False
    except Exception as e:
        print(f"   ❌ Configuration test failed: {e}")
        return False

    print("\n" + "=" * 50)
    print("🎉 All tests passed! Agent persistence system is working correctly.")
    return True


def display_current_config():
    """Display current configuration for debugging"""
    print("\n📊 Current Configuration State:")
    print("-" * 30)

    try:
        config = load_config()
        agents = config.get("agents", {}).get("custom_agents", [])

        if agents:
            print(f"Custom agents ({len(agents)}):")
            for i, agent in enumerate(agents, 1):
                name = agent.get("name", "Unnamed")
                role = agent.get("role", "unknown")
                print(f"  {i}. {name} ({role})")
        else:
            print("No custom agents stored.")

        # Show config file location
        config_path = Path(__file__).parent / "autogen.config.json"
        print(f"\nConfig file: {config_path}")
        print(f"Config exists: {config_path.exists()}")

    except Exception as e:
        print(f"Error reading configuration: {e}")


if __name__ == "__main__":
    print("AutoGen Agent Persistence Test Suite")
    print("This will test all agent management functionality\n")

    # Show current state
    display_current_config()

    # Run tests
    success = test_agent_persistence()

    # Show final state
    display_current_config()

    # Exit with appropriate code
    sys.exit(0 if success else 1)

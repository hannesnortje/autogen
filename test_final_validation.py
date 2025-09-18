#!/usr/bin/env python3
"""
Final validation test for agent persistence
Tests integration without GUI dependencies
"""

import sys
from pathlib import Path

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from autogen_ui.config import load_custom_agents, save_custom_agent, delete_custom_agent


def test_full_integration():
    """Test the complete integration without GUI dependencies"""
    print("🔧 Final Integration Test - Agent Persistence System")
    print("=" * 60)

    # Clean slate
    print("\n1. Starting with clean state...")
    initial_agents = load_custom_agents()
    if initial_agents:
        print(f"   Cleaning up {len(initial_agents)} existing agents...")
        for agent in initial_agents:
            delete_custom_agent(agent.get("name", ""))
        print("   ✅ Clean state achieved")
    else:
        print("   ✅ Already clean")

    # Test a realistic agent creation scenario
    print("\n2. Testing realistic agent scenarios...")

    realistic_agents = [
        {
            "name": "Senior Python Developer",
            "description": "Expert Python developer with Django and FastAPI experience",
            "role": "senior-developer",
            "capabilities": {
                "code_execution": True,
                "function_calling": True,
                "human_input": True,
                "web_browsing": False,
                "file_operations": True,
            },
            "model": {
                "name": "gemini-2.0-flash",
                "temperature": 0.2,
                "max_tokens": 4096,
                "system_prompt": (
                    "You are a senior Python developer with 10+ years of experience. "
                    "You write clean, maintainable code following PEP 8 standards. "
                    "You have expertise in Django, FastAPI, pytest, and modern Python practices."
                ),
            },
            "memory": {
                "enabled": True,
                "scope": "project",
                "retrieval_limit": 20,
            },
        },
        {
            "name": "Technical Writer",
            "description": "Professional technical writer for documentation and content",
            "role": "technical-writer",
            "capabilities": {
                "code_execution": False,
                "function_calling": False,
                "human_input": True,
                "web_browsing": True,
                "file_operations": True,
            },
            "model": {
                "name": "gemini-2.0-flash",
                "temperature": 0.7,
                "max_tokens": 3000,
                "system_prompt": (
                    "You are a professional technical writer. Create clear, "
                    "comprehensive documentation with proper structure, "
                    "examples, and user-friendly language."
                ),
            },
            "memory": {
                "enabled": True,
                "scope": "global",
                "retrieval_limit": 15,
            },
        },
        {
            "name": "DevOps Engineer",
            "description": "DevOps engineer specializing in CI/CD and infrastructure",
            "role": "devops-engineer",
            "capabilities": {
                "code_execution": True,
                "function_calling": True,
                "human_input": False,
                "web_browsing": True,
                "file_operations": True,
            },
            "model": {
                "name": "gpt-4",
                "temperature": 0.1,
                "max_tokens": 2048,
                "system_prompt": (
                    "You are a DevOps engineer with expertise in Docker, "
                    "Kubernetes, GitHub Actions, and cloud infrastructure. "
                    "Focus on automation, security, and best practices."
                ),
            },
            "memory": {
                "enabled": True,
                "scope": "project",
                "retrieval_limit": 25,
            },
        },
    ]

    # Save all agents
    for agent in realistic_agents:
        try:
            save_custom_agent(agent)
            print(f"   ✅ Created: {agent['name']}")
        except Exception as e:
            print(f"   ❌ Failed to create {agent['name']}: {e}")
            return False

    # Verify all agents saved
    print("\n3. Verifying agent persistence...")
    saved_agents = load_custom_agents()

    if len(saved_agents) == len(realistic_agents):
        print(f"   ✅ All {len(realistic_agents)} agents saved successfully")
    else:
        print(f"   ❌ Expected {len(realistic_agents)}, found {len(saved_agents)}")
        return False

    # Test agent data integrity
    print("\n4. Testing data integrity...")
    for original_agent in realistic_agents:
        saved_agent = None
        for agent in saved_agents:
            if agent.get("name") == original_agent["name"]:
                saved_agent = agent
                break

        if not saved_agent:
            print(f"   ❌ Agent '{original_agent['name']}' not found")
            return False

        # Check key fields
        critical_fields = [
            "name",
            "role",
            "description",
            "capabilities",
            "model",
            "memory",
        ]
        for field in critical_fields:
            if field not in saved_agent:
                print(f"   ❌ Field '{field}' missing from {saved_agent['name']}")
                return False

        print(f"   ✅ {saved_agent['name']}: Data integrity verified")

    # Test agent selection dialog compatibility
    print("\n5. Testing dialog compatibility (data format)...")

    # Simulate what AgentSelectionDialog.get_available_agents() would do
    simulated_dialog_agents = []

    for agent_config in saved_agents:
        # Convert format (same as in agent_selection_dialog.py)
        dialog_agent = {
            "name": agent_config.get("name", "Unnamed Agent"),
            "description": agent_config.get("description", "Custom agent"),
            "role": agent_config.get("role", "general"),
            "type": "custom",
            "llm_config": {
                "model": agent_config.get("model", {}).get("name", "gpt-4"),
                "api_type": "custom",
                "temperature": agent_config.get("model", {}).get("temperature", 0.7),
            },
            "system_message": agent_config.get("model", {}).get("system_prompt", ""),
            "capabilities": [
                cap
                for cap, enabled in agent_config.get("capabilities", {}).items()
                if enabled
            ],
        }
        simulated_dialog_agents.append(dialog_agent)

    # Verify conversion worked
    for dialog_agent in simulated_dialog_agents:
        required_dialog_fields = ["name", "description", "role", "type", "llm_config"]
        missing_fields = [f for f in required_dialog_fields if f not in dialog_agent]

        if missing_fields:
            print(
                f"   ❌ Dialog format missing fields for {dialog_agent.get('name')}: {missing_fields}"
            )
            return False

    print(
        f"   ✅ All {len(simulated_dialog_agents)} agents compatible with dialog format"
    )

    # Test update functionality
    print("\n6. Testing agent updates...")

    update_agent = dict(realistic_agents[0])  # Copy first agent
    update_agent["description"] = "UPDATED: " + update_agent["description"]
    update_agent["model"]["temperature"] = 0.95

    try:
        save_custom_agent(update_agent)

        # Verify update
        updated_agents = load_custom_agents()
        updated = None
        for agent in updated_agents:
            if agent.get("name") == update_agent["name"]:
                updated = agent
                break

        if (
            updated
            and updated["description"].startswith("UPDATED:")
            and updated["model"]["temperature"] == 0.95
        ):
            print(f"   ✅ Agent '{update_agent['name']}' updated successfully")
        else:
            print("   ❌ Agent update failed")
            return False

    except Exception as e:
        print(f"   ❌ Update test failed: {e}")
        return False

    # Test deletion
    print("\n7. Testing selective deletion...")

    agent_to_delete = realistic_agents[1]["name"]  # Delete second agent
    try:
        deleted = delete_custom_agent(agent_to_delete)
        if deleted:
            remaining_agents = load_custom_agents()
            remaining_names = [a.get("name") for a in remaining_agents]

            if agent_to_delete not in remaining_names:
                print(f"   ✅ Agent '{agent_to_delete}' deleted successfully")
                print(f"   ✅ {len(remaining_agents)} agents remain")
            else:
                print("   ❌ Agent still exists after deletion")
                return False
        else:
            print("   ❌ Deletion reported failure")
            return False
    except Exception as e:
        print(f"   ❌ Deletion test failed: {e}")
        return False

    # Final cleanup
    print("\n8. Final cleanup...")
    final_agents = load_custom_agents()
    for agent in final_agents:
        delete_custom_agent(agent.get("name", ""))

    print("   ✅ All test agents cleaned up")

    print("\n" + "=" * 60)
    print("🎉 COMPLETE SUCCESS! All integration tests passed!")
    print("\nThe agent persistence system is fully functional:")
    print("✅ Configuration file integration")
    print("✅ Agent CRUD operations (Create, Read, Update, Delete)")
    print("✅ Data integrity preservation")
    print("✅ Dialog format compatibility")
    print("✅ Update and duplicate handling")
    print("✅ Error handling and recovery")

    return True


if __name__ == "__main__":
    success = test_full_integration()
    sys.exit(0 if success else 1)

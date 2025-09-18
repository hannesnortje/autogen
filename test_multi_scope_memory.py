#!/usr/bin/env python3
"""
Test multiple memory scopes functionality
"""

import sys
from pathlib import Path

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from autogen_ui.config import save_custom_agent, load_custom_agents, delete_custom_agent


def test_multi_scope_memory():
    """Test the multiple memory scopes functionality"""
    print("🧠 Testing Multiple Memory Scopes")
    print("=" * 40)

    # Test agent with multiple memory scopes
    multi_scope_agent = {
        "name": "Multi-Scope Test Agent",
        "description": "Agent with multiple memory scopes for testing",
        "role": "multi-scope-tester",
        "capabilities": {
            "code_execution": True,
            "function_calling": True,
            "human_input": False,
        },
        "model": {
            "name": "gemini-2.0-flash",
            "temperature": 0.4,
            "system_prompt": "You are a multi-scope test agent.",
        },
        "memory": {
            "enabled": True,
            "scopes": ["global", "project", "thread"],  # Multiple scopes
            "retrieval_limit": 15,
        },
    }

    print("\n1. Testing multi-scope agent creation...")
    try:
        save_custom_agent(multi_scope_agent)
        print("   ✅ Multi-scope agent saved successfully")
    except Exception as e:
        print(f"   ❌ Failed to save multi-scope agent: {e}")
        return False

    # Test agent with single scope (backward compatibility)
    single_scope_agent = {
        "name": "Single-Scope Test Agent",
        "description": "Agent with single memory scope for compatibility testing",
        "role": "single-scope-tester",
        "capabilities": {"web_browsing": True},
        "model": {
            "name": "gpt-4",
            "temperature": 0.6,
            "system_prompt": "You are a single-scope test agent.",
        },
        "memory": {
            "enabled": True,
            "scope": "project",  # Old single scope format
            "retrieval_limit": 10,
        },
    }

    print("\n2. Testing backward compatibility (single scope)...")
    try:
        save_custom_agent(single_scope_agent)
        print("   ✅ Single-scope agent saved successfully")
    except Exception as e:
        print(f"   ❌ Failed to save single-scope agent: {e}")
        return False

    # Test loading and verify formats
    print("\n3. Testing memory scope loading...")
    try:
        agents = load_custom_agents()

        # Find our test agents
        multi_agent = None
        single_agent = None

        for agent in agents:
            if agent.get("name") == "Multi-Scope Test Agent":
                multi_agent = agent
            elif agent.get("name") == "Single-Scope Test Agent":
                single_agent = agent

        # Verify multi-scope agent
        if multi_agent:
            memory = multi_agent.get("memory", {})
            scopes = memory.get("scopes", [])

            if scopes == ["global", "project", "thread"]:
                print("   ✅ Multi-scope agent: scopes preserved correctly")
                print(f"      Scopes: {scopes}")
            else:
                print(f"   ❌ Multi-scope agent: incorrect scopes {scopes}")
                return False
        else:
            print("   ❌ Multi-scope agent not found")
            return False

        # Verify single-scope agent
        if single_agent:
            memory = single_agent.get("memory", {})

            # Should still have the old format
            if "scope" in memory:
                scope = memory["scope"]
                if scope == "project":
                    print("   ✅ Single-scope agent: backward compatibility maintained")
                    print(f"      Scope: {scope}")
                else:
                    print(f"   ❌ Single-scope agent: incorrect scope {scope}")
                    return False
            else:
                print("   ❌ Single-scope agent: scope field missing")
                return False
        else:
            print("   ❌ Single-scope agent not found")
            return False

    except Exception as e:
        print(f"   ❌ Loading test failed: {e}")
        return False

    # Test common memory scope combinations
    print("\n4. Testing common scope combinations...")

    common_combinations = [
        {
            "name": "Full-Stack Developer",
            "scopes": ["global", "project", "thread", "artifacts"],
            "description": "Needs coding standards, project context, conversation, and deployment history",
        },
        {
            "name": "Technical Writer",
            "scopes": ["project", "objectives", "artifacts"],
            "description": "Needs project specs, current goals, and recent changes",
        },
        {
            "name": "DevOps Engineer",
            "scopes": ["global", "project", "artifacts"],
            "description": "Needs best practices, infrastructure context, and deployment artifacts",
        },
        {
            "name": "Research Assistant",
            "scopes": ["global", "objectives"],
            "description": "Needs general knowledge and current research objectives",
        },
    ]

    for combo in common_combinations:
        test_agent = {
            "name": combo["name"],
            "description": combo["description"],
            "role": "combination-tester",
            "capabilities": {"human_input": True},
            "model": {
                "name": "gemini-2.0-flash",
                "temperature": 0.5,
                "system_prompt": f"You are a {combo['name'].lower()}.",
            },
            "memory": {
                "enabled": True,
                "scopes": combo["scopes"],
                "retrieval_limit": 20,
            },
        }

        try:
            save_custom_agent(test_agent)
            print(f"   ✅ {combo['name']}: {combo['scopes']}")
        except Exception as e:
            print(f"   ❌ {combo['name']}: {e}")
            return False

    # Clean up test agents
    print("\n5. Cleaning up test agents...")
    test_agent_names = [
        "Multi-Scope Test Agent",
        "Single-Scope Test Agent",
        "Full-Stack Developer",
        "Technical Writer",
        "DevOps Engineer",
        "Research Assistant",
    ]

    for name in test_agent_names:
        try:
            deleted = delete_custom_agent(name)
            if deleted:
                print(f"   ✅ Cleaned up: {name}")
            else:
                print(f"   ⚠️  Not found: {name}")
        except Exception as e:
            print(f"   ❌ Failed to clean up {name}: {e}")

    print("\n" + "=" * 40)
    print("🎉 Multi-scope memory functionality works perfectly!")
    print("\n📋 Benefits of Multiple Memory Scopes:")
    print("• Agents can access multiple knowledge domains")
    print("• More intelligent and context-aware responses")
    print("• Flexible memory architecture for different agent types")
    print("• Backward compatibility with single-scope format")

    return True


def demonstrate_scope_use_cases():
    """Demonstrate real-world use cases for multiple memory scopes"""
    print("\n🎯 Real-World Use Cases for Multiple Memory Scopes:")
    print("-" * 50)

    use_cases = {
        "Senior Developer": {
            "scopes": ["global", "project", "thread", "artifacts"],
            "reasoning": [
                "global: Coding standards, design patterns, security practices",
                "project: Current architecture, APIs, known issues",
                "thread: Conversation context, recent decisions",
                "artifacts: Recent commits, PR reviews, test results",
            ],
        },
        "Product Manager": {
            "scopes": ["project", "objectives", "artifacts"],
            "reasoning": [
                "project: Product requirements, user stories, architecture",
                "objectives: Sprint goals, OKRs, milestones",
                "artifacts: Release notes, deployment history",
            ],
        },
        "Documentation Writer": {
            "scopes": ["global", "project", "objectives", "artifacts"],
            "reasoning": [
                "global: Writing standards, style guides",
                "project: API specs, architecture decisions",
                "objectives: Current documentation goals",
                "artifacts: Recent code changes to document",
            ],
        },
        "QA Engineer": {
            "scopes": ["project", "thread", "artifacts"],
            "reasoning": [
                "project: Test plans, known bugs, quality standards",
                "thread: Current testing conversation",
                "artifacts: Build results, test reports, deployments",
            ],
        },
    }

    for role, info in use_cases.items():
        print(f"\n🎭 {role}:")
        print(f"   Scopes: {info['scopes']}")
        print("   Why each scope is needed:")
        for reason in info["reasoning"]:
            print(f"     • {reason}")


if __name__ == "__main__":
    print("Multi-Scope Memory Test Suite")
    print("Testing enhanced memory scope functionality\n")

    success = test_multi_scope_memory()

    if success:
        demonstrate_scope_use_cases()

    sys.exit(0 if success else 1)

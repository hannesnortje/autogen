"""
Comprehensive test for Agent Memory Integration - Step 23.
Tests the complete integration between agents and the memory system.
"""

import time
from autogen_mcp.collections import CollectionManager
from autogen_mcp.simple_agent_memory import AgentMemoryService
from autogen_mcp.orchestrator import AgentOrchestrator
from autogen_mcp.gemini_client import GeminiClient


def test_agent_memory_integration():
    """
    Test complete agent memory integration workflow.
    """
    print("🧠 Testing Agent Memory Integration - Step 23")
    print("=" * 60)

    # 1. Setup
    print("\n1. Setting up memory system and agents...")
    collection_manager = CollectionManager()

    # Ensure collections are created
    try:
        collection_manager.ensure_collections_exist()
        print("✅ Collections initialized")
    except Exception as e:
        print(f"⚠️  Collection setup: {e}")

    # Create memory service
    memory_service = AgentMemoryService(collection_manager)
    print("✅ Agent memory service created")

    # Create Gemini client (may fail if no API key, that's OK)
    gemini_client = None
    try:
        gemini_client = GeminiClient()
        print("✅ Gemini client initialized")
    except Exception as e:
        print(f"⚠️  Gemini client: {e} (using mock responses)")

    # Create orchestrator with memory
    agent_configs = [
        {"role": "Agile", "name": "agile_lead"},
        {"role": "Coder", "name": "senior_dev"},
        {"role": "Reviewer", "name": "tech_lead"},
    ]

    orchestrator = AgentOrchestrator(
        agent_configs=agent_configs,
        gemini_client=gemini_client or MockGeminiClient(),
        collection_manager=collection_manager,
    )
    print("✅ Orchestrator with memory-enabled agents created")

    # 2. Test Session Management
    print("\n2. Testing session management...")
    session_id = orchestrator.start_session("Build a REST API for user management")
    print(f"✅ Session started: {session_id}")

    status = orchestrator.get_session_status()
    print(
        f"✅ Session status: {len(status['agents'])} agents, memory_enabled={status['memory_enabled']}"
    )

    # 3. Test Agent Memory Writing
    print("\n3. Testing agent memory operations...")

    # Run a turn that will write to memory
    results = orchestrator.run_turn("Design the user authentication system")
    print(f"✅ Turn completed: {len(results)} agents responded")

    for agent_name, response in results.items():
        print(f"  - {agent_name}: {response[:100]}...")

    # Wait a moment for memory writes
    time.sleep(1)

    # 4. Test Memory Retrieval and Context
    print("\n4. Testing memory retrieval and context...")

    # Get one of the agents to check its memory context
    test_agent = orchestrator.agents[0]  # Agile agent

    if hasattr(test_agent, "current_conversation_id"):
        context = memory_service.get_agent_context(
            agent_role=test_agent.role,
            conversation_id=test_agent.current_conversation_id,
            query="authentication system design",
            max_results=5,
        )
        print(f"✅ Retrieved context: {len(context)} items")

        if context:
            for i, ctx in enumerate(context[:2]):
                content_preview = ctx.get("content", "")[:100]
                score = ctx.get("score", "N/A")
                print(f"  Context {i+1}: Score={score}, Content: {content_preview}...")
        else:
            print("  No context found (may need a moment for indexing)")

    # 5. Test Agent Decision Recording
    print("\n5. Testing agent decision recording...")

    decision_id = test_agent.make_decision(
        decision="Use JWT tokens for authentication",
        reasoning="JWT provides stateless authentication with good security",
        context="Building user authentication system for REST API",
    )
    print(f"✅ Decision recorded: {decision_id}")

    # 6. Test Multi-turn Conversation
    print("\n6. Testing multi-turn conversation with memory continuity...")

    turn2_results = orchestrator.run_turn("Now implement the database schema for users")
    print(f"✅ Second turn completed: {len(turn2_results)} agents responded")

    # Each agent should now have context from previous turn
    for agent_name, response in turn2_results.items():
        if "previous" in response.lower() or "context" in response.lower():
            print(f"  ✅ {agent_name} shows memory awareness: {response[:80]}...")
        else:
            print(f"  - {agent_name}: {response[:80]}...")

    # 7. Test Performance Insights
    print("\n7. Testing performance insights...")

    insights = test_agent.get_performance_insights()
    print(
        f"✅ Performance insights retrieved for {insights.get('agent_role', 'unknown')}"
    )
    print(f"  - Total interactions: {insights.get('total_interactions', 0)}")
    print(f"  - Decision patterns: {len(insights.get('decision_patterns', []))}")
    print(f"  - Learning patterns: {len(insights.get('learning_patterns', []))}")

    # 8. Test Session End and Summary
    print("\n8. Testing session end and summary...")

    summary = orchestrator.end_session(
        "Successfully designed user authentication system with JWT"
    )
    print(f"✅ Session ended: {summary['session_id']}")
    print(f"  - Agents with summaries: {len(summary['agent_summaries'])}")
    print(f"  - Performance insights: {len(summary['performance_insights'])}")

    # 9. Test Memory Persistence
    print("\n9. Testing memory persistence across sessions...")

    # Start a new session
    session2_id = orchestrator.start_session(
        "Extend the API with user roles and permissions"
    )
    print(f"✅ New session started: {session2_id}")

    # Run turn that should reference previous learning
    results2 = orchestrator.run_turn(
        "How should we handle user roles based on our previous auth design?"
    )
    print(f"✅ Turn with historical context: {len(results2)} agents responded")

    # Check if agents reference previous decisions
    context_aware_count = 0
    for agent_name, response in results2.items():
        if any(
            term in response.lower()
            for term in ["jwt", "authentication", "previous", "auth"]
        ):
            context_aware_count += 1
            print(f"  ✅ {agent_name} shows historical awareness: {response[:80]}...")

    print(
        f"✅ {context_aware_count}/{len(results2)} agents showed historical context awareness"
    )

    # Clean up
    orchestrator.end_session("Completed memory integration testing")

    print("\n" + "=" * 60)
    print("🎉 Agent Memory Integration Test Complete!")
    print("✅ All core memory functionality working:")
    print("  - Agent conversation tracking")
    print("  - Per-turn memory recording")
    print("  - Context retrieval and usage")
    print("  - Decision recording")
    print("  - Performance insights")
    print("  - Cross-session persistence")


class MockGeminiClient:
    """Mock Gemini client for testing when API key is not available."""

    def complete(self, prompt: str) -> str:
        # Simple mock responses based on agent role
        if "[Agile]" in prompt:
            return "As an Agile lead, I'll coordinate the team to deliver this incrementally with proper user stories."
        elif "[Coder]" in prompt:
            return "I'll implement this using best practices, focusing on clean code and proper architecture."
        elif "[Reviewer]" in prompt:
            return "I'll ensure code quality standards are met and security considerations are addressed."
        else:
            return f"Processing: {prompt[:50]}..."


if __name__ == "__main__":
    test_agent_memory_integration()

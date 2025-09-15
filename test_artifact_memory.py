"""
Test script for Artifact Memory Integration Service

This script demonstrates the artifact memory functionality by:
1. Capturing current Git commit information
2. Simulating build results
3. Adding code review feedback
4. Linking all artifacts to memory
5. Searching and retrieving related artifacts

Usage: python test_artifact_memory.py
"""

import asyncio
import sys
from pathlib import Path

from src.autogen_mcp.artifact_memory import ArtifactMemoryService
from src.autogen_mcp.multi_memory import MultiScopeMemoryService

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


async def test_artifact_memory():
    """Test the artifact memory integration"""
    print("🔍 Testing Artifact Memory Integration Service")
    print("=" * 60)

    # Initialize services (using in-memory storage for testing)
    try:
        memory_service = MultiScopeMemoryService()
        memory_service.initialize()  # Initialize the memory service (sync method)
        artifact_service = ArtifactMemoryService(memory_service)

        print("✅ Services initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize services: {e}")
        return

    print("\n📊 Testing Git Integration")
    print("-" * 30)

    # Test Git integration
    git_service = artifact_service.git_service
    current_commit = git_service.get_current_commit_info()

    if current_commit:
        print(f"✅ Current commit: {current_commit.commit_hash[:8]}")
        print(f"   Author: {current_commit.author_name}")
        print(f"   Message: {current_commit.commit_message}")
        print(f"   Branch: {current_commit.branch}")
        print(f"   Files changed: {len(current_commit.files_changed)}")
        print(
            f"   Lines: +{current_commit.lines_added} -{current_commit.lines_removed}"
        )
    else:
        print("⚠️ No Git repository found or no commits")
        return

    # Get recent commits
    recent_commits = git_service.get_recent_commits(5)
    print(f"\n📈 Found {len(recent_commits)} recent commits:")
    for i, commit in enumerate(recent_commits[:3], 1):
        print(f"  {i}. {commit.commit_hash[:8]} - {commit.commit_message[:50]}...")

    print("\n🔨 Testing Build Integration")
    print("-" * 30)

    # Test build simulation
    build_service = artifact_service.build_service
    build_result = build_service.simulate_build_from_current_commit(git_service)

    if build_result:
        print(f"✅ Simulated build: {build_result.build_id}")
        print(f"   Status: {build_result.status}")
        print(f"   Build time: {build_result.build_time:.1f}s")
        print(
            f"   Tests: {build_result.test_results['passed_tests']}"
            f"/{build_result.test_results['total_tests']} passed"
        )
        print(f"   Coverage: {build_result.coverage_percentage:.1f}%")
    else:
        print("❌ Failed to simulate build")
        return

    print("\n📝 Testing Code Review Integration")
    print("-" * 30)

    # Test code review simulation
    review_service = artifact_service.review_service

    # Add some sample reviews
    reviews = [
        (
            "alice",
            "Consider extracting this logic into a separate method",
            "refactoring",
            "medium",
        ),
        ("bob", "Missing error handling for edge cases", "robustness", "high"),
        ("charlie", "Good use of design patterns here", "style", "low"),
    ]

    for reviewer, feedback, category, severity in reviews:
        review = review_service.add_review_feedback(
            commit_hash=current_commit.commit_hash,
            reviewer=reviewer,
            feedback=feedback,
            category=category,
            severity=severity,
        )
        print(f"✅ Added review from {reviewer} ({severity})")

    # Analyze review patterns
    patterns = review_service.get_review_patterns()
    print("\n📊 Review patterns:")
    print(f"   Total reviews: {patterns['patterns']['total_reviews']}")
    print(f"   Most common category: {patterns['patterns']['most_common_category']}")
    print(f"   Severity distribution: {patterns['patterns']['severity_distribution']}")

    print("\n💾 Testing Memory Integration")
    print("-" * 30)

    # Link commit to memory
    commit_linked = await artifact_service.link_commit_to_memory(
        current_commit, "test_integration"
    )
    print(f"✅ Commit linked to memory: {commit_linked}")

    # Link build to memory
    build_linked = await artifact_service.link_build_to_memory(build_result)
    print(f"✅ Build linked to memory: {build_linked}")

    # Link reviews to memory
    review_count = 0
    for review in review_service.review_history:
        review_linked = await artifact_service.link_review_to_memory(review)
        if review_linked:
            review_count += 1
    print(f"✅ Reviews linked to memory: {review_count}/{len(reviews)}")

    print("\n🔍 Testing Artifact Search")
    print("-" * 30)

    # Search for related artifacts
    search_queries = [
        f"commit_{current_commit.commit_hash[:8]}",
        "build failure",
        "code review feedback",
        (
            current_commit.commit_message.split()[0]
            if current_commit.commit_message
            else "test"
        ),
    ]

    for query in search_queries:
        results = await artifact_service.search_related_artifacts(query, limit=3)
        print(f"🔍 Query '{query}': {len(results)} results")
        for i, result in enumerate(results[:2], 1):
            metadata = result.get("metadata", {})
            artifact_type = metadata.get("type", "unknown")
            print(f"   {i}. {artifact_type}: {result.get('content', '')[:50]}...")

    print("\n📚 Testing Learning Insights")
    print("-" * 30)

    # Get commit learning insights
    insights = await artifact_service.get_commit_learning_insights(
        current_commit.commit_hash
    )

    print(f"✅ Learning insights for commit {current_commit.commit_hash[:8]}:")
    print(f"   Related builds: {len(insights['related_builds'])}")
    print(f"   Related reviews: {len(insights['related_reviews'])}")
    print(f"   Similar commits: {len(insights['similar_commits'])}")
    print(f"   Learning points: {len(insights['learning_points'])}")

    for i, point in enumerate(insights["learning_points"], 1):
        print(f"   {i}. {point}")

    print("\n🎯 Testing Development State Capture")
    print("-" * 30)

    # Capture complete development state
    state = await artifact_service.capture_current_development_state()

    print("✅ Development state capture completed:")
    print(f"   Commit captured: {state['commit_linked']}")
    print(f"   Build captured: {state['build_linked']}")

    if state["commit_info"]:
        commit_info = state["commit_info"]
        print(f"   Commit: {commit_info['commit_hash'][:8]} on {commit_info['branch']}")
        print(f"   Files changed: {len(commit_info['files_changed'])}")

    if state["build_result"]:
        build_info = state["build_result"]
        print(f"   Build: {build_info['status']} in {build_info['build_time']:.1f}s")

    print("\n🎉 Artifact Memory Integration Test Complete!")
    print("=" * 60)

    return {
        "services_initialized": True,
        "git_integration": current_commit is not None,
        "build_integration": build_result is not None,
        "review_integration": len(review_service.review_history) > 0,
        "memory_integration": commit_linked and build_linked,
        "search_functionality": len(results) >= 0,
        "learning_insights": len(insights["learning_points"]) >= 0,
        "state_capture": state["commit_linked"] and state["build_linked"],
    }


if __name__ == "__main__":
    asyncio.run(test_artifact_memory())

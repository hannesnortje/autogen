#!/usr/bin/env python3
"""
Demo of cross-project learning capabilities for AutoGen MCP Server.

This script demonstrates how the cross-project learning service can:
1. Register projects with their characteristics
2. Find similar projects based on technology and domain
3. Generate recommendations based on cross-project insights
4. Analyze patterns across multiple projects
"""

from unittest.mock import Mock

from src.autogen_mcp.cross_project_learning import CrossProjectLearningService


def demonstrate_cross_project_learning():
    """Demonstrate the cross-project learning service capabilities"""

    print("🚀 Cross-Project Learning Service Demonstration")
    print("=" * 60)

    # Setup mock services (in real usage, these would be actual services)
    mock_memory_service = Mock()
    mock_artifact_service = Mock()

    # Mock memory search for global knowledge
    mock_memory_service.search.return_value = [
        {
            "content": "SOLID principles ensure maintainable code through single responsibility, open-closed, liskov substitution, interface segregation, and dependency inversion principles.",
            "metadata": {"category": "SOLID Principles"},
        },
        {
            "content": "PDCA cycle (Plan-Do-Check-Act) provides a structured approach for continuous improvement in software development processes.",
            "metadata": {"category": "PDCA Methodology"},
        },
    ]

    # Initialize the service
    service = CrossProjectLearningService(mock_memory_service, mock_artifact_service)

    print("\n📝 Step 1: Registering Projects")
    print("-" * 40)

    # Register multiple projects to build the knowledge base
    projects = [
        {
            "project_id": "ecommerce-platform",
            "name": "E-commerce Platform",
            "description": "Scalable online shopping platform with payment processing",
            "tech_stack": ["python", "django", "postgresql", "redis", "celery"],
            "domain": "web",
        },
        {
            "project_id": "blog-cms",
            "name": "Blog Content Management System",
            "description": "Modern blogging platform with rich content editing",
            "tech_stack": ["python", "flask", "postgresql", "elasticsearch"],
            "domain": "web",
        },
        {
            "project_id": "task-mobile-app",
            "name": "Mobile Task Manager",
            "description": "Cross-platform productivity app for task management",
            "tech_stack": ["typescript", "react-native", "sqlite", "redux"],
            "domain": "mobile",
        },
        {
            "project_id": "data-analytics",
            "name": "Business Analytics Dashboard",
            "description": "Real-time data analytics and visualization platform",
            "tech_stack": ["python", "pandas", "plotly", "postgresql"],
            "domain": "data-science",
        },
    ]

    # Mock pattern detection to return realistic patterns
    def mock_detect_patterns(project_id):
        pattern_map = {
            "ecommerce-platform": ["mvc", "repository", "factory", "observer"],
            "blog-cms": ["mvc", "repository", "singleton"],
            "task-mobile-app": ["mvvm", "observer", "command"],
            "data-analytics": ["etl_pattern", "repository", "observer"],
        }
        return pattern_map.get(project_id, [])

    # Mock metrics computation to return realistic success metrics
    def mock_compute_metrics(project_id):
        metrics_map = {
            "ecommerce-platform": {
                "overall_success": 0.92,
                "build_success_rate": 0.95,
                "test_coverage": 0.88,
                "code_quality": 0.90,
            },
            "blog-cms": {
                "overall_success": 0.85,
                "build_success_rate": 0.90,
                "test_coverage": 0.80,
                "code_quality": 0.85,
            },
            "task-mobile-app": {
                "overall_success": 0.78,
                "build_success_rate": 0.85,
                "test_coverage": 0.75,
                "code_quality": 0.80,
            },
            "data-analytics": {
                "overall_success": 0.88,
                "build_success_rate": 0.92,
                "test_coverage": 0.85,
                "code_quality": 0.87,
            },
        }
        return metrics_map.get(project_id, {})

    # Patch the methods
    service._detect_patterns_in_project = mock_detect_patterns
    service._compute_project_metrics = mock_compute_metrics

    # Register all projects
    for project_data in projects:
        profile = service.register_project(**project_data)
        print(f"✅ Registered: {profile.name} ({profile.domain})")
        print(f"   Tech Stack: {', '.join(profile.tech_stack[:3])}...")
        print(f"   Patterns: {', '.join(profile.patterns_used)}")
        print(
            f"   Success Score: {profile.success_metrics.get('overall_success', 0):.2f}"
        )
        print()

    print("\n🔍 Step 2: Getting Project Recommendations")
    print("-" * 40)

    # Get recommendations for a new web project
    target_project = "blog-cms"
    recommendations = service.get_project_recommendations(target_project)

    print(f"📊 Recommendations for: {recommendations['project_name']}")
    print()

    # Show similar projects
    print("🤝 Similar Projects:")
    for similar in recommendations["similar_projects"]:
        print(
            f"   • {similar['project_id']} (similarity: {similar['similarity_score']:.3f})"
        )
        print(f"     Common patterns: {', '.join(similar['common_patterns'])}")
        factors = similar["similarity_factors"]
        print(
            f"     Tech: {factors['tech_stack']:.2f}, Domain: {factors['domain']:.2f}, Patterns: {factors['patterns_used']:.2f}"
        )
        print()

    # Show global knowledge recommendations
    print("🌐 Global Knowledge Recommendations:")
    for rec in recommendations["global_patterns_to_consider"][:3]:
        print(f"   • {rec['title']}")
        print(f"     {rec['description'][:100]}...")
        print()

    print("\n📈 Step 3: Cross-Project Analysis")
    print("-" * 40)

    # Analyze patterns across all projects
    analysis = service.analyze_cross_project_patterns()

    print(f"🏗️ Total Projects Analyzed: {analysis['total_projects']}")
    print()

    print("💻 Most Popular Technologies:")
    for tech, count in analysis["most_popular_technologies"][:5]:
        print(f"   • {tech}: used in {count} projects")
    print()

    print("🏢 Domain Distribution:")
    for domain, count in analysis["domain_distribution"].items():
        print(f"   • {domain}: {count} projects")
    print()

    print("🎯 Most Used Patterns:")
    for pattern, count in analysis["most_used_patterns"][:5]:
        print(f"   • {pattern}: used in {count} projects")
    print()

    print("📊 Average Success Metrics:")
    for metric, value in analysis["average_success_metrics"].items():
        print(f"   • {metric}: {value:.3f}")
    print()

    print("💡 Cross-Project Insights:")
    for insight in analysis["cross_project_insights"]:
        print(f"   • {insight}")
    print()

    print("\n🎯 Step 4: Simulating New Project Registration")
    print("-" * 40)

    # Register a new project and see recommendations
    new_project_profile = service.register_project(
        project_id="social-media-app",
        name="Social Media Platform",
        description="Modern social networking application with real-time features",
        tech_stack=["python", "django", "postgresql", "redis", "websockets"],
        domain="web",
    )

    print(f"✅ New Project Registered: {new_project_profile.name}")
    print(f"   Detected Patterns: {', '.join(new_project_profile.patterns_used)}")
    print()

    # Get recommendations for the new project
    new_recommendations = service.get_project_recommendations("social-media-app")

    print("🎯 Recommendations for New Project:")
    print(f"   Found {len(new_recommendations['similar_projects'])} similar projects")

    if new_recommendations["similar_projects"]:
        best_match = new_recommendations["similar_projects"][0]
        print(
            f"   Best match: {best_match['project_id']} (similarity: {best_match['similarity_score']:.3f})"
        )
        print(f"   Shared patterns: {', '.join(best_match['common_patterns'])}")

    print()
    print("✨ Demonstration Complete! The cross-project learning service can:")
    print("   • Register and profile projects with automatic pattern detection")
    print("   • Find similar projects based on tech stack, domain, and patterns")
    print("   • Provide global knowledge recommendations (PDCA, SOLID, etc.)")
    print("   • Analyze trends and insights across the project portfolio")
    print("   • Suggest solutions and best practices from similar successful projects")


if __name__ == "__main__":
    demonstrate_cross_project_learning()

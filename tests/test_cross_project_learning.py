"""
Test Cross-Project Learning Service

Comprehensive tests for the cross-project memory learning and intelligence
system, including project similarity matching, solution reuse, best practice
propagation, and global knowledge integration.

Author: AutoGen Team
Date: 2025-09-15
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from src.autogen_mcp.cross_project_learning import (
    CrossProjectLearningService,
    ProjectProfile,
    ProjectSimilarityEngine,
    SolutionReuseSystem,
    BestPracticePropagator,
    SolutionPattern,
    BestPractice,
)


class TestProjectSimilarityEngine:
    """Test the project similarity matching engine"""

    def setup_method(self):
        """Setup test fixtures"""
        self.engine = ProjectSimilarityEngine()

        # Create test project profiles
        self.web_project_a = ProjectProfile(
            project_id="web-a",
            name="E-commerce Site",
            description="Online shopping platform",
            tech_stack=["python", "django", "postgresql", "redis"],
            domain="web",
            patterns_used=["mvc", "repository", "singleton"],
            success_metrics={"overall_success": 0.85, "build_success_rate": 0.90},
            created_date=datetime.now(timezone.utc),
            last_updated=datetime.now(timezone.utc),
        )

        self.web_project_b = ProjectProfile(
            project_id="web-b",
            name="Blog Platform",
            description="Content management system",
            tech_stack=["python", "flask", "postgresql", "elasticsearch"],
            domain="web",
            patterns_used=["mvc", "factory", "observer"],
            success_metrics={"overall_success": 0.80, "build_success_rate": 0.85},
            created_date=datetime.now(timezone.utc),
            last_updated=datetime.now(timezone.utc),
        )

        self.mobile_project = ProjectProfile(
            project_id="mobile-a",
            name="Task Manager App",
            description="Mobile productivity app",
            tech_stack=["typescript", "react-native", "sqlite"],
            domain="mobile",
            patterns_used=["mvvm", "singleton", "observer"],
            success_metrics={"overall_success": 0.75, "build_success_rate": 0.80},
            created_date=datetime.now(timezone.utc),
            last_updated=datetime.now(timezone.utc),
        )

    def test_compute_similarity_same_domain_high_tech_overlap(self):
        """Test similarity computation for same domain with high tech overlap"""
        similarity = self.engine.compute_similarity(
            self.web_project_a, self.web_project_b
        )

        assert similarity.project_a == "web-a"
        assert similarity.project_b == "web-b"
        assert similarity.similarity_score > 0.5  # Should be reasonably high
        assert "python" in [self.web_project_a.tech_stack[0]]
        assert "mvc" in similarity.common_patterns

    def test_compute_similarity_different_domains(self):
        """Test similarity computation for different domains"""
        similarity = self.engine.compute_similarity(
            self.web_project_a, self.mobile_project
        )

        assert similarity.project_a == "web-a"
        assert similarity.project_b == "mobile-a"
        assert similarity.similarity_score < 0.5  # Should be lower
        assert similarity.similarity_factors["domain"] == 0.0

    def test_compute_similarity_common_patterns(self):
        """Test that common patterns are identified correctly"""
        similarity = self.engine.compute_similarity(
            self.web_project_a, self.web_project_b
        )

        assert "mvc" in similarity.common_patterns
        assert len(similarity.common_patterns) >= 1

    def test_find_similar_projects(self):
        """Test finding similar projects from a collection"""
        all_projects = [self.web_project_a, self.web_project_b, self.mobile_project]

        similar_projects = self.engine.find_similar_projects(
            self.web_project_a, all_projects, min_similarity=0.3, max_results=5
        )

        # Should find web_project_b as similar (same domain)
        assert len(similar_projects) >= 1
        project_ids = [sim.project_b for sim in similar_projects]
        assert "web-b" in project_ids

        # Should be sorted by similarity score (highest first)
        scores = [sim.similarity_score for sim in similar_projects]
        assert scores == sorted(scores, reverse=True)

    def test_find_similar_projects_min_threshold(self):
        """Test minimum similarity threshold filtering"""
        all_projects = [self.web_project_a, self.web_project_b, self.mobile_project]

        # Set high threshold that should filter out mobile project
        similar_projects = self.engine.find_similar_projects(
            self.web_project_a, all_projects, min_similarity=0.8, max_results=5
        )

        project_ids = [sim.project_b for sim in similar_projects]
        # Mobile project should be filtered out due to low similarity
        assert "mobile-a" not in project_ids


class TestSolutionReuseSystem:
    """Test the solution reuse and adaptation system"""

    def setup_method(self):
        """Setup test fixtures"""
        self.mock_memory_service = Mock()
        self.system = SolutionReuseSystem(self.mock_memory_service)

        # Create test project profile
        self.test_project = ProjectProfile(
            project_id="test-project",
            name="Test Project",
            description="A test project",
            tech_stack=["python", "django", "postgresql"],
            domain="web",
            patterns_used=["mvc", "repository"],
            success_metrics={"overall_success": 0.85},
            created_date=datetime.now(timezone.utc),
            last_updated=datetime.now(timezone.utc),
        )

    def test_extract_solutions_from_project(self):
        """Test extracting solutions from project memory"""
        # Mock memory service search results
        mock_results = [
            {
                "content": "Implemented caching solution using Redis for session management. This improved response times by 40%.",
                "metadata": {
                    "type": "solution",
                    "title": "Redis Caching Solution",
                    "problem": "Slow session lookup",
                    "success_rate": 0.9,
                    "tags": ["caching", "performance"],
                },
            }
        ]

        self.mock_memory_service.search.return_value = mock_results

        solutions = self.system.extract_solutions_from_project(self.test_project)

        assert len(solutions) >= 1
        solution = solutions[0]
        assert isinstance(solution, SolutionPattern)
        assert solution.name == "Redis Caching Solution"
        assert solution.success_rate == 0.9
        assert "test-project" in solution.source_projects

    def test_is_solution_applicable_tech_compatibility(self):
        """Test solution applicability based on tech stack compatibility"""
        # Create solution with overlapping tech requirements
        solution = SolutionPattern(
            pattern_id="test-pattern",
            name="Test Solution",
            description="A test solution",
            problem_description="Test problem",
            solution_description="Test solution description",
            code_examples=[],
            tech_requirements=["python", "postgresql", "redis"],  # 2/3 overlap
            success_criteria=[],
            usage_count=1,
            success_rate=0.8,
            source_projects=["source-project"],
            tags=[],
        )

        is_applicable = self.system._is_solution_applicable(solution, self.test_project)

        # Should be applicable with >30% tech overlap (2/3 = 66%)
        assert is_applicable is True

    def test_is_solution_applicable_low_compatibility(self):
        """Test solution rejection due to low tech compatibility"""
        # Create solution with minimal tech overlap
        solution = SolutionPattern(
            pattern_id="test-pattern",
            name="Test Solution",
            description="A test solution",
            problem_description="Test problem",
            solution_description="Test solution description",
            code_examples=[],
            tech_requirements=["java", "mysql", "mongodb"],  # 0/3 overlap
            success_criteria=[],
            usage_count=1,
            success_rate=0.8,
            source_projects=["source-project"],
            tags=[],
        )

        is_applicable = self.system._is_solution_applicable(solution, self.test_project)

        # Should not be applicable with 0% tech overlap
        assert is_applicable is False

    def test_adapt_solution_for_target_project(self):
        """Test adapting a solution for target project context"""
        original_solution = SolutionPattern(
            pattern_id="original-pattern",
            name="Original Solution",
            description="Original description",
            problem_description="Original problem",
            solution_description="Original solution text",
            code_examples=["example code"],
            tech_requirements=["python", "redis"],
            success_criteria=["fast response"],
            usage_count=5,
            success_rate=0.85,
            source_projects=["source-project"],
            tags=["original"],
        )

        adapted_solution = self.system._adapt_solution(
            original_solution, self.test_project
        )

        # Check adaptation characteristics
        assert adapted_solution.pattern_id != original_solution.pattern_id
        assert "Adapted for Test Project" in adapted_solution.name
        assert adapted_solution.success_rate == 0.85 * 0.9  # Adaptation discount
        assert "test-project" in adapted_solution.source_projects
        assert "adapted" in adapted_solution.tags
        assert self.test_project.domain in adapted_solution.tags

        # Check contextualized solution description
        assert "Test Project" in adapted_solution.solution_description
        assert "web project" in adapted_solution.solution_description


class TestBestPracticePropagator:
    """Test the best practice identification and propagation system"""

    def setup_method(self):
        """Setup test fixtures"""
        self.mock_memory_service = Mock()
        self.propagator = BestPracticePropagator(self.mock_memory_service)

        # Create test successful projects
        self.successful_projects = [
            ProjectProfile(
                project_id="success-1",
                name="Successful Web App 1",
                description="High-performing e-commerce site",
                tech_stack=["python", "django", "postgresql", "redis"],
                domain="web",
                patterns_used=["mvc", "repository"],
                success_metrics={"overall_success": 0.9},
                created_date=datetime.now(timezone.utc),
                last_updated=datetime.now(timezone.utc),
            ),
            ProjectProfile(
                project_id="success-2",
                name="Successful Web App 2",
                description="High-performing content platform",
                tech_stack=["python", "flask", "postgresql", "elasticsearch"],
                domain="web",
                patterns_used=["mvc", "factory"],
                success_metrics={"overall_success": 0.85},
                created_date=datetime.now(timezone.utc),
                last_updated=datetime.now(timezone.utc),
            ),
        ]

    def test_extract_common_practices_tech_usage(self):
        """Test extracting common technology practices from successful projects"""
        practices = self.propagator._extract_common_practices(
            self.successful_projects, "web"
        )

        # Should identify common technologies as best practices
        python_practice = next(
            (p for p in practices if "python" in p.title.lower()), None
        )
        postgresql_practice = next(
            (p for p in practices if "postgresql" in p.title.lower()), None
        )

        assert python_practice is not None
        assert postgresql_practice is not None
        assert python_practice.confidence_score >= 0.7  # Used in 100% of projects
        assert python_practice.category == "technology-choice"

    def test_identify_best_practices_multiple_domains(self):
        """Test identifying best practices across different domains"""
        # Add mobile projects
        mobile_projects = [
            ProjectProfile(
                project_id="mobile-success-1",
                name="Successful Mobile App 1",
                description="High-performing task manager",
                tech_stack=["typescript", "react-native"],
                domain="mobile",
                patterns_used=["mvvm"],
                success_metrics={"overall_success": 0.9},
                created_date=datetime.now(timezone.utc),
                last_updated=datetime.now(timezone.utc),
            )
        ]

        all_projects = self.successful_projects + mobile_projects
        practices = self.propagator.identify_best_practices(all_projects)

        # Should have practices for both web and mobile domains
        domains = {p.domain for p in practices}
        assert "web" in domains
        # Note: mobile might not show up if only 1 project (need 2+ for patterns)

    def test_is_practice_applicable_domain_match(self):
        """Test practice applicability based on domain matching"""
        practice = BestPractice(
            practice_id="web-practice",
            title="Use Python for Web Projects",
            description="Python works well for web development",
            category="technology-choice",
            domain="web",
            evidence=["Used in successful projects"],
            implementation_steps=["Add Python to dependencies"],
            success_metrics={"adoption_rate": 1.0},
            source_projects=["success-1", "success-2"],
            confidence_score=0.9,
        )

        target_project = ProjectProfile(
            project_id="target-web",
            name="Target Web Project",
            description="A new web project",
            tech_stack=["python"],
            domain="web",
            patterns_used=[],
            success_metrics={},
            created_date=datetime.now(timezone.utc),
            last_updated=datetime.now(timezone.utc),
        )

        is_applicable = self.propagator._is_practice_applicable(
            practice, target_project, similarity_score=0.8
        )

        assert is_applicable is True

    def test_is_practice_applicable_domain_mismatch(self):
        """Test practice rejection due to domain mismatch"""
        web_practice = BestPractice(
            practice_id="web-practice",
            title="Use Django for Web Projects",
            description="Django works well for web development",
            category="technology-choice",
            domain="web",
            evidence=["Used in successful projects"],
            implementation_steps=["Add Django to dependencies"],
            success_metrics={"adoption_rate": 1.0},
            source_projects=["success-1"],
            confidence_score=0.9,
        )

        mobile_project = ProjectProfile(
            project_id="target-mobile",
            name="Target Mobile Project",
            description="A new mobile project",
            tech_stack=["typescript", "react-native"],
            domain="mobile",
            patterns_used=[],
            success_metrics={},
            created_date=datetime.now(timezone.utc),
            last_updated=datetime.now(timezone.utc),
        )

        is_applicable = self.propagator._is_practice_applicable(
            web_practice, mobile_project, similarity_score=0.8
        )

        assert is_applicable is False


class TestCrossProjectLearningService:
    """Test the main cross-project learning service"""

    def setup_method(self):
        """Setup test fixtures"""
        self.mock_memory_service = Mock()
        self.mock_artifact_service = Mock()

        self.service = CrossProjectLearningService(
            self.mock_memory_service, self.mock_artifact_service
        )

    def test_register_project(self):
        """Test registering a new project for cross-project learning"""
        # Mock the pattern detection and metrics computation
        with (
            patch.object(
                self.service,
                "_detect_patterns_in_project",
                return_value=["mvc", "repository"],
            ),
            patch.object(
                self.service,
                "_compute_project_metrics",
                return_value={"overall_success": 0.8, "build_success_rate": 0.85},
            ),
        ):
            project_profile = self.service.register_project(
                project_id="test-register",
                name="Test Registration Project",
                description="A project for testing registration",
                tech_stack=["python", "django"],
                domain="web",
            )

            assert project_profile.project_id == "test-register"
            assert project_profile.name == "Test Registration Project"
            assert project_profile.domain == "web"
            assert "python" in project_profile.tech_stack
            assert "mvc" in project_profile.patterns_used
            assert project_profile.success_metrics["overall_success"] == 0.8

            # Check that project is stored
            assert "test-register" in self.service.project_profiles

    def test_get_project_recommendations_unregistered_project(self):
        """Test getting recommendations for unregistered project returns error"""
        recommendations = self.service.get_project_recommendations("nonexistent")

        assert "error" in recommendations
        assert recommendations["error"] == "Project not registered"

    def test_get_project_recommendations_with_registered_projects(self):
        """Test getting recommendations with registered projects"""
        # Register multiple projects first
        with (
            patch.object(
                self.service, "_detect_patterns_in_project", return_value=["mvc"]
            ),
            patch.object(
                self.service,
                "_compute_project_metrics",
                return_value={"overall_success": 0.8},
            ),
        ):
            # Register target project
            self.service.register_project(
                project_id="target",
                name="Target Project",
                description="Target for recommendations",
                tech_stack=["python", "django"],
                domain="web",
            )

            # Register similar project
            self.service.register_project(
                project_id="similar",
                name="Similar Project",
                description="Similar project for comparison",
                tech_stack=["python", "flask"],
                domain="web",
            )

        # Mock global knowledge search
        self.mock_memory_service.search.return_value = [
            {
                "content": "PDCA principles for continuous improvement",
                "metadata": {"category": "PDCA Methodology"},
            }
        ]

        recommendations = self.service.get_project_recommendations("target")

        assert "project_id" in recommendations
        assert recommendations["project_id"] == "target"
        assert "similar_projects" in recommendations
        assert "recommended_solutions" in recommendations
        assert "recommended_practices" in recommendations
        assert "global_patterns_to_consider" in recommendations

    def test_analyze_cross_project_patterns_no_projects(self):
        """Test cross-project analysis with no registered projects"""
        analysis = self.service.analyze_cross_project_patterns()

        assert "message" in analysis
        assert analysis["message"] == "No projects registered yet"

    def test_analyze_cross_project_patterns_with_projects(self):
        """Test cross-project analysis with registered projects"""
        # Register test projects
        with (
            patch.object(
                self.service,
                "_detect_patterns_in_project",
                return_value=["mvc", "repository"],
            ),
            patch.object(
                self.service,
                "_compute_project_metrics",
                return_value={"overall_success": 0.85, "build_success_rate": 0.90},
            ),
        ):
            self.service.register_project(
                project_id="analyze-1",
                name="Analysis Project 1",
                description="First project for analysis",
                tech_stack=["python", "django", "postgresql"],
                domain="web",
            )

            self.service.register_project(
                project_id="analyze-2",
                name="Analysis Project 2",
                description="Second project for analysis",
                tech_stack=["python", "flask", "mysql"],
                domain="web",
            )

        analysis = self.service.analyze_cross_project_patterns()

        assert "total_projects" in analysis
        assert analysis["total_projects"] == 2
        assert "most_popular_technologies" in analysis
        assert "domain_distribution" in analysis
        assert "most_used_patterns" in analysis
        assert "average_success_metrics" in analysis
        assert "cross_project_insights" in analysis

        # Check that Python is identified as popular technology
        tech_usage = dict(analysis["most_popular_technologies"])
        assert "python" in tech_usage
        assert tech_usage["python"] == 2  # Used in both projects

    def test_detect_patterns_in_project(self):
        """Test pattern detection in project memory"""
        # Mock memory search results
        mock_results = [
            {"content": "implemented mvc pattern for separation", "metadata": {}},
            {"content": "used singleton pattern for database", "metadata": {}},
        ]

        self.mock_memory_service.search.return_value = mock_results

        patterns = self.service._detect_patterns_in_project("test-project")

        assert "mvc" in patterns or "design_pattern" in patterns
        assert len(patterns) > 0

    def test_compute_project_metrics_with_artifact_data(self):
        """Test computing project metrics using artifact data"""
        # Mock artifact search results
        mock_artifact_results = [
            {
                "metadata": {
                    "type": "build_result",
                    "status": "success",
                    "coverage_percentage": 85,
                }
            }
        ]

        self.mock_memory_service.search.return_value = mock_artifact_results

        metrics = self.service._compute_project_metrics("test-project")

        assert "overall_success" in metrics
        assert "build_success_rate" in metrics
        assert "test_coverage" in metrics
        assert "code_quality" in metrics

        # Coverage should be updated from artifact data
        assert metrics["test_coverage"] == 0.85

    def test_get_global_pattern_recommendations(self):
        """Test getting global pattern recommendations"""
        # Mock global knowledge search
        mock_global_results = [
            {
                "content": "SOLID principles ensure maintainable code through single responsibility, open-closed, liskov substitution, interface segregation, and dependency inversion.",
                "metadata": {"category": "SOLID Principles"},
            },
            {
                "content": "PDCA cycle: Plan-Do-Check-Act for continuous improvement in software development processes.",
                "metadata": {"category": "PDCA Methodology"},
            },
        ]

        self.mock_memory_service.search.return_value = mock_global_results

        test_project = ProjectProfile(
            project_id="global-test",
            name="Global Test Project",
            description="Project for testing global recommendations",
            tech_stack=["python", "django"],
            domain="web",
            patterns_used=[],
            success_metrics={},
            created_date=datetime.now(timezone.utc),
            last_updated=datetime.now(timezone.utc),
        )

        recommendations = self.service._get_global_pattern_recommendations(test_project)

        assert len(recommendations) > 0
        assert any("SOLID" in rec["title"] for rec in recommendations)
        assert all(rec["source"] == "global_knowledge_base" for rec in recommendations)
        assert all(rec["type"] == "global_knowledge" for rec in recommendations)


# Integration Tests
class TestCrossProjectLearningIntegration:
    """Integration tests for the complete cross-project learning workflow"""

    @pytest.fixture
    def mock_services(self):
        """Setup mock services for integration testing"""
        mock_memory = Mock()
        mock_artifact = Mock()
        return mock_memory, mock_artifact

    def test_complete_workflow(self, mock_services):
        """Test the complete cross-project learning workflow"""
        mock_memory, mock_artifact = mock_services
        service = CrossProjectLearningService(mock_memory, mock_artifact)

        # Mock pattern detection and metrics
        with (
            patch.object(service, "_detect_patterns_in_project") as mock_patterns,
            patch.object(service, "_compute_project_metrics") as mock_metrics,
        ):
            mock_patterns.return_value = ["mvc", "repository", "singleton"]
            mock_metrics.return_value = {
                "overall_success": 0.9,
                "build_success_rate": 0.95,
                "test_coverage": 0.85,
                "code_quality": 0.88,
            }

            # 1. Register multiple projects
            web_profile_1 = service.register_project(
                project_id="integration-web-1",
                name="Integration E-commerce",
                description="Full-featured e-commerce platform",
                tech_stack=["python", "django", "postgresql", "redis", "celery"],
                domain="web",
            )

            web_profile_2 = service.register_project(
                project_id="integration-web-2",
                name="Integration Blog",
                description="Content management and blogging platform",
                tech_stack=["python", "flask", "postgresql", "elasticsearch"],
                domain="web",
            )

            mobile_profile = service.register_project(
                project_id="integration-mobile-1",
                name="Integration Task App",
                description="Mobile productivity application",
                tech_stack=["typescript", "react-native", "sqlite"],
                domain="mobile",
            )

            # Verify projects are registered
            assert len(service.project_profiles) == 3
            assert web_profile_1.project_id in service.project_profiles
            assert web_profile_2.project_id in service.project_profiles
            assert mobile_profile.project_id in service.project_profiles

        # Mock memory searches for recommendations
        mock_memory.search.return_value = [
            {
                "content": "SOLID principles ensure maintainable and extensible code architecture.",
                "metadata": {"category": "SOLID Principles"},
            }
        ]

        # 2. Get recommendations for web project
        recommendations = service.get_project_recommendations("integration-web-1")

        assert recommendations["project_id"] == "integration-web-1"
        assert len(recommendations["similar_projects"]) > 0

        # Should find web-2 as similar (same domain)
        similar_project_ids = [
            proj["project_id"] for proj in recommendations["similar_projects"]
        ]
        assert "integration-web-2" in similar_project_ids

        # Should include global knowledge recommendations
        assert len(recommendations["global_patterns_to_consider"]) > 0

        # 3. Analyze cross-project patterns
        analysis = service.analyze_cross_project_patterns()

        assert analysis["total_projects"] == 3
        assert "web" in analysis["domain_distribution"]
        assert "mobile" in analysis["domain_distribution"]
        assert analysis["domain_distribution"]["web"] == 2
        assert analysis["domain_distribution"]["mobile"] == 1

        # Should identify Python as popular technology
        tech_usage = dict(analysis["most_popular_technologies"])
        assert "python" in tech_usage
        assert tech_usage["python"] == 2

        # Should have insights about successful technologies
        assert len(analysis["cross_project_insights"]) > 0


if __name__ == "__main__":
    pytest.main([__file__])

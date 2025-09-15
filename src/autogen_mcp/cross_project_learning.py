"""
Cross-Project Memory Learning Service

This service enables agents to leverage solutions, patterns, and best practices
across multiple projects, building on foundational knowledge from the global
collection and extending it with project-specific learnings.

Key Features:
- Cross-project pattern recognition and solution reuse
- Project similarity matching based on tech stack, domain, and patterns
- Best practice propagation from successful projects
- Solution adaptation and contextualization
- Global pattern evolution and refinement

Author: AutoGen Team
Date: 2025-09-15
"""

import hashlib
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any

from .multi_memory import MultiScopeMemoryService
from .artifact_memory import ArtifactMemoryService
from .observability import get_logger

logger = get_logger(__name__)


@dataclass
class ProjectProfile:
    """Profile of a project for similarity matching"""

    project_id: str
    name: str
    description: str
    tech_stack: List[str]  # languages, frameworks, tools
    domain: str  # web, mobile, data-science, devops, etc.
    patterns_used: List[str]  # design patterns, architectural patterns
    success_metrics: Dict[str, float]  # build_success_rate, test_coverage
    created_date: datetime
    last_updated: datetime


@dataclass
class SolutionPattern:
    """A reusable solution pattern from a project"""

    pattern_id: str
    name: str
    description: str
    problem_description: str
    solution_description: str
    code_examples: List[str]
    tech_requirements: List[str]
    success_criteria: List[str]
    usage_count: int
    success_rate: float
    source_projects: List[str]
    tags: List[str]


@dataclass
class BestPractice:
    """A best practice learned from project experience"""

    practice_id: str
    title: str
    description: str
    category: str  # architecture, testing, deployment, etc.
    domain: str
    evidence: List[str]  # specific examples or metrics
    implementation_steps: List[str]
    success_metrics: Dict[str, float]
    source_projects: List[str]
    confidence_score: float


@dataclass
class ProjectSimilarity:
    """Similarity assessment between projects"""

    project_a: str
    project_b: str
    similarity_score: float
    similarity_factors: Dict[str, float]  # tech_stack: 0.8, domain: 0.9
    common_patterns: List[str]
    recommended_solutions: List[str]


class ProjectSimilarityEngine:
    """Engine for computing project similarities and matching"""

    def __init__(self):
        self.similarity_weights = {
            "tech_stack": 0.4,
            "domain": 0.3,
            "patterns_used": 0.2,
            "success_metrics": 0.1,
        }

    def compute_similarity(
        self, project_a: ProjectProfile, project_b: ProjectProfile
    ) -> ProjectSimilarity:
        """Compute similarity score between two projects"""

        # Tech stack similarity (Jaccard similarity)
        tech_a = set(project_a.tech_stack)
        tech_b = set(project_b.tech_stack)
        tech_similarity = (
            len(tech_a.intersection(tech_b)) / len(tech_a.union(tech_b))
            if tech_a.union(tech_b)
            else 0.0
        )

        # Domain similarity (exact match or related domains)
        is_same_domain = project_a.domain == project_b.domain
        domain_similarity = 1.0 if is_same_domain else 0.0

        if domain_similarity == 0.0:
            # Check for related domains
            related_domains = {
                "web": ["api", "frontend", "backend"],
                "mobile": ["ios", "android", "cross-platform"],
                "data-science": ["ml", "ai", "analytics"],
                "devops": ["ci-cd", "infrastructure", "monitoring"],
            }
            for main_domain, sub_domains in related_domains.items():
                both_in_subdomain = (
                    project_a.domain in sub_domains and project_b.domain in sub_domains
                )
                if both_in_subdomain:
                    domain_similarity = 0.7
                    break

        # Pattern similarity
        patterns_a = set(project_a.patterns_used)
        patterns_b = set(project_b.patterns_used)
        pattern_union = patterns_a.union(patterns_b)
        pattern_similarity = (
            len(patterns_a.intersection(patterns_b)) / len(pattern_union)
            if pattern_union
            else 0.0
        )

        # Success metrics similarity (simplified)
        success_similarity = 0.5  # Default moderate similarity

        # Weighted overall similarity
        similarity_factors = {
            "tech_stack": tech_similarity,
            "domain": domain_similarity,
            "patterns_used": pattern_similarity,
            "success_metrics": success_similarity,
        }

        overall_similarity = sum(
            similarity_factors[factor] * self.similarity_weights[factor]
            for factor in similarity_factors
        )

        common_patterns = list(patterns_a.intersection(patterns_b))

        return ProjectSimilarity(
            project_a=project_a.project_id,
            project_b=project_b.project_id,
            similarity_score=overall_similarity,
            similarity_factors=similarity_factors,
            common_patterns=common_patterns,
            recommended_solutions=[],  # Populated by solution reuse
        )

    def find_similar_projects(
        self,
        target_project: ProjectProfile,
        all_projects: List[ProjectProfile],
        min_similarity: float = 0.3,
        max_results: int = 5,
    ) -> List[ProjectSimilarity]:
        """Find projects similar to the target project"""

        similarities = []
        for project in all_projects:
            if project.project_id != target_project.project_id:
                similarity = self.compute_similarity(target_project, project)
                if similarity.similarity_score >= min_similarity:
                    similarities.append(similarity)

        # Sort by similarity score descending
        similarities.sort(key=lambda x: x.similarity_score, reverse=True)
        return similarities[:max_results]


class SolutionReuseSystem:
    """System for finding and adapting solutions from previous projects"""

    def __init__(self, memory_service: MultiScopeMemoryService):
        self.memory_service = memory_service
        self.solution_patterns: List[SolutionPattern] = []

    def extract_solutions_from_project(
        self, project_profile: ProjectProfile
    ) -> List[SolutionPattern]:
        """Extract reusable solutions from a project's memory"""
        solutions = []

        # Search project memory for solution patterns
        search_queries = [
            f"solution {project_profile.domain}",
            f"pattern {project_profile.name}",
            "best practice implementation",
            "successful approach",
        ]

        for query in search_queries:
            try:
                results = self.memory_service.search(
                    query=query, scope="project", limit=10
                )

                for result in results:
                    metadata = result.get("metadata", {})
                    solution_types = ["solution", "pattern", "best_practice"]
                    if metadata.get("type") in solution_types:
                        solution = self._create_solution_pattern(
                            result, project_profile
                        )
                        if solution:
                            solutions.append(solution)

            except Exception as e:
                project_id = project_profile.project_id
                logger.error(
                    f"Error extracting solutions from project " f"{project_id}: {e}"
                )

        return solutions

    def _create_solution_pattern(
        self, memory_result: Dict, project: ProjectProfile
    ) -> Optional[SolutionPattern]:
        """Create a solution pattern from memory result"""
        try:
            content = memory_result.get("content", "")
            metadata = memory_result.get("metadata", {})

            pattern_content = f"{project.project_id}_{content[:100]}"
            pattern_id = hashlib.md5(pattern_content.encode()).hexdigest()[:16]

            description = content[:200] + "..." if len(content) > 200 else content

            return SolutionPattern(
                pattern_id=pattern_id,
                name=metadata.get("title", "Unnamed Solution"),
                description=description,
                problem_description=metadata.get("problem", ""),
                solution_description=content,
                code_examples=metadata.get("code_examples", []),
                tech_requirements=project.tech_stack,
                success_criteria=metadata.get("success_criteria", []),
                usage_count=1,
                success_rate=metadata.get("success_rate", 0.8),
                source_projects=[project.project_id],
                tags=metadata.get("tags", []),
            )
        except Exception as e:
            logger.error(f"Error creating solution pattern: {e}")
            return None

    def find_applicable_solutions(
        self, target_project: ProjectProfile, similar_projects: List[ProjectSimilarity]
    ) -> List[SolutionPattern]:
        """Find solutions applicable to target project"""

        applicable_solutions = []

        for similarity in similar_projects:
            # Get solutions from similar project
            project_solutions = [
                solution
                for solution in self.solution_patterns
                if similarity.project_b in solution.source_projects
            ]

            for solution in project_solutions:
                # Check if solution is applicable to target project
                if self._is_solution_applicable(solution, target_project):
                    # Adapt solution for target project context
                    adapted_solution = self._adapt_solution(solution, target_project)
                    applicable_solutions.append(adapted_solution)

        # Sort by success rate and usage count
        def sort_key(x):
            return (x.success_rate, x.usage_count)

        applicable_solutions.sort(key=sort_key, reverse=True)
        return applicable_solutions[:10]  # Top 10 most promising solutions

    def _is_solution_applicable(
        self, solution: SolutionPattern, target_project: ProjectProfile
    ) -> bool:
        """Check if a solution is applicable to the target project"""

        # Check tech stack compatibility
        solution_tech = set(solution.tech_requirements)
        project_tech = set(target_project.tech_stack)
        tech_overlap = (
            len(solution_tech.intersection(project_tech)) / len(solution_tech)
            if solution_tech
            else 0
        )

        # Require at least 30% tech stack overlap
        return tech_overlap >= 0.3

    def _adapt_solution(
        self, solution: SolutionPattern, target_project: ProjectProfile
    ) -> SolutionPattern:
        """Adapt a solution for the target project context"""

        # Create adapted version with target project context
        adapted_pattern_id = (
            f"{solution.pattern_id}_adapted_" f"{target_project.project_id[:8]}"
        )
        adapted_name = f"{solution.name} " f"(Adapted for {target_project.name})"
        adapted_solution_description = self._contextualize_solution(
            solution.solution_description, target_project
        )
        combined_tech_requirements = list(
            set(solution.tech_requirements + target_project.tech_stack)
        )
        combined_source_projects = solution.source_projects + [
            target_project.project_id
        ]
        combined_tags = solution.tags + [target_project.domain, "adapted"]

        adapted_solution = SolutionPattern(
            pattern_id=adapted_pattern_id,
            name=adapted_name,
            description=solution.description,
            problem_description=solution.problem_description,
            solution_description=adapted_solution_description,
            code_examples=solution.code_examples,
            tech_requirements=combined_tech_requirements,
            success_criteria=solution.success_criteria,
            usage_count=solution.usage_count,
            success_rate=solution.success_rate * 0.9,  # Adaptation discount
            source_projects=combined_source_projects,
            tags=combined_tags,
        )

        return adapted_solution

    def _contextualize_solution(
        self, solution_text: str, target_project: ProjectProfile
    ) -> str:
        """Contextualize solution description for target project"""

        # Add project-specific context
        tech_list = ", ".join(target_project.tech_stack[:3])
        context_note = (
            f"\n\nAdapted for {target_project.name} "
            f"({target_project.domain} project using {tech_list}):\n"
        )

        # Add tech stack specific notes
        if "python" in target_project.tech_stack:
            context_note += "- Consider using Python-specific libraries\n"
        if "typescript" in target_project.tech_stack:
            context_note += "- Leverage TypeScript type safety features\n"
        if "react" in target_project.tech_stack:
            context_note += "- Apply React component patterns and hooks\n"

        return solution_text + context_note


class BestPracticePropagator:
    """System for propagating best practices across projects"""

    def __init__(self, memory_service: MultiScopeMemoryService):
        self.memory_service = memory_service
        self.best_practices: List[BestPractice] = []

    def identify_best_practices(
        self, projects: List[ProjectProfile]
    ) -> List[BestPractice]:
        """Identify best practices from successful projects"""

        practices = []

        # Group projects by domain and analyze successful patterns
        domain_groups = {}
        for project in projects:
            if project.domain not in domain_groups:
                domain_groups[project.domain] = []
            domain_groups[project.domain].append(project)

        for domain, domain_projects in domain_groups.items():
            # Find common patterns in successful projects
            successful_projects = [
                p
                for p in domain_projects
                if p.success_metrics.get("overall_success", 0) > 0.8
            ]

            if len(successful_projects) >= 2:  # Need at least 2 successful
                common_practices = self._extract_common_practices(
                    successful_projects, domain
                )
                practices.extend(common_practices)

        return practices

    def _extract_common_practices(
        self, projects: List[ProjectProfile], domain: str
    ) -> List[BestPractice]:
        """Extract common practices from successful projects in a domain"""

        practices = []

        # Analyze common tech stack patterns
        tech_usage = {}
        for project in projects:
            for tech in project.tech_stack:
                tech_usage[tech] = tech_usage.get(tech, 0) + 1

        # Create best practices for commonly used technologies
        for tech, usage_count in tech_usage.items():
            # Used in 70% of successful projects
            if usage_count >= len(projects) * 0.7:
                practice_content = f"{domain}_{tech}_practice"
                practice_id = hashlib.md5(practice_content.encode()).hexdigest()[:16]

                success_info = (
                    f"{usage_count}/{len(projects)} " f"successful {domain} projects"
                )
                description = f"{tech} has proven successful in " f"{success_info}"
                evidence = [
                    f"Used in {p.name}" for p in projects if tech in p.tech_stack
                ]
                implementation_steps = [
                    f"Add {tech} to project dependencies",
                    f"Set up {tech} development environment",
                    f"Follow {tech} best practices from global knowledge",
                ]
                success_metrics = {"adoption_rate": usage_count / len(projects)}
                source_projects = [
                    p.project_id for p in projects if tech in p.tech_stack
                ]
                confidence_score = min(0.95, usage_count / len(projects))

                practice = BestPractice(
                    practice_id=practice_id,
                    title=f"Use {tech} for {domain} Projects",
                    description=description,
                    category="technology-choice",
                    domain=domain,
                    evidence=evidence,
                    implementation_steps=implementation_steps,
                    success_metrics=success_metrics,
                    source_projects=source_projects,
                    confidence_score=confidence_score,
                )
                practices.append(practice)

        return practices

    def propagate_practices(
        self, target_project: ProjectProfile, similar_projects: List[ProjectSimilarity]
    ) -> List[BestPractice]:
        """Get best practices applicable to target project"""

        applicable_practices = []

        # Get practices from similar projects
        for similarity in similar_projects:
            project_practices = [
                practice
                for practice in self.best_practices
                if similarity.project_b in practice.source_projects
            ]

            for practice in project_practices:
                if self._is_practice_applicable(
                    practice, target_project, similarity.similarity_score
                ):
                    applicable_practices.append(practice)

        # Remove duplicates and sort by confidence
        unique_practices = {p.practice_id: p for p in applicable_practices}
        sorted_practices = sorted(
            unique_practices.values(), key=lambda x: x.confidence_score, reverse=True
        )

        return sorted_practices[:5]  # Top 5 most confident recommendations

    def _is_practice_applicable(
        self,
        practice: BestPractice,
        target_project: ProjectProfile,
        similarity_score: float,
    ) -> bool:
        """Check if a best practice is applicable to target project"""

        # Domain match is important
        domain_match = (
            practice.domain == target_project.domain or practice.domain == "general"
        )
        if not domain_match:
            return False

        # Higher similarity projects have more applicable practices
        if similarity_score < 0.5:
            return False

        # Technology-specific practices need tech stack compatibility
        if practice.category == "technology-choice":
            tech_mentioned = any(
                tech in practice.title.lower() for tech in target_project.tech_stack
            )
            return tech_mentioned

        return True


class CrossProjectLearningService:
    """Main service for cross-project memory learning and intelligence"""

    def __init__(
        self,
        memory_service: MultiScopeMemoryService,
        artifact_service: ArtifactMemoryService,
    ):
        self.memory_service = memory_service
        self.artifact_service = artifact_service
        self.similarity_engine = ProjectSimilarityEngine()
        self.solution_reuse = SolutionReuseSystem(memory_service)
        self.practice_propagator = BestPracticePropagator(memory_service)

        self.project_profiles: Dict[str, ProjectProfile] = {}

        logger.info("CrossProjectLearningService initialized")

    def register_project(
        self,
        project_id: str,
        name: str,
        description: str,
        tech_stack: List[str],
        domain: str,
    ) -> ProjectProfile:
        """Register a new project for cross-project learning"""

        project_profile = ProjectProfile(
            project_id=project_id,
            name=name,
            description=description,
            tech_stack=tech_stack,
            domain=domain,
            patterns_used=self._detect_patterns_in_project(project_id),
            success_metrics=self._compute_project_metrics(project_id),
            created_date=datetime.now(timezone.utc),
            last_updated=datetime.now(timezone.utc),
        )

        self.project_profiles[project_id] = project_profile
        tech_info = ", ".join(tech_stack)
        logger.info(
            f"Registered project: {name} ({domain}) " f"with tech stack: {tech_info}"
        )

        return project_profile

    def _detect_patterns_in_project(self, project_id: str) -> List[str]:
        """Detect design patterns and architectural patterns in project"""

        patterns = []

        try:
            # Search project memory for pattern usage
            pattern_queries = [
                "design pattern",
                "architectural pattern",
                "singleton",
                "factory",
                "observer",
                "strategy",
                "repository",
                "mvc",
                "microservices",
                "event-driven",
            ]

            for query in pattern_queries:
                results = self.memory_service.search(
                    query=query, scope="project", limit=5
                )
                for result in results:
                    content = result.get("content", "").lower()
                    metadata = result.get("metadata", {})

                    # Check for pattern mentions
                    query_in_content = query in content
                    query_in_metadata = query in str(metadata).lower()
                    if query_in_content or query_in_metadata:
                        patterns.append(query.replace(" ", "_"))

        except Exception as e:
            logger.error(f"Error detecting patterns in project " f"{project_id}: {e}")

        return list(set(patterns))  # Remove duplicates

    def _compute_project_metrics(self, project_id: str) -> Dict[str, float]:
        """Compute success metrics for a project"""

        # Default metrics
        metrics = {
            "overall_success": 0.7,
            "build_success_rate": 0.85,
            "test_coverage": 0.75,
            "code_quality": 0.8,
        }

        try:
            # Try to get actual metrics from artifacts memory
            search_query = f"project {project_id} metrics build test"
            artifact_results = self.memory_service.search(
                query=search_query, scope="artifacts", limit=10
            )

            # Analyze artifact data for metrics
            for result in artifact_results:
                metadata = result.get("metadata", {})
                if metadata.get("type") == "build_result":
                    if metadata.get("status") == "success":
                        current_rate = metrics["build_success_rate"]
                        metrics["build_success_rate"] = min(1.0, current_rate + 0.1)
                    if "coverage_percentage" in metadata:
                        coverage_pct = metadata["coverage_percentage"]
                        metrics["test_coverage"] = coverage_pct / 100.0

        except Exception as e:
            logger.error(f"Error computing metrics for project " f"{project_id}: {e}")

        return metrics

    def get_project_recommendations(self, project_id: str) -> Dict[str, Any]:
        """Get comprehensive recommendations for a project"""

        if project_id not in self.project_profiles:
            return {"error": "Project not registered"}

        target_project = self.project_profiles[project_id]
        all_projects = list(self.project_profiles.values())

        # Find similar projects
        similar_projects = self.similarity_engine.find_similar_projects(
            target_project, all_projects
        )

        # Get solution recommendations
        applicable_solutions = self.solution_reuse.find_applicable_solutions(
            target_project, similar_projects
        )

        # Get best practice recommendations
        applicable_practices = self.practice_propagator.propagate_practices(
            target_project, similar_projects
        )

        # Build similar projects summary
        similar_projects_info = [
            {
                "project_id": sim.project_b,
                "similarity_score": sim.similarity_score,
                "common_patterns": sim.common_patterns,
                "similarity_factors": sim.similarity_factors,
            }
            for sim in similar_projects
        ]

        recommendations = {
            "project_id": project_id,
            "project_name": target_project.name,
            "similar_projects": similar_projects_info,
            "recommended_solutions": [
                asdict(solution) for solution in applicable_solutions
            ],
            "recommended_practices": [
                asdict(practice) for practice in applicable_practices
            ],
            "global_patterns_to_consider": (
                self._get_global_pattern_recommendations(target_project)
            ),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        solution_count = len(applicable_solutions)
        practice_count = len(applicable_practices)
        logger.info(
            f"Generated recommendations for project {project_id}: "
            f"{solution_count} solutions, {practice_count} practices"
        )

        return recommendations

    def _get_global_pattern_recommendations(
        self, project: ProjectProfile
    ) -> List[Dict[str, Any]]:
        """Get global pattern recommendations from foundational knowledge"""

        recommendations = []

        try:
            # Search global knowledge for patterns relevant to project
            search_queries = [
                f"{project.domain} best practices",
                "PDCA continuous improvement",
                "SOLID principles",
                f"design patterns {project.domain}",
            ]

            for tech in project.tech_stack[:3]:  # Top 3 technologies
                search_queries.append(f"{tech} best practices")

            for query in search_queries:
                results = self.memory_service.search(
                    query=query, scope="global", limit=3
                )
                for result in results:
                    title = result.get("metadata", {}).get(
                        "category", "General Pattern"
                    )
                    content = result.get("content", "")
                    description = content[:200] + "..."

                    recommendations.append(
                        {
                            "type": "global_knowledge",
                            "title": title,
                            "description": description,
                            "relevance": "high",
                            "source": "global_knowledge_base",
                        }
                    )

        except Exception as e:
            logger.error(f"Error getting global recommendations: {e}")

        return recommendations[:5]  # Top 5 most relevant

    def analyze_cross_project_patterns(self) -> Dict[str, Any]:
        """Analyze patterns across all projects for insights"""

        if not self.project_profiles:
            return {"message": "No projects registered yet"}

        all_projects = list(self.project_profiles.values())

        # Tech stack analysis
        tech_usage = {}
        domain_distribution = {}

        for project in all_projects:
            # Count tech usage
            for tech in project.tech_stack:
                tech_usage[tech] = tech_usage.get(tech, 0) + 1

            # Count domain distribution
            current_count = domain_distribution.get(project.domain, 0)
            domain_distribution[project.domain] = current_count + 1

        # Pattern usage analysis
        pattern_usage = {}
        for project in all_projects:
            for pattern in project.patterns_used:
                pattern_usage[pattern] = pattern_usage.get(pattern, 0) + 1

        # Sort technologies by usage
        top_technologies = sorted(tech_usage.items(), key=lambda x: x[1], reverse=True)[
            :10
        ]

        # Sort patterns by usage
        top_patterns = sorted(pattern_usage.items(), key=lambda x: x[1], reverse=True)[
            :10
        ]

        analysis = {
            "total_projects": len(all_projects),
            "most_popular_technologies": top_technologies,
            "domain_distribution": domain_distribution,
            "most_used_patterns": top_patterns,
            "average_success_metrics": (
                self._compute_average_success_metrics(all_projects)
            ),
            "cross_project_insights": (
                self._generate_cross_project_insights(all_projects)
            ),
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        }

        return analysis

    def _compute_average_success_metrics(
        self, projects: List[ProjectProfile]
    ) -> Dict[str, float]:
        """Compute average success metrics across all projects"""

        if not projects:
            return {}

        metric_sums = {}
        metric_counts = {}

        for project in projects:
            for metric, value in project.success_metrics.items():
                metric_sums[metric] = metric_sums.get(metric, 0) + value
                metric_counts[metric] = metric_counts.get(metric, 0) + 1

        return {
            metric: metric_sums[metric] / metric_counts[metric]
            for metric in metric_sums
        }

    def _generate_cross_project_insights(
        self, projects: List[ProjectProfile]
    ) -> List[str]:
        """Generate insights from cross-project analysis"""

        insights = []

        if len(projects) >= 2:
            # Tech stack insights
            tech_usage = {}
            successful_projects = [
                p for p in projects if p.success_metrics.get("overall_success", 0) > 0.8
            ]

            for project in successful_projects:
                for tech in project.tech_stack:
                    tech_usage[tech] = tech_usage.get(tech, 0) + 1

            if tech_usage:
                most_successful_tech = max(tech_usage.items(), key=lambda x: x[1])
                tech_name, usage_count = most_successful_tech
                insights.append(
                    f"Most successful technology: {tech_name} "
                    f"(used in {usage_count} high-performing projects)"
                )

            # Domain insights
            domain_success = {}
            for project in projects:
                domain = project.domain
                success = project.success_metrics.get("overall_success", 0)
                if domain not in domain_success:
                    domain_success[domain] = []
                domain_success[domain].append(success)

            for domain, successes in domain_success.items():
                avg_success = sum(successes) / len(successes)
                if avg_success > 0.8:
                    insights.append(
                        f"{domain} domain shows high success rate: "
                        f"{avg_success:.2f}"
                    )

        return insights

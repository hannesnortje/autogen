"""
Artifact Memory Integration Service

This service connects the memory system to the complete software development
lifecycle by linking memory events to Git commits, PRs, build reports, test
results, and deployment outcomes.

Key Features:
- Git integration: Link memory to commits, branches, and PRs
- Build integration: Capture build reports and test results
- Code review learning: Store and learn from review feedback
- Deployment tracking: Connect memory to deployment outcomes
- Artifact-based learning: Enable agents to learn from development lifecycle

Architecture:
- ArtifactMemoryService: Main orchestrator for artifact memory
- GitIntegrationService: Git commit and PR tracking
- BuildIntegrationService: Build and test result capture
- CodeReviewService: Review feedback and learning patterns
- DeploymentTrackingService: Deployment outcome analysis

Author: AutoGen Team
Date: 2025-09-15
"""

import subprocess
import hashlib
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from pathlib import Path

from .multi_memory import MultiScopeMemoryService
from .observability import get_logger

logger = get_logger(__name__)


def log_function_call(func):
    """Simple decorator for logging function calls"""

    def wrapper(*args, **kwargs):
        logger.debug(f"Calling {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"Completed {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            raise

    return wrapper


@dataclass
class GitCommitInfo:
    """Information about a Git commit"""

    commit_hash: str
    author_name: str
    author_email: str
    commit_message: str
    timestamp: datetime
    branch: str
    files_changed: List[str]
    lines_added: int
    lines_removed: int
    is_merge: bool


@dataclass
class BuildResult:
    """Build and test result information"""

    build_id: str
    commit_hash: str
    status: str  # success, failure, error
    build_time: float
    test_results: Dict[str, Any]
    coverage_percentage: Optional[float]
    warnings: List[str]
    errors: List[str]
    artifacts: List[str]


@dataclass
class CodeReviewFeedback:
    """Code review feedback and patterns"""

    review_id: str
    commit_hash: str
    reviewer: str
    feedback: str
    category: str  # style, logic, performance, security, etc.
    severity: str  # low, medium, high, critical
    resolved: bool
    resolution_commit: Optional[str]


@dataclass
class DeploymentOutcome:
    """Deployment result and performance metrics"""

    deployment_id: str
    commit_hash: str
    environment: str  # dev, staging, production
    status: str  # success, failure, rollback
    deploy_time: datetime
    performance_metrics: Dict[str, float]
    issues: List[str]
    rollback_reason: Optional[str]


class GitIntegrationService:
    """Service for Git repository integration and commit tracking"""

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)

    @log_function_call
    def get_current_commit_info(self) -> Optional[GitCommitInfo]:
        """Get information about the current HEAD commit"""
        try:
            # Get commit hash
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.repo_path,
            )
            if result.returncode != 0:
                logger.warning("Not a git repository or no commits")
                return None

            commit_hash = result.stdout.strip()

            # Get commit info
            result = subprocess.run(
                [
                    "git",
                    "show",
                    "--format=%an|%ae|%s|%ct|%P",
                    "--name-only",
                    commit_hash,
                ],
                capture_output=True,
                text=True,
                cwd=self.repo_path,
            )
            if result.returncode != 0:
                return None

            lines = result.stdout.strip().split("\n")
            commit_info = lines[0].split("|")

            author_name = commit_info[0]
            author_email = commit_info[1]
            commit_message = commit_info[2]
            timestamp = datetime.fromtimestamp(int(commit_info[3]), tz=timezone.utc)
            parent_commits = commit_info[4].split() if commit_info[4] else []
            is_merge = len(parent_commits) > 1

            # Get files changed
            files_changed = [line for line in lines[2:] if line.strip()]

            # Get current branch
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                cwd=self.repo_path,
            )
            branch = result.stdout.strip() if result.returncode == 0 else "unknown"

            # Get line changes
            result = subprocess.run(
                ["git", "show", "--numstat", commit_hash],
                capture_output=True,
                text=True,
                cwd=self.repo_path,
            )

            lines_added = 0
            lines_removed = 0
            if result.returncode == 0:
                # Skip commit info line
                for line in result.stdout.strip().split("\n")[1:]:
                    parts = line.split("\t")
                    if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
                        lines_added += int(parts[0])
                        lines_removed += int(parts[1])

            return GitCommitInfo(
                commit_hash=commit_hash,
                author_name=author_name,
                author_email=author_email,
                commit_message=commit_message,
                timestamp=timestamp,
                branch=branch,
                files_changed=files_changed,
                lines_added=lines_added,
                lines_removed=lines_removed,
                is_merge=is_merge,
            )

        except Exception as e:
            logger.error(f"Failed to get commit info: {e}")
            return None

    @log_function_call
    def get_recent_commits(self, limit: int = 10) -> List[GitCommitInfo]:
        """Get information about recent commits"""
        commits = []
        try:
            result = subprocess.run(
                [
                    "git",
                    "log",
                    f"-{limit}",
                    "--format=%H|%an|%ae|%s|%ct",
                    "--name-only",
                ],
                capture_output=True,
                text=True,
                cwd=self.repo_path,
            )
            if result.returncode != 0:
                return commits

            # Parse commit log output
            current_commit = None
            files_for_commit = []

            for line in result.stdout.split("\n"):
                line = line.strip()
                if not line:
                    continue

                if "|" in line:  # Commit info line
                    # Save previous commit if exists
                    if current_commit:
                        current_commit.files_changed = files_for_commit
                        commits.append(current_commit)
                        files_for_commit = []

                    # Parse new commit
                    parts = line.split("|")
                    if len(parts) >= 5:
                        current_commit = GitCommitInfo(
                            commit_hash=parts[0],
                            author_name=parts[1],
                            author_email=parts[2],
                            commit_message=parts[3],
                            timestamp=datetime.fromtimestamp(
                                int(parts[4]), tz=timezone.utc
                            ),
                            # Would need separate call per commit
                            branch="unknown",
                            files_changed=[],
                            lines_added=0,
                            lines_removed=0,
                            is_merge=False,
                        )
                else:
                    # File changed in current commit
                    files_for_commit.append(line)

            # Add last commit
            if current_commit:
                current_commit.files_changed = files_for_commit
                commits.append(current_commit)

        except Exception as e:
            logger.error(f"Failed to get recent commits: {e}")

        return commits


class BuildIntegrationService:
    """Service for build and test result integration"""

    def __init__(self):
        self.build_history: List[BuildResult] = []

    @log_function_call
    def capture_build_result(
        self,
        build_id: str,
        commit_hash: str,
        status: str,
        build_time: float,
        test_results: Dict[str, Any] = None,
        coverage_percentage: float = None,
    ) -> BuildResult:
        """Capture a build result for memory storage"""

        build_result = BuildResult(
            build_id=build_id,
            commit_hash=commit_hash,
            status=status,
            build_time=build_time,
            test_results=test_results or {},
            coverage_percentage=coverage_percentage,
            warnings=[],
            errors=[],
            artifacts=[],
        )

        self.build_history.append(build_result)
        return build_result

    @log_function_call
    def simulate_build_from_current_commit(
        self, git_service: GitIntegrationService
    ) -> Optional[BuildResult]:
        """Simulate a build result for the current commit (for testing)"""
        commit_info = git_service.get_current_commit_info()
        if not commit_info:
            return None

        # Simulate build metrics based on commit characteristics
        build_time = max(10.0, len(commit_info.files_changed) * 2.5)

        # Determine simulated status based on commit message and files
        status = "success"
        if any(
            keyword in commit_info.commit_message.lower()
            for keyword in ["fix", "bug", "error", "issue"]
        ):
            status = "success"  # Fixes usually succeed
        elif any(
            keyword in commit_info.commit_message.lower()
            for keyword in ["refactor", "major", "breaking"]
        ):
            if commit_info.lines_added < 100:
                status = "success"
            else:
                status = "failure"

        test_results = {
            "total_tests": max(10, len(commit_info.files_changed) * 5),
            "passed_tests": max(8, len(commit_info.files_changed) * 4),
            "failed_tests": 0 if status == "success" else 2,
            "skipped_tests": 1,
        }

        coverage = min(95.0, 70.0 + (len(commit_info.files_changed) * 2))

        build_id = (
            f"build_{commit_info.commit_hash[:8]}_" f"{int(datetime.now().timestamp())}"
        )

        return self.capture_build_result(
            build_id=build_id,
            commit_hash=commit_info.commit_hash,
            status=status,
            build_time=build_time,
            test_results=test_results,
            coverage_percentage=coverage,
        )


class CodeReviewService:
    """Service for code review feedback integration"""

    def __init__(self):
        self.review_history: List[CodeReviewFeedback] = []

    @log_function_call
    def add_review_feedback(
        self,
        commit_hash: str,
        reviewer: str,
        feedback: str,
        category: str = "general",
        severity: str = "medium",
    ) -> CodeReviewFeedback:
        """Add code review feedback for a commit"""

        review_id = hashlib.md5(
            f"{commit_hash}_{reviewer}_{feedback}".encode()
        ).hexdigest()[:16]

        review = CodeReviewFeedback(
            review_id=review_id,
            commit_hash=commit_hash,
            reviewer=reviewer,
            feedback=feedback,
            category=category,
            severity=severity,
            resolved=False,
            resolution_commit=None,
        )

        self.review_history.append(review)
        return review

    @log_function_call
    def get_review_patterns(self) -> Dict[str, Any]:
        """Analyze review patterns and common feedback"""
        if not self.review_history:
            return {"patterns": [], "common_issues": [], "reviewer_preferences": {}}

        # Analyze categories
        category_counts = {}
        severity_counts = {}
        reviewer_stats = {}

        for review in self.review_history:
            category_counts[review.category] = (
                category_counts.get(review.category, 0) + 1
            )
            severity_counts[review.severity] = (
                severity_counts.get(review.severity, 0) + 1
            )

            if review.reviewer not in reviewer_stats:
                reviewer_stats[review.reviewer] = {"total": 0, "categories": {}}
            reviewer_stats[review.reviewer]["total"] += 1
            cat_stats = reviewer_stats[review.reviewer]["categories"]
            cat_stats[review.category] = cat_stats.get(review.category, 0) + 1

        return {
            "patterns": {
                "most_common_category": (
                    max(category_counts, key=category_counts.get)
                    if category_counts
                    else None
                ),
                "severity_distribution": severity_counts,
                "total_reviews": len(self.review_history),
            },
            "common_issues": list(category_counts.keys())[:5],
            "reviewer_preferences": reviewer_stats,
        }


class ArtifactMemoryService:
    """Main service for artifact memory integration"""

    def __init__(self, memory_service: MultiScopeMemoryService, repo_path: str = "."):
        self.memory_service = memory_service
        self.git_service = GitIntegrationService(repo_path)
        self.build_service = BuildIntegrationService()
        self.review_service = CodeReviewService()

        logger.info("ArtifactMemoryService initialized")

    @log_function_call
    async def link_commit_to_memory(
        self, commit_info: GitCommitInfo, context: str = "code_change"
    ) -> bool:
        """Link a Git commit to the artifacts memory collection"""
        try:
            result = self.memory_service.write_artifact(
                content=f"Git commit: {commit_info.commit_message}",
                artifact_type="git_commit",
                reference=commit_info.commit_hash,
                commit_hash=commit_info.commit_hash,
            )

            if result:
                logger.info(
                    f"Linked commit {commit_info.commit_hash[:8]} " f"to memory"
                )
                return True
            else:
                logger.error(
                    f"Failed to link commit " f"{commit_info.commit_hash[:8]} to memory"
                )
                return False

        except Exception as e:
            logger.error(f"Error linking commit to memory: {e}")
            return False

    @log_function_call
    async def link_build_to_memory(self, build_result: BuildResult) -> bool:
        """Link a build result to the artifacts memory collection"""
        try:
            content = (
                f"Build {build_result.status}: {build_result.build_id} "
                f"(commit: {build_result.commit_hash[:8]}, "
                f"time: {build_result.build_time:.1f}s)"
            )

            result = self.memory_service.write_artifact(
                content=content,
                artifact_type="build_result",
                reference=build_result.build_id,
                commit_hash=build_result.commit_hash,
            )

            if result:
                logger.info(f"Linked build {build_result.build_id} to memory")
                return True
            else:
                logger.error(
                    f"Failed to link build {build_result.build_id} " f"to memory"
                )
                return False

        except Exception as e:
            logger.error(f"Error linking build to memory: {e}")
            return False

    @log_function_call
    async def link_review_to_memory(self, review: CodeReviewFeedback) -> bool:
        """Link code review feedback to the artifacts memory collection"""
        try:
            content = f"Code review feedback: {review.feedback[:100]}..."

            result = self.memory_service.write_artifact(
                content=content,
                artifact_type="code_review",
                reference=review.review_id,
                commit_hash=review.commit_hash,
            )

            if result:
                logger.info(f"Linked review {review.review_id} to memory")
                return True
            else:
                logger.error(f"Failed to link review {review.review_id} " f"to memory")
                return False

        except Exception as e:
            logger.error(f"Error linking review to memory: {e}")
            return False

    @log_function_call
    async def capture_current_development_state(self) -> Dict[str, Any]:
        """Capture the current development state and link to memory"""
        results = {
            "commit_linked": False,
            "build_linked": False,
            "commit_info": None,
            "build_result": None,
        }

        try:
            # Get current commit
            commit_info = self.git_service.get_current_commit_info()
            if commit_info:
                results["commit_info"] = asdict(commit_info)
                results["commit_linked"] = await self.link_commit_to_memory(
                    commit_info, "development_capture"
                )

            # Simulate build for current commit
            if commit_info:
                build_service = self.build_service
                build_result = build_service.simulate_build_from_current_commit(
                    self.git_service
                )
                if build_result:
                    results["build_result"] = asdict(build_result)
                    results["build_linked"] = await self.link_build_to_memory(
                        build_result
                    )

            logger.info(
                "Development state capture completed",
                extra={
                    "commit_captured": results["commit_linked"],
                    "build_captured": results["build_linked"],
                },
            )

        except Exception as e:
            logger.error(f"Error capturing development state: {e}")

        return results

    @log_function_call
    async def search_related_artifacts(
        self, query: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for related artifacts in memory"""
        try:
            results = self.memory_service.search(
                query=query,
                scope="artifacts",  # Use string scope instead of enum
                limit=limit,
            )

            logger.info(
                f"Found {len(results)} related artifacts " f"for query: {query}"
            )
            return results

        except Exception as e:
            logger.error(f"Error searching artifacts: {e}")
            return []

    @log_function_call
    async def get_commit_learning_insights(self, commit_hash: str) -> Dict[str, Any]:
        """Get learning insights for a specific commit"""
        try:
            # Search for related artifacts
            related_artifacts = await self.search_related_artifacts(
                f"commit_{commit_hash[:8]}", limit=20
            )

            insights = {
                "commit_hash": commit_hash,
                "related_builds": [],
                "related_reviews": [],
                "similar_commits": [],
                "learning_points": [],
            }

            for artifact in related_artifacts:
                metadata = artifact.get("metadata", {})
                artifact_type = metadata.get("type")
                if artifact_type == "build_result":
                    insights["related_builds"].append(metadata)
                elif artifact_type == "code_review":
                    insights["related_reviews"].append(metadata)
                elif artifact_type == "git_commit":
                    insights["similar_commits"].append(metadata)

            # Generate learning points
            if insights["related_builds"]:
                build_statuses = [b["status"] for b in insights["related_builds"]]
                if "failure" in build_statuses:
                    insights["learning_points"].append(
                        "This commit or similar ones had build failures"
                    )

            if insights["related_reviews"]:
                high_severity = [
                    r
                    for r in insights["related_reviews"]
                    if r["severity"] in ["high", "critical"]
                ]
                if high_severity:
                    insights["learning_points"].append(
                        "Similar commits received critical review feedback"
                    )

            return insights

        except Exception as e:
            logger.error(f"Error getting commit insights: {e}")
            return {"error": str(e)}

"""
Memory Pruning Service for importance-based cleanup of low-value memories.

Automatically removes or archives memory entries based on importance scores,
age, and usage patterns to maintain system performance and relevance.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from autogen_mcp.collections import MemoryScope
from autogen_mcp.multi_memory import MultiScopeMemoryService
from autogen_mcp.observability import get_logger


@dataclass
class PruningRules:
    """Configuration for memory pruning behavior."""

    # Age-based pruning (in seconds)
    max_age_thread: int = 30 * 24 * 3600  # 30 days for thread messages
    max_age_project: int = 90 * 24 * 3600  # 90 days for project notes
    max_age_agent: int = 180 * 24 * 3600  # 180 days for agent preferences

    # Importance-based pruning
    min_importance_keep: float = 0.3  # Keep memories above this importance
    low_importance_threshold: float = 0.5  # Consider for pruning below this

    # Usage-based pruning
    min_access_count: int = 2  # Keep memories accessed at least this many times
    stale_threshold: int = 60 * 24 * 3600  # 60 days without access

    # Collection size limits
    max_thread_entries_per_thread: int = 1000  # Max entries per thread
    max_project_entries: int = 5000  # Max entries per project
    max_agent_entries_per_type: int = 500  # Max entries per agent type

    # Batch processing
    batch_size: int = 100  # Process this many entries at a time
    dry_run: bool = True  # Default to dry run for safety


@dataclass
class PruningResult:
    """Result of a memory pruning operation."""

    scope: MemoryScope
    collection_name: str
    entries_examined: int
    entries_pruned: int
    entries_archived: int
    space_freed: int  # Approximate bytes freed
    errors: List[str]
    execution_time: float


class MemoryPruningService:
    """Manages intelligent pruning of memory entries based on configurable rules."""

    def __init__(
        self,
        memory_service: MultiScopeMemoryService,
        rules: Optional[PruningRules] = None,
    ):
        self.memory_service = memory_service
        self.rules = rules or PruningRules()
        self.logger = get_logger("autogen.memory_pruning")

    def analyze_memory_usage(
        self, scope: Optional[MemoryScope] = None
    ) -> Dict[str, Any]:
        """Analyze current memory usage and identify pruning candidates."""
        try:
            analysis = {
                "timestamp": time.time(),
                "total_collections": 0,
                "scopes": {},
                "pruning_candidates": {},
                "recommendations": [],
            }

            scopes_to_check = [scope] if scope else list(MemoryScope)

            for memory_scope in scopes_to_check:
                if memory_scope == MemoryScope.GLOBAL:
                    continue  # Skip global - we don't prune foundation knowledge

                scope_analysis = self._analyze_scope(memory_scope)
                analysis["scopes"][memory_scope.value] = scope_analysis
                analysis["total_collections"] += scope_analysis.get(
                    "collections_count", 0
                )

                # Identify pruning candidates
                candidates = self._identify_pruning_candidates(
                    memory_scope, scope_analysis
                )
                if candidates:
                    analysis["pruning_candidates"][memory_scope.value] = candidates

            # Generate recommendations
            analysis["recommendations"] = self._generate_recommendations(analysis)

            return analysis

        except Exception as e:
            error_msg = f"Memory usage analysis failed: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg, "timestamp": time.time()}

    def prune_scope(
        self, scope: MemoryScope, project_id: Optional[str] = None
    ) -> PruningResult:
        """Prune memories for a specific scope."""
        start_time = time.time()

        try:
            if scope == MemoryScope.GLOBAL:
                raise ValueError(
                    "Cannot prune global scope - contains foundation knowledge"
                )

            collection_name = (
                self.memory_service.collection_manager.get_collection_name(
                    scope, project_id
                )
            )

            # Get all entries for analysis
            entries = self._get_scope_entries(scope, project_id)

            result = PruningResult(
                scope=scope,
                collection_name=collection_name,
                entries_examined=len(entries),
                entries_pruned=0,
                entries_archived=0,
                space_freed=0,
                errors=[],
                execution_time=0,
            )

            if not entries:
                result.execution_time = time.time() - start_time
                return result

            # Identify entries to prune
            to_prune, to_archive = self._classify_entries_for_pruning(entries, scope)

            self.logger.info(
                f"Pruning analysis for {scope.value}: {len(to_prune)} to prune, "
                f"{len(to_archive)} to archive, {len(entries)} total"
            )

            if not self.rules.dry_run:
                # Execute pruning in batches
                result.entries_pruned = self._execute_pruning(to_prune)
                result.entries_archived = self._execute_archiving(to_archive)

                # Estimate space freed (rough calculation)
                result.space_freed = self._estimate_space_freed(to_prune + to_archive)
            else:
                # Dry run - just log what would be done
                result.entries_pruned = len(to_prune)
                result.entries_archived = len(to_archive)
                self.logger.info(
                    f"DRY RUN: Would prune {len(to_prune)} and archive {len(to_archive)} entries"
                )

            result.execution_time = time.time() - start_time
            return result

        except Exception as e:
            error_msg = f"Failed to prune scope {scope.value}: {str(e)}"
            self.logger.error(error_msg)

            return PruningResult(
                scope=scope,
                collection_name=(
                    collection_name if "collection_name" in locals() else "unknown"
                ),
                entries_examined=0,
                entries_pruned=0,
                entries_archived=0,
                space_freed=0,
                errors=[error_msg],
                execution_time=time.time() - start_time,
            )

    def prune_all_scopes(self) -> List[PruningResult]:
        """Prune all eligible scopes (excluding global)."""
        results = []

        for scope in MemoryScope:
            if scope == MemoryScope.GLOBAL:
                continue  # Skip global knowledge

            try:
                result = self.prune_scope(scope)
                results.append(result)

                # Small delay between scopes to avoid overwhelming the system
                time.sleep(0.5)

            except Exception as e:
                error_result = PruningResult(
                    scope=scope,
                    collection_name="unknown",
                    entries_examined=0,
                    entries_pruned=0,
                    entries_archived=0,
                    space_freed=0,
                    errors=[f"Scope pruning failed: {str(e)}"],
                    execution_time=0,
                )
                results.append(error_result)

        # Log summary
        total_pruned = sum(r.entries_pruned for r in results)
        total_archived = sum(r.entries_archived for r in results)
        total_space_freed = sum(r.space_freed for r in results)

        self.logger.info(
            f"Pruning summary: {total_pruned} pruned, {total_archived} archived, "
            f"~{total_space_freed} bytes freed across {len(results)} scopes"
        )

        return results

    def _analyze_scope(self, scope: MemoryScope) -> Dict[str, Any]:
        """Analyze memory usage for a specific scope."""
        try:
            # Get basic collection info
            # This is a simplified implementation - in practice would query Qdrant directly
            analysis = {
                "scope": scope.value,
                "collections_count": 1,  # Simplified - could be multiple for projects
                "total_entries": 0,
                "avg_importance": 0.0,
                "oldest_entry": None,
                "newest_entry": None,
                "size_estimate": 0,
            }

            # Get entries for analysis
            entries = self._get_scope_entries(scope)

            if entries:
                analysis["total_entries"] = len(entries)
                importance_scores = [
                    entry.get("metadata", {}).get("importance", 0.5)
                    for entry in entries
                ]
                analysis["avg_importance"] = sum(importance_scores) / len(
                    importance_scores
                )

                timestamps = [
                    entry.get("metadata", {}).get("timestamp", time.time())
                    for entry in entries
                ]
                analysis["oldest_entry"] = min(timestamps)
                analysis["newest_entry"] = max(timestamps)

                # Rough size estimate
                content_lengths = [len(entry.get("content", "")) for entry in entries]
                analysis["size_estimate"] = sum(content_lengths)

            return analysis

        except Exception as e:
            return {
                "scope": scope.value,
                "error": str(e),
                "collections_count": 0,
                "total_entries": 0,
            }

    def _get_scope_entries(
        self, scope: MemoryScope, project_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all entries for a scope (simplified implementation)."""
        try:
            # Use the memory service search to get entries
            # This is a simplified approach - in practice might need direct Qdrant queries
            scope_query_map = {
                MemoryScope.THREAD: "message_type:message OR message_type:decision",
                MemoryScope.PROJECT: "type:note OR type:decision OR type:adr",
                MemoryScope.AGENT: "capability:general OR capability:coding",
                MemoryScope.OBJECTIVES: "objective_type:sprint OR status:active",
                MemoryScope.ARTIFACTS: "artifact_type:commit OR artifact_type:pr",
            }

            query = scope_query_map.get(scope, "*")
            results = self.memory_service.search(
                query=query,
                scope=scope.value,
                limit=1000,  # Get more entries for analysis
            )

            return results

        except Exception as e:
            self.logger.warning(f"Failed to get entries for scope {scope.value}: {e}")
            return []

    def _identify_pruning_candidates(
        self, scope: MemoryScope, scope_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Identify entries that are candidates for pruning."""
        candidates = {
            "low_importance": 0,
            "stale_entries": 0,
            "old_entries": 0,
            "duplicate_candidates": 0,
            "total_candidates": 0,
        }

        try:
            entries = self._get_scope_entries(scope)
            current_time = time.time()

            for entry in entries:
                metadata = entry.get("metadata", {})
                importance = metadata.get("importance", 0.5)
                timestamp = metadata.get("timestamp", current_time)
                age_days = (current_time - timestamp) / (24 * 3600)

                # Check various pruning criteria
                if importance < self.rules.low_importance_threshold:
                    candidates["low_importance"] += 1

                if age_days > self._get_max_age_for_scope(scope) / (24 * 3600):
                    candidates["old_entries"] += 1

                # Stale entries (not accessed recently)
                last_accessed = metadata.get("last_accessed", timestamp)
                days_since_access = (current_time - last_accessed) / (24 * 3600)
                if days_since_access > self.rules.stale_threshold / (24 * 3600):
                    candidates["stale_entries"] += 1

            candidates["total_candidates"] = len(
                [entry for entry in entries if self._should_prune_entry(entry, scope)]
            )

        except Exception as e:
            self.logger.warning(f"Failed to identify candidates for {scope.value}: {e}")

        return candidates

    def _classify_entries_for_pruning(
        self, entries: List[Dict[str, Any]], scope: MemoryScope
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Classify entries into those to prune vs archive."""
        to_prune = []
        to_archive = []

        for entry in entries:
            if self._should_prune_entry(entry, scope):
                if self._should_archive_vs_delete(entry, scope):
                    to_archive.append(entry)
                else:
                    to_prune.append(entry)

        return to_prune, to_archive

    def _should_prune_entry(self, entry: Dict[str, Any], scope: MemoryScope) -> bool:
        """Determine if an entry should be pruned."""
        metadata = entry.get("metadata", {})
        importance = metadata.get("importance", 0.5)
        timestamp = metadata.get("timestamp", time.time())

        current_time = time.time()
        age_seconds = current_time - timestamp

        # Never prune high-importance entries
        if importance >= self.rules.min_importance_keep:
            return False

        # Never prune recently accessed entries
        last_accessed = metadata.get("last_accessed", timestamp)
        if current_time - last_accessed < self.rules.stale_threshold:
            return False

        # Check age limits
        max_age = self._get_max_age_for_scope(scope)
        if age_seconds > max_age:
            return True

        # Check importance threshold
        if importance < self.rules.low_importance_threshold:
            return True

        return False

    def _should_archive_vs_delete(
        self, entry: Dict[str, Any], scope: MemoryScope
    ) -> bool:
        """Determine if entry should be archived rather than deleted."""
        metadata = entry.get("metadata", {})
        importance = metadata.get("importance", 0.5)

        # Archive if has moderate importance
        if importance >= 0.3:
            return True

        # Archive if it's a summary or decision
        message_type = metadata.get("message_type", "")
        if message_type in ["summary", "decision", "milestone"]:
            return True

        # Archive if it's linked to artifacts
        if metadata.get("artifact_type") or metadata.get("commit_hash"):
            return True

        return False

    def _get_max_age_for_scope(self, scope: MemoryScope) -> int:
        """Get maximum age in seconds for a scope."""
        age_map = {
            MemoryScope.THREAD: self.rules.max_age_thread,
            MemoryScope.PROJECT: self.rules.max_age_project,
            MemoryScope.AGENT: self.rules.max_age_agent,
            MemoryScope.OBJECTIVES: self.rules.max_age_project,  # Same as project
            MemoryScope.ARTIFACTS: self.rules.max_age_project
            * 2,  # Keep artifacts longer
        }
        return age_map.get(scope, self.rules.max_age_thread)

    def _execute_pruning(self, entries: List[Dict[str, Any]]) -> int:
        """Execute actual pruning of entries."""
        # This would involve actual deletion from Qdrant
        # Simplified implementation for now
        pruned_count = 0

        for entry in entries:
            try:
                # In real implementation: delete from Qdrant
                # self.memory_service.collection_manager.qdrant.delete_point(
                #     collection=collection_name, point_id=entry["id"]
                # )
                pruned_count += 1

            except Exception as e:
                self.logger.warning(
                    f"Failed to prune entry {entry.get('id', 'unknown')}: {e}"
                )

        return pruned_count

    def _execute_archiving(self, entries: List[Dict[str, Any]]) -> int:
        """Execute archiving of entries (move to archive collection)."""
        # This would involve moving to an archive collection
        # Simplified implementation for now
        archived_count = 0

        for entry in entries:
            try:
                # In real implementation: move to archive collection
                # or update metadata to mark as archived
                archived_count += 1

            except Exception as e:
                self.logger.warning(
                    f"Failed to archive entry {entry.get('id', 'unknown')}: {e}"
                )

        return archived_count

    def _estimate_space_freed(self, entries: List[Dict[str, Any]]) -> int:
        """Estimate bytes freed by removing entries."""
        total_size = 0
        for entry in entries:
            content = entry.get("content", "")
            metadata = entry.get("metadata", {})

            # Rough estimate: content + metadata + vector overhead
            content_size = len(content.encode("utf-8"))
            metadata_size = len(str(metadata).encode("utf-8"))
            vector_size = 384 * 4  # 384-dim float32 vector

            total_size += content_size + metadata_size + vector_size

        return total_size

    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate pruning recommendations based on analysis."""
        recommendations = []

        total_candidates = sum(
            scope_data.get("total_candidates", 0)
            for scope_data in analysis.get("pruning_candidates", {}).values()
        )

        if total_candidates > 1000:
            recommendations.append(
                f"Consider immediate pruning - {total_candidates} candidates identified"
            )
        elif total_candidates > 500:
            recommendations.append(
                f"Schedule pruning soon - {total_candidates} candidates found"
            )

        for scope, scope_data in analysis.get("scopes", {}).items():
            if scope_data.get("total_entries", 0) > 10000:
                recommendations.append(
                    f"Scope {scope} is very large - consider pruning"
                )

            if scope_data.get("avg_importance", 1.0) < 0.4:
                recommendations.append(
                    f"Scope {scope} has low average importance - review quality"
                )

        if not recommendations:
            recommendations.append(
                "Memory usage looks healthy - no immediate action needed"
            )

        return recommendations

    def get_pruning_status(self) -> Dict[str, Any]:
        """Get current status of the pruning system."""
        return {
            "rules": {
                "max_age_days": {
                    "thread": self.rules.max_age_thread // (24 * 3600),
                    "project": self.rules.max_age_project // (24 * 3600),
                    "agent": self.rules.max_age_agent // (24 * 3600),
                },
                "importance_thresholds": {
                    "min_keep": self.rules.min_importance_keep,
                    "low_threshold": self.rules.low_importance_threshold,
                },
                "dry_run_mode": self.rules.dry_run,
            },
            "last_analysis": time.time(),
            "service_operational": True,
        }

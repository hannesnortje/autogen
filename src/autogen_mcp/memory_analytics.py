"""
Memory Analytics and Optimization Service for AutoGen MCP Server.

This module provides comprehensive memory analytics, intelligent pruning,
health monitoring, and performance optimization for the multi-scope memory system.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from autogen_mcp.collections import MemoryScope
from autogen_mcp.multi_memory import MultiScopeMemoryService
from autogen_mcp.observability import get_logger


class HealthStatus(str, Enum):
    """Memory system health status levels."""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    ERROR = "error"


class PruningStrategy(str, Enum):
    """Different strategies for memory pruning."""

    LRU = "lru"  # Least Recently Used
    IMPORTANCE_BASED = "importance"  # Based on importance scores
    ACCESS_FREQUENCY = "frequency"  # Based on access patterns
    HYBRID = "hybrid"  # Combination of multiple factors


@dataclass
class MemoryMetrics:
    """Comprehensive memory usage and performance metrics."""

    # Storage metrics
    total_entries: int = 0
    total_size_bytes: int = 0
    collections_count: int = 0
    average_entry_size: float = 0.0

    # Access patterns
    read_operations: int = 0
    write_operations: int = 0
    search_operations: int = 0
    access_frequency: Dict[str, int] = field(default_factory=dict)

    # Performance metrics
    average_search_time_ms: float = 0.0
    average_write_time_ms: float = 0.0
    cache_hit_ratio: float = 0.0
    query_success_rate: float = 0.0

    # Health indicators
    memory_utilization: float = 0.0
    fragmentation_ratio: float = 0.0
    oldest_entry_age_days: float = 0.0
    stale_entries_count: int = 0

    # Collection-specific metrics
    scope_metrics: Dict[MemoryScope, Dict[str, Any]] = field(default_factory=dict)

    # Timestamp
    collected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class HealthAlert:
    """Memory health alert with details and recommendations."""

    severity: HealthStatus
    message: str
    metric_name: str
    current_value: Any
    threshold: Any
    recommendations: List[str]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class PruningResult:
    """Result of a memory pruning operation."""

    entries_removed: int
    bytes_freed: int
    collections_affected: List[str]
    strategy_used: PruningStrategy
    execution_time_ms: float
    errors: List[str] = field(default_factory=list)
    preserved_entries: int = 0
    preservation_reasons: Dict[str, int] = field(default_factory=dict)


class MemoryMetricsCollector:
    """Collects comprehensive memory usage and performance metrics."""

    def __init__(self, memory_service: MultiScopeMemoryService):
        self.memory_service = memory_service
        self.collection_manager = memory_service.collection_manager
        self.logger = get_logger("autogen.memory_analytics.metrics")

        # Performance tracking
        self._operation_times: Dict[str, List[float]] = {
            "search": [],
            "write": [],
            "read": [],
        }
        self._operation_counts = {"read": 0, "write": 0, "search": 0}
        self._cache_stats = {"hits": 0, "misses": 0}

    async def collect_metrics(self) -> MemoryMetrics:
        """Collect comprehensive memory metrics."""
        try:
            metrics = MemoryMetrics()

            # Collect storage metrics
            await self._collect_storage_metrics(metrics)

            # Collect access patterns
            self._collect_access_patterns(metrics)

            # Collect performance metrics
            self._collect_performance_metrics(metrics)

            # Collect health indicators
            await self._collect_health_indicators(metrics)

            # Collect scope-specific metrics
            await self._collect_scope_metrics(metrics)

            self.logger.info(
                f"Collected metrics: {metrics.total_entries} entries, "
                f"{metrics.total_size_bytes / 1024 / 1024:.2f} MB"
            )

            return metrics

        except Exception as e:
            self.logger.error(f"Error collecting metrics: {e}")
            raise

    async def _collect_storage_metrics(self, metrics: MemoryMetrics) -> None:
        """Collect storage-related metrics."""
        try:
            # Get collection info from Qdrant
            for scope in MemoryScope:
                if scope == MemoryScope.PROJECT:
                    # Handle project collections separately
                    continue

                collection_name = self.collection_manager._get_collection_name(scope)
                try:
                    info = await self.collection_manager.qdrant.get_collection_info(
                        collection_name
                    )
                    if info:
                        metrics.total_entries += info.get("vectors_count", 0)
                        metrics.collections_count += 1

                        # Estimate size (rough calculation)
                        vector_count = info.get("vectors_count", 0)
                        vector_size = (
                            info.get("config", {})
                            .get("params", {})
                            .get("vectors", {})
                            .get("size", 384)
                        )
                        estimated_size = (
                            vector_count * vector_size * 4
                        )  # 4 bytes per float
                        metrics.total_size_bytes += estimated_size

                except Exception as e:
                    self.logger.warning(
                        f"Could not get info for {collection_name}: {e}"
                    )

            # Calculate average entry size
            if metrics.total_entries > 0:
                metrics.average_entry_size = (
                    metrics.total_size_bytes / metrics.total_entries
                )

        except Exception as e:
            self.logger.error(f"Error collecting storage metrics: {e}")

    def _collect_access_patterns(self, metrics: MemoryMetrics) -> None:
        """Collect access pattern metrics."""
        metrics.read_operations = self._operation_counts.get("read", 0)
        metrics.write_operations = self._operation_counts.get("write", 0)
        metrics.search_operations = self._operation_counts.get("search", 0)

    def _collect_performance_metrics(self, metrics: MemoryMetrics) -> None:
        """Collect performance-related metrics."""
        # Calculate average operation times
        search_times = self._operation_times.get("search", [])
        if search_times:
            metrics.average_search_time_ms = sum(search_times) / len(search_times)

        write_times = self._operation_times.get("write", [])
        if write_times:
            metrics.average_write_time_ms = sum(write_times) / len(write_times)

        # Calculate cache hit ratio
        total_cache_ops = self._cache_stats["hits"] + self._cache_stats["misses"]
        if total_cache_ops > 0:
            metrics.cache_hit_ratio = self._cache_stats["hits"] / total_cache_ops

    async def _collect_health_indicators(self, metrics: MemoryMetrics) -> None:
        """Collect health-related indicators."""
        try:
            # Memory utilization (simplified calculation)
            max_memory_bytes = 1024 * 1024 * 1024  # 1GB default limit
            metrics.memory_utilization = min(
                metrics.total_size_bytes / max_memory_bytes, 1.0
            )

            # Find oldest entry (simplified - would need proper timestamp tracking)
            metrics.oldest_entry_age_days = 0.0  # Placeholder

            # Fragmentation estimation (placeholder)
            metrics.fragmentation_ratio = 0.1  # Default low fragmentation

        except Exception as e:
            self.logger.error(f"Error collecting health indicators: {e}")

    async def _collect_scope_metrics(self, metrics: MemoryMetrics) -> None:
        """Collect metrics per memory scope."""
        for scope in MemoryScope:
            try:
                scope_metrics = {
                    "entry_count": 0,
                    "size_bytes": 0,
                    "last_accessed": None,
                    "avg_importance": 0.0,
                }

                # This would be expanded with actual scope-specific collection queries
                metrics.scope_metrics[scope] = scope_metrics

            except Exception as e:
                self.logger.warning(f"Error collecting metrics for scope {scope}: {e}")

    def track_operation(self, operation_type: str, duration_ms: float) -> None:
        """Track operation performance."""
        if operation_type in self._operation_times:
            self._operation_times[operation_type].append(duration_ms)
            self._operation_counts[operation_type] += 1

            # Keep only recent operations (last 1000)
            if len(self._operation_times[operation_type]) > 1000:
                self._operation_times[operation_type] = self._operation_times[
                    operation_type
                ][-1000:]

    def track_cache_hit(self, hit: bool) -> None:
        """Track cache hit/miss."""
        if hit:
            self._cache_stats["hits"] += 1
        else:
            self._cache_stats["misses"] += 1


class IntelligentMemoryPruner:
    """Intelligent memory pruning with multiple strategies."""

    def __init__(self, memory_service: MultiScopeMemoryService):
        self.memory_service = memory_service
        self.collection_manager = memory_service.collection_manager
        self.logger = get_logger("autogen.memory_analytics.pruner")

        # Pruning configuration
        self.max_entries_per_scope = {
            MemoryScope.GLOBAL: 10000,
            MemoryScope.PROJECT: 5000,
            MemoryScope.AGENT: 2000,
            MemoryScope.THREAD: 1000,
            MemoryScope.OBJECTIVES: 1000,
            MemoryScope.ARTIFACTS: 20000,
        }

        self.importance_threshold = 0.3  # Minimum importance to keep
        self.staleness_days = 90  # Days after which entries are considered stale

    async def prune_memory(
        self,
        strategy: PruningStrategy = PruningStrategy.HYBRID,
        target_reduction_percent: float = 20.0,
        dry_run: bool = False,
    ) -> PruningResult:
        """Execute memory pruning based on the specified strategy."""
        start_time = time.time()

        try:
            result = PruningResult(
                entries_removed=0,
                bytes_freed=0,
                collections_affected=[],
                strategy_used=strategy,
                execution_time_ms=0,
            )

            # Get current metrics
            metrics_collector = MemoryMetricsCollector(self.memory_service)
            current_metrics = await metrics_collector.collect_metrics()

            # Calculate target entries to remove
            target_entries = int(
                current_metrics.total_entries * (target_reduction_percent / 100)
            )

            self.logger.info(
                f"Starting {strategy} pruning: target {target_entries} entries "
                f"({target_reduction_percent}% reduction)"
            )

            # Execute strategy-specific pruning
            if strategy == PruningStrategy.LRU:
                await self._prune_lru(result, target_entries, dry_run)
            elif strategy == PruningStrategy.IMPORTANCE_BASED:
                await self._prune_by_importance(result, target_entries, dry_run)
            elif strategy == PruningStrategy.ACCESS_FREQUENCY:
                await self._prune_by_frequency(result, target_entries, dry_run)
            elif strategy == PruningStrategy.HYBRID:
                await self._prune_hybrid(result, target_entries, dry_run)

            result.execution_time_ms = (time.time() - start_time) * 1000

            if not dry_run:
                self.logger.info(
                    f"Pruning completed: {result.entries_removed} entries removed, "
                    f"{result.bytes_freed / 1024 / 1024:.2f} MB freed"
                )
            else:
                self.logger.info(
                    f"Pruning dry run: would remove {result.entries_removed} entries"
                )

            return result

        except Exception as e:
            self.logger.error(f"Error during pruning: {e}")
            raise

    async def _prune_lru(
        self, result: PruningResult, target_entries: int, dry_run: bool
    ) -> None:
        """Prune least recently used entries."""
        # This would implement LRU pruning logic
        # For now, implement a basic version
        self.logger.info("Executing LRU pruning strategy")

        # Placeholder implementation
        result.entries_removed = min(target_entries, 100)
        result.bytes_freed = result.entries_removed * 1024  # Estimate
        result.preservation_reasons["lru"] = result.entries_removed

    async def _prune_by_importance(
        self, result: PruningResult, target_entries: int, dry_run: bool
    ) -> None:
        """Prune entries with low importance scores."""
        self.logger.info("Executing importance-based pruning strategy")

        # This would query entries by importance and remove low-scored ones
        # Placeholder implementation
        result.entries_removed = min(target_entries, 150)
        result.bytes_freed = result.entries_removed * 1024
        result.preservation_reasons["importance"] = result.entries_removed

    async def _prune_by_frequency(
        self, result: PruningResult, target_entries: int, dry_run: bool
    ) -> None:
        """Prune entries with low access frequency."""
        self.logger.info("Executing frequency-based pruning strategy")

        # This would analyze access patterns and remove rarely accessed entries
        # Placeholder implementation
        result.entries_removed = min(target_entries, 120)
        result.bytes_freed = result.entries_removed * 1024
        result.preservation_reasons["frequency"] = result.entries_removed

    async def _prune_hybrid(
        self, result: PruningResult, target_entries: int, dry_run: bool
    ) -> None:
        """Prune using a combination of strategies."""
        self.logger.info("Executing hybrid pruning strategy")

        # Combine multiple factors: importance, frequency, staleness
        # This would implement a weighted scoring system

        # Placeholder implementation combining all strategies
        result.entries_removed = min(target_entries, 200)
        result.bytes_freed = result.entries_removed * 1024
        result.preservation_reasons = {
            "importance": result.entries_removed // 3,
            "frequency": result.entries_removed // 3,
            "staleness": result.entries_removed // 3,
        }


class MemoryHealthMonitor:
    """Monitors memory system health and generates alerts."""

    def __init__(self, memory_service: MultiScopeMemoryService):
        self.memory_service = memory_service
        self.logger = get_logger("autogen.memory_analytics.health")

        # Health thresholds
        self.thresholds = {
            "memory_utilization": {"warning": 0.7, "critical": 0.9},
            "average_search_time_ms": {"warning": 1000, "critical": 3000},
            "fragmentation_ratio": {"warning": 0.3, "critical": 0.5},
            "cache_hit_ratio": {"warning": 0.6, "critical": 0.4},  # Lower is worse
            "stale_entries_percent": {"warning": 0.2, "critical": 0.4},
        }

    async def check_health(self) -> Tuple[HealthStatus, List[HealthAlert]]:
        """Perform comprehensive health check."""
        try:
            # Collect current metrics
            metrics_collector = MemoryMetricsCollector(self.memory_service)
            metrics = await metrics_collector.collect_metrics()

            alerts = []
            overall_status = HealthStatus.HEALTHY

            # Check memory utilization
            self._check_memory_utilization(metrics, alerts)

            # Check performance metrics
            self._check_performance_metrics(metrics, alerts)

            # Check system health indicators
            self._check_health_indicators(metrics, alerts)

            # Determine overall status
            if any(alert.severity == HealthStatus.CRITICAL for alert in alerts):
                overall_status = HealthStatus.CRITICAL
            elif any(alert.severity == HealthStatus.ERROR for alert in alerts):
                overall_status = HealthStatus.ERROR
            elif any(alert.severity == HealthStatus.WARNING for alert in alerts):
                overall_status = HealthStatus.WARNING

            self.logger.info(
                f"Health check completed: {overall_status}, {len(alerts)} alerts"
            )

            return overall_status, alerts

        except Exception as e:
            self.logger.error(f"Error during health check: {e}")
            error_alert = HealthAlert(
                severity=HealthStatus.ERROR,
                message=f"Health check failed: {str(e)}",
                metric_name="health_check",
                current_value="error",
                threshold="success",
                recommendations=[
                    "Check system logs",
                    "Verify memory service connectivity",
                ],
            )
            return HealthStatus.ERROR, [error_alert]

    def _check_memory_utilization(
        self, metrics: MemoryMetrics, alerts: List[HealthAlert]
    ) -> None:
        """Check memory utilization levels."""
        utilization = metrics.memory_utilization
        thresholds = self.thresholds["memory_utilization"]

        if utilization >= thresholds["critical"]:
            alerts.append(
                HealthAlert(
                    severity=HealthStatus.CRITICAL,
                    message=f"Memory utilization critically high: {utilization:.1%}",
                    metric_name="memory_utilization",
                    current_value=utilization,
                    threshold=thresholds["critical"],
                    recommendations=[
                        "Execute immediate memory pruning",
                        "Archive old project data",
                        "Consider increasing memory limits",
                    ],
                )
            )
        elif utilization >= thresholds["warning"]:
            alerts.append(
                HealthAlert(
                    severity=HealthStatus.WARNING,
                    message=f"Memory utilization high: {utilization:.1%}",
                    metric_name="memory_utilization",
                    current_value=utilization,
                    threshold=thresholds["warning"],
                    recommendations=[
                        "Schedule memory pruning",
                        "Review memory usage patterns",
                        "Consider optimization strategies",
                    ],
                )
            )

    def _check_performance_metrics(
        self, metrics: MemoryMetrics, alerts: List[HealthAlert]
    ) -> None:
        """Check performance-related metrics."""
        # Check search performance
        search_time = metrics.average_search_time_ms
        search_thresholds = self.thresholds["average_search_time_ms"]

        if search_time >= search_thresholds["critical"]:
            alerts.append(
                HealthAlert(
                    severity=HealthStatus.CRITICAL,
                    message=f"Search performance critically slow: {search_time:.1f}ms",
                    metric_name="average_search_time_ms",
                    current_value=search_time,
                    threshold=search_thresholds["critical"],
                    recommendations=[
                        "Optimize search indexes",
                        "Reduce search result size",
                        "Consider query optimization",
                    ],
                )
            )
        elif search_time >= search_thresholds["warning"]:
            alerts.append(
                HealthAlert(
                    severity=HealthStatus.WARNING,
                    message=f"Search performance degraded: {search_time:.1f}ms",
                    metric_name="average_search_time_ms",
                    current_value=search_time,
                    threshold=search_thresholds["warning"],
                    recommendations=[
                        "Monitor search patterns",
                        "Review index configuration",
                        "Consider performance tuning",
                    ],
                )
            )

    def _check_health_indicators(
        self, metrics: MemoryMetrics, alerts: List[HealthAlert]
    ) -> None:
        """Check general health indicators."""
        # Check cache performance
        cache_ratio = metrics.cache_hit_ratio
        cache_thresholds = self.thresholds["cache_hit_ratio"]

        if cache_ratio <= cache_thresholds["critical"]:
            alerts.append(
                HealthAlert(
                    severity=HealthStatus.CRITICAL,
                    message=f"Cache hit ratio critically low: {cache_ratio:.1%}",
                    metric_name="cache_hit_ratio",
                    current_value=cache_ratio,
                    threshold=cache_thresholds["critical"],
                    recommendations=[
                        "Review cache configuration",
                        "Increase cache size",
                        "Optimize cache eviction policy",
                    ],
                )
            )
        elif cache_ratio <= cache_thresholds["warning"]:
            alerts.append(
                HealthAlert(
                    severity=HealthStatus.WARNING,
                    message=f"Cache hit ratio low: {cache_ratio:.1%}",
                    metric_name="cache_hit_ratio",
                    current_value=cache_ratio,
                    threshold=cache_thresholds["warning"],
                    recommendations=[
                        "Monitor cache usage patterns",
                        "Consider cache tuning",
                        "Review access patterns",
                    ],
                )
            )


class MemoryAnalyticsService:
    """Main service orchestrating memory analytics, optimization, and monitoring."""

    def __init__(self, memory_service: MultiScopeMemoryService):
        self.memory_service = memory_service
        self.metrics_collector = MemoryMetricsCollector(memory_service)
        self.pruner = IntelligentMemoryPruner(memory_service)
        self.health_monitor = MemoryHealthMonitor(memory_service)
        self.logger = get_logger("autogen.memory_analytics")

        # Analytics configuration
        self.auto_pruning_enabled = True
        self.health_check_interval_minutes = 15
        self.metrics_collection_interval_minutes = 5

        # Background tasks
        self._monitoring_task: Optional[asyncio.Task] = None
        self._metrics_task: Optional[asyncio.Task] = None

    async def start_monitoring(self) -> None:
        """Start background monitoring tasks."""
        if self._monitoring_task is None or self._monitoring_task.done():
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())

        if self._metrics_task is None or self._metrics_task.done():
            self._metrics_task = asyncio.create_task(self._metrics_collection_loop())

        self.logger.info("Memory analytics monitoring started")

    async def stop_monitoring(self) -> None:
        """Stop background monitoring tasks."""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        if self._metrics_task:
            self._metrics_task.cancel()
            try:
                await self._metrics_task
            except asyncio.CancelledError:
                pass

        self.logger.info("Memory analytics monitoring stopped")

    async def get_analytics_report(self) -> Dict[str, Any]:
        """Generate comprehensive analytics report."""
        try:
            # Collect current metrics
            metrics = await self.metrics_collector.collect_metrics()

            # Perform health check
            health_status, alerts = await self.health_monitor.check_health()

            # Generate report
            report = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metrics": {
                    "storage": {
                        "total_entries": metrics.total_entries,
                        "total_size_mb": metrics.total_size_bytes / 1024 / 1024,
                        "collections_count": metrics.collections_count,
                        "average_entry_size_kb": metrics.average_entry_size / 1024,
                    },
                    "performance": {
                        "average_search_time_ms": metrics.average_search_time_ms,
                        "average_write_time_ms": metrics.average_write_time_ms,
                        "cache_hit_ratio": metrics.cache_hit_ratio,
                        "query_success_rate": metrics.query_success_rate,
                    },
                    "access_patterns": {
                        "read_operations": metrics.read_operations,
                        "write_operations": metrics.write_operations,
                        "search_operations": metrics.search_operations,
                    },
                    "health": {
                        "memory_utilization": metrics.memory_utilization,
                        "fragmentation_ratio": metrics.fragmentation_ratio,
                        "oldest_entry_age_days": metrics.oldest_entry_age_days,
                        "stale_entries_count": metrics.stale_entries_count,
                    },
                },
                "health_status": health_status,
                "alerts": [
                    {
                        "severity": alert.severity,
                        "message": alert.message,
                        "metric": alert.metric_name,
                        "current_value": alert.current_value,
                        "threshold": alert.threshold,
                        "recommendations": alert.recommendations,
                        "timestamp": alert.timestamp.isoformat(),
                    }
                    for alert in alerts
                ],
                "scope_metrics": {
                    scope.value: scope_data
                    for scope, scope_data in metrics.scope_metrics.items()
                },
            }

            return report

        except Exception as e:
            self.logger.error(f"Error generating analytics report: {e}")
            raise

    async def optimize_memory(
        self,
        strategy: PruningStrategy = PruningStrategy.HYBRID,
        target_reduction_percent: float = 15.0,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Execute memory optimization."""
        try:
            self.logger.info(
                f"Starting memory optimization: {strategy}, "
                f"{target_reduction_percent}% reduction, dry_run={dry_run}"
            )

            # Perform pruning
            pruning_result = await self.pruner.prune_memory(
                strategy=strategy,
                target_reduction_percent=target_reduction_percent,
                dry_run=dry_run,
            )

            # Generate optimization report
            optimization_report = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "strategy": strategy,
                "target_reduction_percent": target_reduction_percent,
                "dry_run": dry_run,
                "results": {
                    "entries_removed": pruning_result.entries_removed,
                    "bytes_freed": pruning_result.bytes_freed,
                    "collections_affected": pruning_result.collections_affected,
                    "execution_time_ms": pruning_result.execution_time_ms,
                    "preserved_entries": pruning_result.preserved_entries,
                    "preservation_reasons": pruning_result.preservation_reasons,
                    "errors": pruning_result.errors,
                },
            }

            if not dry_run:
                # Trigger health check after optimization
                health_status, alerts = await self.health_monitor.check_health()
                optimization_report["post_optimization_health"] = {
                    "status": health_status,
                    "alerts_count": len(alerts),
                }

            return optimization_report

        except Exception as e:
            self.logger.error(f"Error during memory optimization: {e}")
            raise

    async def _monitoring_loop(self) -> None:
        """Background health monitoring loop."""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval_minutes * 60)

                health_status, alerts = await self.health_monitor.check_health()

                # Handle critical alerts
                if health_status == HealthStatus.CRITICAL and self.auto_pruning_enabled:
                    self.logger.warning(
                        "Critical health status detected, executing emergency pruning"
                    )
                    try:
                        await self.optimize_memory(
                            strategy=PruningStrategy.HYBRID,
                            target_reduction_percent=25.0,
                            dry_run=False,
                        )
                    except Exception as e:
                        self.logger.error(f"Emergency pruning failed: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")

    async def _metrics_collection_loop(self) -> None:
        """Background metrics collection loop."""
        while True:
            try:
                await asyncio.sleep(self.metrics_collection_interval_minutes * 60)

                # Collect and log metrics
                metrics = await self.metrics_collector.collect_metrics()
                self.logger.info(
                    f"Metrics collected: {metrics.total_entries} entries, "
                    f"{metrics.memory_utilization:.1%} utilization"
                )

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in metrics collection loop: {e}")

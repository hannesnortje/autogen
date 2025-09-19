"""
Comprehensive Knowledge Management Service integrating all knowledge operations.

This service orchestrates knowledge seeding, thread summarization, memory pruning,
and knowledge transfer to provide a complete knowledge management solution.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from autogen_mcp.memory_collections import CollectionManager
from autogen_mcp.knowledge_seeder import KnowledgeSeeder
from autogen_mcp.knowledge_transfer import (
    ExportConfig,
    ImportConfig,
    KnowledgeExportImportService,
)
from autogen_mcp.memory_pruning import MemoryPruningService
from autogen_mcp.multi_memory import MultiScopeMemoryService
from autogen_mcp.observability import get_logger
from autogen_mcp.thread_summarization import (
    ThreadSummarizationService,
)


@dataclass
class KnowledgeManagementConfig:
    """Configuration for knowledge management operations."""

    # Auto-summarization settings
    auto_summarization_enabled: bool = True
    summarization_check_interval: int = 3600  # Check every hour

    # Auto-pruning settings
    auto_pruning_enabled: bool = True
    pruning_check_interval: int = 24 * 3600  # Check daily
    pruning_dry_run: bool = True  # Safety default

    # Knowledge seeding settings
    seed_on_initialization: bool = True
    reseed_global_knowledge: bool = False  # Only seed if empty

    # Health monitoring
    health_check_interval: int = 6 * 3600  # Check every 6 hours
    alert_on_memory_issues: bool = True


class KnowledgeManagementService:
    """Comprehensive service for managing all knowledge operations."""

    def __init__(
        self,
        memory_service: MultiScopeMemoryService,
        collection_manager: Optional[CollectionManager] = None,
        config: Optional[KnowledgeManagementConfig] = None,
    ):
        self.memory_service = memory_service
        self.collection_manager = collection_manager or CollectionManager()
        self.config = config or KnowledgeManagementConfig()
        self.logger = get_logger("autogen.knowledge_management")

        # Initialize component services
        self.seeder = KnowledgeSeeder(self.collection_manager)
        self.summarization = ThreadSummarizationService(self.memory_service)
        self.pruning = MemoryPruningService(self.memory_service)
        self.transfer = KnowledgeExportImportService(self.memory_service)

        # Track last operation times
        self._last_summarization_check = 0
        self._last_pruning_check = 0
        self._last_health_check = 0

    def initialize_knowledge_system(
        self, project_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Initialize the complete knowledge management system."""
        start_time = time.time()
        result = {
            "timestamp": time.time(),
            "components": {},
            "success": True,
            "errors": [],
        }

        try:
            self.logger.info("Initializing comprehensive knowledge management system")

            # 1. Initialize memory service
            self.logger.info("Initializing memory service...")
            memory_result = self.memory_service.initialize(project_ids)
            result["components"]["memory_service"] = memory_result

            # 2. Seed global knowledge if configured
            if self.config.seed_on_initialization:
                self.logger.info("Seeding global knowledge...")
                if self.config.reseed_global_knowledge:
                    seeding_result = self.seeder.seed_global_knowledge()
                else:
                    # Only seed if global collection is empty
                    global_search = self.memory_service.search(
                        query="*", scope="global", limit=1
                    )
                    if not global_search:
                        seeding_result = self.seeder.seed_global_knowledge()
                    else:
                        seeding_result = {
                            "status": "skipped",
                            "reason": "Global knowledge already exists",
                        }

                result["components"]["knowledge_seeding"] = seeding_result

            # 3. Initialize component services
            for service_name, service in [
                ("summarization", self.summarization),
                ("pruning", self.pruning),
                ("transfer", self.transfer),
            ]:
                try:
                    if hasattr(service, "get_status"):
                        status = service.get_status()
                    else:
                        status = {"operational": True, "initialized": True}
                    result["components"][service_name] = status
                except Exception as e:
                    result["errors"].append(
                        f"{service_name} initialization warning: {str(e)}"
                    )

            # 4. Perform initial health check
            health_result = self.get_system_health()
            result["components"]["health_check"] = health_result

            execution_time = time.time() - start_time
            result["execution_time"] = execution_time

            success = len(result["errors"]) == 0 and memory_result.get("success", False)
            result["success"] = success

            if success:
                self.logger.info(
                    f"Knowledge management system initialized successfully in {execution_time:.2f}s"
                )
            else:
                self.logger.warning(
                    f"Knowledge management system initialized with warnings in {execution_time:.2f}s"
                )

            return result

        except Exception as e:
            error_msg = f"Knowledge management initialization failed: {str(e)}"
            self.logger.error(error_msg)
            result["success"] = False
            result["error"] = error_msg
            result["execution_time"] = time.time() - start_time
            return result

    def run_maintenance_cycle(self) -> Dict[str, Any]:
        """Run a complete maintenance cycle including summarization, pruning, and health checks."""
        start_time = time.time()
        result = {
            "timestamp": time.time(),
            "operations": {},
            "success": True,
            "errors": [],
        }

        try:
            self.logger.info("Starting knowledge management maintenance cycle")

            # 1. Thread Summarization
            if self.config.auto_summarization_enabled:
                if self._should_run_summarization():
                    self.logger.info("Running automatic thread summarization...")
                    summary_results = (
                        self.summarization.auto_summarize_eligible_threads()
                    )
                    result["operations"]["summarization"] = {
                        "executed": True,
                        "results": summary_results,
                    }
                    self._last_summarization_check = time.time()
                else:
                    result["operations"]["summarization"] = {
                        "executed": False,
                        "reason": "Not due for summarization check",
                    }

            # 2. Memory Pruning
            if self.config.auto_pruning_enabled:
                if self._should_run_pruning():
                    self.logger.info("Running automatic memory pruning...")
                    pruning_results = self.pruning.prune_all_scopes()
                    result["operations"]["pruning"] = {
                        "executed": True,
                        "results": pruning_results,
                    }
                    self._last_pruning_check = time.time()
                else:
                    result["operations"]["pruning"] = {
                        "executed": False,
                        "reason": "Not due for pruning check",
                    }

            # 3. System Health Check
            if self._should_run_health_check():
                self.logger.info("Running system health check...")
                health_result = self.get_system_health()
                result["operations"]["health_check"] = {
                    "executed": True,
                    "results": health_result,
                }
                self._last_health_check = time.time()
            else:
                result["operations"]["health_check"] = {
                    "executed": False,
                    "reason": "Not due for health check",
                }

            execution_time = time.time() - start_time
            result["execution_time"] = execution_time

            # Determine overall success
            operations_run = sum(
                1 for op in result["operations"].values() if op.get("executed", False)
            )
            result["operations_run"] = operations_run
            result["success"] = len(result["errors"]) == 0

            self.logger.info(
                f"Maintenance cycle completed: {operations_run} operations in {execution_time:.2f}s"
            )

            return result

        except Exception as e:
            error_msg = f"Maintenance cycle failed: {str(e)}"
            self.logger.error(error_msg)
            result["success"] = False
            result["error"] = error_msg
            result["execution_time"] = time.time() - start_time
            return result

    def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive health status of the knowledge management system."""
        try:
            health = {
                "timestamp": time.time(),
                "overall_status": "healthy",
                "components": {},
                "recommendations": [],
                "alerts": [],
            }

            # Check memory service health
            memory_health = self.memory_service.get_health_status()
            health["components"]["memory_service"] = memory_health

            # Check component services
            try:
                health["components"][
                    "summarization"
                ] = self.summarization.get_summarization_status()
            except Exception as e:
                health["components"]["summarization"] = {"error": str(e)}

            try:
                health["components"]["pruning"] = self.pruning.get_pruning_status()
            except Exception as e:
                health["components"]["pruning"] = {"error": str(e)}

            try:
                health["components"]["transfer"] = self.transfer.get_transfer_status()
            except Exception as e:
                health["components"]["transfer"] = {"error": str(e)}

            # Analyze memory usage
            try:
                pruning_analysis = self.pruning.analyze_memory_usage()
                health["memory_analysis"] = pruning_analysis

                # Generate recommendations based on analysis
                recommendations = pruning_analysis.get("recommendations", [])
                health["recommendations"].extend(recommendations)

                # Check for alerts
                if self.config.alert_on_memory_issues:
                    total_candidates = sum(
                        scope_data.get("total_candidates", 0)
                        for scope_data in pruning_analysis.get(
                            "pruning_candidates", {}
                        ).values()
                    )
                    if total_candidates > 2000:
                        health["alerts"].append(
                            f"High number of pruning candidates ({total_candidates}) - consider immediate pruning"
                        )

            except Exception as e:
                health["memory_analysis"] = {"error": str(e)}

            # Determine overall health status
            component_errors = [
                comp
                for comp in health["components"].values()
                if "error" in comp or not comp.get("service_operational", True)
            ]

            if len(component_errors) > 0:
                health["overall_status"] = "degraded"
                health["alerts"].append(
                    f"{len(component_errors)} components have issues"
                )

            if len(health["alerts"]) > 3:
                health["overall_status"] = "unhealthy"

            return health

        except Exception as e:
            return {
                "timestamp": time.time(),
                "overall_status": "error",
                "error": str(e),
                "components": {},
                "recommendations": ["Check system logs for detailed error information"],
                "alerts": ["System health check failed"],
            }

    def export_system_knowledge(self, output_path: str) -> Dict[str, Any]:
        """Export all system knowledge for backup or migration."""
        config = ExportConfig(
            exclude_low_importance=False,  # Export everything for backup
            include_vectors=False,  # Can be regenerated
            anonymize_sensitive_data=True,
        )

        return self.transfer.export_knowledge(output_path, config)

    def import_system_knowledge(self, import_path: str) -> Dict[str, Any]:
        """Import system knowledge from backup or external source."""
        config = ImportConfig(
            merge_strategy="skip_existing",  # Don't overwrite existing
            regenerate_vectors=True,
            validate_before_import=True,
        )

        return self.transfer.import_knowledge(import_path, config)

    def create_project_knowledge_pack(
        self, project_id: str, output_path: str
    ) -> Dict[str, Any]:
        """Create a knowledge pack for a specific project."""
        return self.transfer.export_project_template(project_id, output_path)

    def bootstrap_project_from_template(
        self, template_path: str, new_project_id: str
    ) -> Dict[str, Any]:
        """Bootstrap a new project using a knowledge template."""
        return self.transfer.import_project_template(template_path, new_project_id)

    def _should_run_summarization(self) -> bool:
        """Check if it's time to run thread summarization."""
        current_time = time.time()
        return (
            current_time - self._last_summarization_check
        ) >= self.config.summarization_check_interval

    def _should_run_pruning(self) -> bool:
        """Check if it's time to run memory pruning."""
        current_time = time.time()
        return (
            current_time - self._last_pruning_check
        ) >= self.config.pruning_check_interval

    def _should_run_health_check(self) -> bool:
        """Check if it's time to run system health check."""
        current_time = time.time()
        return (
            current_time - self._last_health_check
        ) >= self.config.health_check_interval

    def get_management_status(self) -> Dict[str, Any]:
        """Get current status of the knowledge management service."""
        return {
            "config": {
                "auto_summarization_enabled": self.config.auto_summarization_enabled,
                "auto_pruning_enabled": self.config.auto_pruning_enabled,
                "seed_on_initialization": self.config.seed_on_initialization,
                "health_monitoring": self.config.alert_on_memory_issues,
            },
            "last_operations": {
                "summarization_check": self._last_summarization_check,
                "pruning_check": self._last_pruning_check,
                "health_check": self._last_health_check,
            },
            "next_operations": {
                "summarization_due": self._should_run_summarization(),
                "pruning_due": self._should_run_pruning(),
                "health_check_due": self._should_run_health_check(),
            },
            "service_operational": True,
        }

    def update_configuration(
        self, new_config: KnowledgeManagementConfig
    ) -> Dict[str, Any]:
        """Update the knowledge management configuration."""
        old_config = self.config
        self.config = new_config

        # Update component configurations
        if hasattr(self.pruning.rules, "dry_run"):
            self.pruning.rules.dry_run = new_config.pruning_dry_run

        return {
            "status": "updated",
            "old_config": old_config.__dict__,
            "new_config": new_config.__dict__,
            "timestamp": time.time(),
        }

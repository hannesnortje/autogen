"""
Knowledge Export/Import Service for sharing memory between projects and teams.

Enables exporting knowledge collections to portable formats and importing
knowledge from external sources to seed new projects or share best practices.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from autogen_mcp.collections import MemoryScope
from autogen_mcp.multi_memory import MultiScopeMemoryService, MemoryWriteOptions
from autogen_mcp.observability import get_logger


@dataclass
class ExportConfig:
    """Configuration for knowledge export operations."""

    include_scopes: List[MemoryScope] = None
    exclude_low_importance: bool = True
    min_importance_threshold: float = 0.5
    include_vectors: bool = False  # Vectors are large and can be regenerated
    max_entries_per_scope: int = 1000
    anonymize_sensitive_data: bool = True


@dataclass
class ImportConfig:
    """Configuration for knowledge import operations."""

    target_project_id: Optional[str] = None
    merge_strategy: str = "skip_existing"  # skip_existing, overwrite, append
    regenerate_vectors: bool = True  # Regenerate embeddings on import
    validate_before_import: bool = True
    import_batch_size: int = 50


@dataclass
class KnowledgePackage:
    """A portable package of knowledge for export/import."""

    metadata: Dict[str, Any]
    global_knowledge: List[Dict[str, Any]]
    project_knowledge: List[Dict[str, Any]]
    agent_knowledge: List[Dict[str, Any]]
    objectives: List[Dict[str, Any]]
    artifacts: List[Dict[str, Any]]
    export_timestamp: float
    export_version: str = "1.0"


class KnowledgeExportImportService:
    """Service for exporting and importing knowledge between projects."""

    def __init__(self, memory_service: MultiScopeMemoryService):
        self.memory_service = memory_service
        self.logger = get_logger("autogen.knowledge_transfer")

    def export_knowledge(
        self,
        output_path: str,
        config: Optional[ExportConfig] = None,
        project_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Export knowledge to a portable JSON file."""
        config = config or ExportConfig()
        start_time = time.time()

        try:
            self.logger.info(f"Starting knowledge export to {output_path}")

            # Determine scopes to export
            scopes_to_export = config.include_scopes or [
                MemoryScope.GLOBAL,
                MemoryScope.PROJECT,
                MemoryScope.AGENT,
                MemoryScope.OBJECTIVES,
                MemoryScope.ARTIFACTS,
            ]

            # Collect knowledge from each scope
            package = KnowledgePackage(
                metadata=self._generate_export_metadata(config, project_id),
                global_knowledge=[],
                project_knowledge=[],
                agent_knowledge=[],
                objectives=[],
                artifacts=[],
                export_timestamp=time.time(),
            )

            total_entries = 0
            errors = []

            for scope in scopes_to_export:
                try:
                    entries = self._export_scope(scope, config, project_id)
                    total_entries += len(entries)

                    # Add to appropriate section
                    if scope == MemoryScope.GLOBAL:
                        package.global_knowledge = entries
                    elif scope == MemoryScope.PROJECT:
                        package.project_knowledge = entries
                    elif scope == MemoryScope.AGENT:
                        package.agent_knowledge = entries
                    elif scope == MemoryScope.OBJECTIVES:
                        package.objectives = entries
                    elif scope == MemoryScope.ARTIFACTS:
                        package.artifacts = entries

                    self.logger.debug(
                        f"Exported {len(entries)} entries from {scope.value}"
                    )

                except Exception as e:
                    error_msg = f"Failed to export {scope.value}: {str(e)}"
                    errors.append(error_msg)
                    self.logger.warning(error_msg)

            # Write to file
            self._write_package_to_file(package, output_path)

            execution_time = time.time() - start_time
            result = {
                "export_path": output_path,
                "total_entries": total_entries,
                "scopes_exported": len(scopes_to_export),
                "package_size": self._get_file_size(output_path),
                "execution_time": execution_time,
                "errors": errors,
                "success": len(errors) == 0,
            }

            self.logger.info(
                f"Knowledge export completed: {total_entries} entries in {execution_time:.2f}s",
                extra={"extra": result},
            )

            return result

        except Exception as e:
            error_msg = f"Knowledge export failed: {str(e)}"
            self.logger.error(error_msg)
            return {
                "export_path": output_path,
                "error": error_msg,
                "success": False,
                "execution_time": time.time() - start_time,
            }

    def import_knowledge(
        self,
        import_path: str,
        config: Optional[ImportConfig] = None,
    ) -> Dict[str, Any]:
        """Import knowledge from a portable JSON file."""
        config = config or ImportConfig()
        start_time = time.time()

        try:
            self.logger.info(f"Starting knowledge import from {import_path}")

            # Load and validate package
            package = self._load_package_from_file(import_path)
            if config.validate_before_import:
                validation_result = self._validate_package(package)
                if not validation_result["valid"]:
                    return {
                        "import_path": import_path,
                        "error": f"Package validation failed: {validation_result['errors']}",
                        "success": False,
                        "execution_time": time.time() - start_time,
                    }

            total_imported = 0
            errors = []
            skipped = 0

            # Import each scope
            for scope_name, entries in [
                ("global", package.global_knowledge),
                ("project", package.project_knowledge),
                ("agent", package.agent_knowledge),
                ("objectives", package.objectives),
                ("artifacts", package.artifacts),
            ]:
                if not entries:
                    continue

                try:
                    scope_result = self._import_scope_entries(
                        scope_name, entries, config
                    )
                    total_imported += scope_result["imported"]
                    skipped += scope_result["skipped"]
                    errors.extend(scope_result["errors"])

                    self.logger.debug(
                        f"Imported {scope_result['imported']} entries to {scope_name} scope"
                    )

                except Exception as e:
                    error_msg = f"Failed to import {scope_name} scope: {str(e)}"
                    errors.append(error_msg)
                    self.logger.warning(error_msg)

            execution_time = time.time() - start_time
            result = {
                "import_path": import_path,
                "total_imported": total_imported,
                "skipped": skipped,
                "package_metadata": package.metadata,
                "execution_time": execution_time,
                "errors": errors,
                "success": len(errors) == 0,
            }

            self.logger.info(
                f"Knowledge import completed: {total_imported} entries imported, "
                f"{skipped} skipped in {execution_time:.2f}s",
                extra={"extra": result},
            )

            return result

        except Exception as e:
            error_msg = f"Knowledge import failed: {str(e)}"
            self.logger.error(error_msg)
            return {
                "import_path": import_path,
                "error": error_msg,
                "success": False,
                "execution_time": time.time() - start_time,
            }

    def export_project_template(
        self, project_id: str, output_path: str
    ) -> Dict[str, Any]:
        """Export a project as a template for reuse."""
        config = ExportConfig(
            include_scopes=[
                MemoryScope.GLOBAL,  # Include global patterns
                MemoryScope.PROJECT,  # Project-specific decisions
                MemoryScope.OBJECTIVES,  # Goal patterns
            ],
            exclude_low_importance=True,
            min_importance_threshold=0.7,  # Higher threshold for templates
            anonymize_sensitive_data=True,
        )

        result = self.export_knowledge(output_path, config, project_id)
        result["template_type"] = "project"
        return result

    def import_project_template(
        self, template_path: str, new_project_id: str
    ) -> Dict[str, Any]:
        """Import a project template to bootstrap a new project."""
        config = ImportConfig(
            target_project_id=new_project_id,
            merge_strategy="append",  # Add to existing knowledge
            regenerate_vectors=True,
        )

        return self.import_knowledge(template_path, config)

    def export_agent_profiles(self, output_path: str) -> Dict[str, Any]:
        """Export agent knowledge profiles for sharing."""
        config = ExportConfig(
            include_scopes=[MemoryScope.AGENT],
            exclude_low_importance=False,  # Keep all agent knowledge
            anonymize_sensitive_data=True,
        )

        return self.export_knowledge(output_path, config)

    def import_agent_profiles(self, import_path: str) -> Dict[str, Any]:
        """Import agent knowledge profiles."""
        config = ImportConfig(
            merge_strategy="overwrite",  # Update agent capabilities
            regenerate_vectors=True,
        )

        return self.import_knowledge(import_path, config)

    def _generate_export_metadata(
        self, config: ExportConfig, project_id: Optional[str]
    ) -> Dict[str, Any]:
        """Generate metadata for the export package."""
        return {
            "export_timestamp": time.time(),
            "export_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "source_project": project_id,
            "export_config": asdict(config) if config else {},
            "memory_service_version": "1.0",
            "total_scopes": len(config.include_scopes) if config.include_scopes else 0,
        }

    def _export_scope(
        self,
        scope: MemoryScope,
        config: ExportConfig,
        project_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Export entries from a specific memory scope."""
        try:
            # Get entries from scope
            scope_query_map = {
                MemoryScope.GLOBAL: "*",
                MemoryScope.PROJECT: "type:note OR type:decision OR type:adr",
                MemoryScope.AGENT: "capability:* OR preference_type:*",
                MemoryScope.OBJECTIVES: "objective_type:* OR status:*",
                MemoryScope.ARTIFACTS: "artifact_type:* OR reference:*",
            }

            query = scope_query_map.get(scope, "*")
            entries = self.memory_service.search(
                query=query, scope=scope.value, limit=config.max_entries_per_scope
            )

            exported_entries = []
            for entry in entries:
                # Filter by importance if requested
                importance = entry.get("metadata", {}).get("importance", 0.5)
                if config.exclude_low_importance:
                    if importance < config.min_importance_threshold:
                        continue

                # Create export entry
                export_entry = {
                    "content": entry.get("content", ""),
                    "metadata": entry.get("metadata", {}),
                    "importance": importance,
                    "scope": scope.value,
                }

                # Include vector if requested
                if config.include_vectors and "vector" in entry:
                    export_entry["vector"] = entry["vector"]

                # Anonymize sensitive data if requested
                if config.anonymize_sensitive_data:
                    export_entry = self._anonymize_entry(export_entry)

                exported_entries.append(export_entry)

            return exported_entries

        except Exception as e:
            self.logger.error(f"Failed to export scope {scope.value}: {e}")
            return []

    def _import_scope_entries(
        self, scope_name: str, entries: List[Dict[str, Any]], config: ImportConfig
    ) -> Dict[str, Any]:
        """Import entries into a specific scope."""
        imported = 0
        skipped = 0
        errors = []

        scope_map = {
            "global": MemoryScope.GLOBAL,
            "project": MemoryScope.PROJECT,
            "agent": MemoryScope.AGENT,
            "objectives": MemoryScope.OBJECTIVES,
            "artifacts": MemoryScope.ARTIFACTS,
        }

        scope = scope_map.get(scope_name)
        if not scope:
            errors.append(f"Unknown scope: {scope_name}")
            return {"imported": 0, "skipped": len(entries), "errors": errors}

        for entry in entries:
            try:
                content = entry.get("content", "")
                metadata = entry.get("metadata", {})

                # Check if entry already exists (for skip_existing strategy)
                if config.merge_strategy == "skip_existing":
                    if self._entry_exists(content, scope, metadata):
                        skipped += 1
                        continue

                # Write to memory system
                options = MemoryWriteOptions(
                    scope=scope,
                    project_id=config.target_project_id,
                    importance=entry.get("importance", 0.5),
                    auto_embed=config.regenerate_vectors,
                )

                # Add import metadata
                metadata["imported"] = True
                metadata["import_timestamp"] = time.time()

                self.memory_service.write_event(content, options, metadata)
                imported += 1

            except Exception as e:
                errors.append(f"Failed to import entry: {str(e)}")
                continue

        return {"imported": imported, "skipped": skipped, "errors": errors}

    def _write_package_to_file(
        self, package: KnowledgePackage, output_path: str
    ) -> None:
        """Write knowledge package to JSON file."""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with output_file.open("w", encoding="utf-8") as f:
            json.dump(asdict(package), f, indent=2, ensure_ascii=False)

    def _load_package_from_file(self, import_path: str) -> KnowledgePackage:
        """Load knowledge package from JSON file."""
        import_file = Path(import_path)
        if not import_file.exists():
            raise FileNotFoundError(f"Import file not found: {import_path}")

        with import_file.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # Convert back to KnowledgePackage
        return KnowledgePackage(
            metadata=data.get("metadata", {}),
            global_knowledge=data.get("global_knowledge", []),
            project_knowledge=data.get("project_knowledge", []),
            agent_knowledge=data.get("agent_knowledge", []),
            objectives=data.get("objectives", []),
            artifacts=data.get("artifacts", []),
            export_timestamp=data.get("export_timestamp", time.time()),
            export_version=data.get("export_version", "1.0"),
        )

    def _validate_package(self, package: KnowledgePackage) -> Dict[str, Any]:
        """Validate a knowledge package before import."""
        errors = []
        warnings = []

        # Check package structure
        if not package.metadata:
            warnings.append("Package has no metadata")

        # Check version compatibility
        if package.export_version != "1.0":
            warnings.append(
                f"Package version {package.export_version} may not be fully compatible"
            )

        # Check age of export
        age_days = (time.time() - package.export_timestamp) / (24 * 3600)
        if age_days > 30:
            warnings.append(
                f"Package is {age_days:.0f} days old - may contain outdated information"
            )

        # Validate entries structure
        all_entries = (
            package.global_knowledge
            + package.project_knowledge
            + package.agent_knowledge
            + package.objectives
            + package.artifacts
        )

        for i, entry in enumerate(all_entries):
            if not entry.get("content"):
                errors.append(f"Entry {i} missing content")
            if not entry.get("metadata"):
                warnings.append(f"Entry {i} missing metadata")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "total_entries": len(all_entries),
        }

    def _entry_exists(
        self, content: str, scope: MemoryScope, metadata: Dict[str, Any]
    ) -> bool:
        """Check if an entry already exists in the memory system."""
        try:
            # Simple content-based check
            results = self.memory_service.search(
                query=content[:50], scope=scope.value, limit=5
            )

            for result in results:
                if result.get("content", "") == content:
                    return True
            return False

        except Exception:
            # If we can't check, assume it doesn't exist
            return False

    def _anonymize_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Anonymize sensitive data in an entry."""
        # This is a simplified implementation
        # In practice, you might want more sophisticated anonymization
        sensitive_keys = ["user_id", "email", "api_key", "password", "token"]

        anonymized = entry.copy()
        metadata = anonymized.get("metadata", {}).copy()

        for key in sensitive_keys:
            if key in metadata:
                metadata[key] = "[ANONYMIZED]"

        # Anonymize content patterns (basic implementation)
        content = anonymized.get("content", "")
        # Remove email patterns
        import re

        content = re.sub(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL]", content
        )
        # Remove potential API keys (long alphanumeric strings)
        content = re.sub(r"\b[A-Za-z0-9]{32,}\b", "[API_KEY]", content)

        anonymized["content"] = content
        anonymized["metadata"] = metadata

        return anonymized

    def _get_file_size(self, file_path: str) -> int:
        """Get file size in bytes."""
        try:
            return Path(file_path).stat().st_size
        except Exception:
            return 0

    def get_transfer_status(self) -> Dict[str, Any]:
        """Get current status of the knowledge transfer system."""
        return {
            "service_operational": True,
            "supported_formats": ["json"],
            "supported_scopes": [scope.value for scope in MemoryScope],
            "default_config": {
                "export": asdict(ExportConfig()),
                "import": asdict(ImportConfig()),
            },
        }

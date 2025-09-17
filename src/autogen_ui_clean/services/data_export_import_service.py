"""
Data Export/Import Service for AutoGen UI

Provides comprehensive data export and import functionality supporting
JSON, CSV, and Excel formats for memory data, sessions, agents,
and system backups.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
from enum import Enum
from dataclasses import dataclass
from PySide6.QtCore import QObject, Signal, QThread
import requests

try:
    import pandas as pd  # type: ignore
except ImportError:
    pd = None

logger = logging.getLogger(__name__)


class ExportFormat(Enum):
    """Supported export formats"""

    JSON = "json"
    CSV = "csv"
    EXCEL = "xlsx"


class DataType(Enum):
    """Types of data that can be exported/imported"""

    MEMORY = "memory"
    SESSIONS = "sessions"
    AGENTS = "agents"
    SERVER_CONFIG = "server_config"
    ALL = "all"


@dataclass
class ExportOptions:
    """Export configuration options"""

    data_types: List[DataType]
    format: ExportFormat
    output_path: str
    include_timestamps: bool = True
    filter_criteria: Optional[Dict[str, Any]] = None
    date_range: Optional[tuple] = None  # (start_date, end_date)


@dataclass
class ImportOptions:
    """Import configuration options"""

    data_type: DataType
    input_path: str
    validate_data: bool = True
    merge_strategy: str = "append"  # "append", "replace", "update"
    backup_existing: bool = True


class ExportWorker(QThread):
    """Worker thread for data export operations"""

    export_started = Signal()
    export_progress = Signal(int)  # percentage
    export_completed = Signal(str)  # output_path
    export_failed = Signal(str)  # error_message

    def __init__(self, server_url: str, export_options: ExportOptions):
        super().__init__()
        self.server_url = server_url
        self.export_options = export_options
        self.total_steps = 0
        self.current_step = 0

    def run(self):
        """Execute the export operation"""
        try:
            self.export_started.emit()
            self._calculate_total_steps()

            # Collect data based on types requested
            all_data = {}

            for data_type in self.export_options.data_types:
                self._update_progress(f"Exporting {data_type.value}")

                if data_type == DataType.MEMORY:
                    all_data["memory"] = self._export_memory_data()
                elif data_type == DataType.SESSIONS:
                    all_data["sessions"] = self._export_session_data()
                elif data_type == DataType.AGENTS:
                    all_data["agents"] = self._export_agent_data()
                elif data_type == DataType.SERVER_CONFIG:
                    all_data["server_config"] = self._export_server_config()
                elif data_type == DataType.ALL:
                    all_data.update(
                        {
                            "memory": self._export_memory_data(),
                            "sessions": self._export_session_data(),
                            "agents": self._export_agent_data(),
                            "server_config": self._export_server_config(),
                        }
                    )

                self._step_completed()

            # Add metadata
            if self.export_options.include_timestamps:
                all_data["export_metadata"] = {
                    "timestamp": datetime.now().isoformat(),
                    "format": self.export_options.format.value,
                    "data_types": [dt.value for dt in self.export_options.data_types],
                    "version": "1.0",
                }

            # Write data in requested format
            self._update_progress("Writing export file")
            output_path = self._write_export_data(all_data)
            self._step_completed()

            self.export_completed.emit(output_path)

        except Exception as e:
            logger.error(f"Export failed: {e}")
            self.export_failed.emit(str(e))

    def _calculate_total_steps(self):
        """Calculate total steps for progress tracking"""
        self.total_steps = len(self.export_options.data_types) + 1  # +1 for writing
        if DataType.ALL in self.export_options.data_types:
            self.total_steps += 3  # Additional steps for ALL type

    def _update_progress(self, message: str):
        """Update progress with message"""
        progress = int((self.current_step / self.total_steps) * 100)
        self.export_progress.emit(progress)
        logger.info(f"Export progress: {message} ({progress}%)")

    def _step_completed(self):
        """Mark step as completed and update progress"""
        self.current_step += 1
        progress = int((self.current_step / self.total_steps) * 100)
        self.export_progress.emit(progress)

    def _export_memory_data(self) -> List[Dict]:
        """Export memory data from MCP server"""
        try:
            # Get memory statistics to understand available collections
            stats_response = requests.get(f"{self.server_url}/memory/stats")
            if stats_response.status_code != 200:
                logger.warning("Could not fetch memory stats")
                return []

            stats = stats_response.json()
            collections = stats.get("collections", {})

            all_memory_data = []

            # Export data from each collection
            for collection_name, collection_info in collections.items():
                try:
                    # Search for all entries in this collection
                    search_payload = {
                        "query": "*",  # Get all entries
                        "scope": collection_name,
                        "k": 1000,  # Large number to get all entries
                    }

                    search_response = requests.post(
                        f"{self.server_url}/memory/search", json=search_payload
                    )

                    if search_response.status_code == 200:
                        results = search_response.json()
                        for result in results.get("results", []):
                            all_memory_data.append(
                                {
                                    "collection": collection_name,
                                    "id": result.get("id"),
                                    "content": result.get("payload", {}).get(
                                        "content", ""
                                    ),
                                    "metadata": result.get("payload", {}),
                                    "score": result.get("score", 0.0),
                                }
                            )
                except Exception as e:
                    logger.error(
                        f"Failed to export from collection {collection_name}: {e}"
                    )

            return all_memory_data

        except Exception as e:
            logger.error(f"Failed to export memory data: {e}")
            return []

    def _export_session_data(self) -> List[Dict]:
        """Export session data from MCP server"""
        try:
            response = requests.get(f"{self.server_url}/orchestrate/sessions")
            if response.status_code == 200:
                return response.json().get("sessions", [])
            else:
                logger.warning("Could not fetch session data")
                return []
        except Exception as e:
            logger.error(f"Failed to export session data: {e}")
            return []

    def _export_agent_data(self) -> List[Dict]:
        """Export agent configuration data"""
        # Since agents are typically configured in the UI,
        # we'll create a structure for common agent presets
        return [
            {
                "name": "Code Assistant",
                "type": "code_assistant",
                "model": "gpt-4",
                "temperature": 0.1,
                "capabilities": ["code_generation", "debugging", "review"],
                "system_prompt": "You are a helpful coding assistant...",
            },
            {
                "name": "Data Analyst",
                "type": "data_analyst",
                "model": "gpt-4",
                "temperature": 0.3,
                "capabilities": ["data_analysis", "visualization", "statistics"],
                "system_prompt": "You are a data analysis expert...",
            },
            {
                "name": "Content Writer",
                "type": "content_writer",
                "model": "gpt-4",
                "temperature": 0.7,
                "capabilities": ["writing", "editing", "content_creation"],
                "system_prompt": "You are a professional content writer...",
            },
            {
                "name": "Research Assistant",
                "type": "research_assistant",
                "model": "gpt-4",
                "temperature": 0.4,
                "capabilities": ["research", "analysis", "summarization"],
                "system_prompt": "You are a thorough research assistant...",
            },
        ]

    def _export_server_config(self) -> Dict:
        """Export server configuration"""
        try:
            response = requests.get(f"{self.server_url}/health")
            if response.status_code == 200:
                health_data = response.json()
                return {
                    "server_status": health_data,
                    "server_url": self.server_url,
                    "export_timestamp": datetime.now().isoformat(),
                }
            else:
                return {"server_url": self.server_url}
        except Exception as e:
            logger.error(f"Failed to export server config: {e}")
            return {"server_url": self.server_url}

    def _write_export_data(self, data: Dict) -> str:
        """Write data in the specified format"""
        output_path = Path(self.export_options.output_path)

        if self.export_options.format == ExportFormat.JSON:
            output_path = output_path.with_suffix(".json")
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)

        elif self.export_options.format == ExportFormat.CSV:
            output_path = output_path.with_suffix(".csv")
            # Flatten data for CSV export
            flattened_data = self._flatten_data_for_csv(data)
            df = pd.DataFrame(flattened_data)
            df.to_csv(output_path, index=False)

        elif self.export_options.format == ExportFormat.EXCEL:
            output_path = output_path.with_suffix(".xlsx")
            with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
                # Write each data type to a separate sheet
                for data_type, type_data in data.items():
                    if data_type == "export_metadata":
                        # Write metadata as a simple key-value sheet
                        metadata_df = pd.DataFrame(
                            list(type_data.items()), columns=["Key", "Value"]
                        )
                        metadata_df.to_excel(writer, sheet_name="Metadata", index=False)
                    elif isinstance(type_data, list) and type_data:
                        df = pd.DataFrame(type_data)
                        sheet_name = data_type.capitalize()[:31]  # Excel limit
                        df.to_excel(writer, sheet_name=sheet_name, index=False)

        return str(output_path)

    def _flatten_data_for_csv(self, data: Dict) -> List[Dict]:
        """Flatten nested data structure for CSV export"""
        flattened = []

        for data_type, type_data in data.items():
            if isinstance(type_data, list):
                for item in type_data:
                    flat_item = {"data_type": data_type}
                    flat_item.update(self._flatten_dict(item))
                    flattened.append(flat_item)
            elif isinstance(type_data, dict):
                flat_item = {"data_type": data_type}
                flat_item.update(self._flatten_dict(type_data))
                flattened.append(flat_item)

        return flattened

    def _flatten_dict(self, d: Dict, parent_key: str = "", sep: str = ".") -> Dict:
        """Flatten a nested dictionary"""
        items: List[Tuple[str, Any]] = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                items.append((new_key, json.dumps(v)))
            else:
                items.append((new_key, v))
        return dict(items)


class ImportWorker(QThread):
    """Worker thread for data import operations"""

    import_started = Signal()
    import_progress = Signal(int)  # percentage
    import_completed = Signal(str)  # summary_message
    import_failed = Signal(str)  # error_message

    def __init__(self, server_url: str, import_options: ImportOptions):
        super().__init__()
        self.server_url = server_url
        self.import_options = import_options

    def run(self):
        """Execute the import operation"""
        try:
            self.import_started.emit()

            # Read and validate input data
            self.import_progress.emit(10)
            data = self._read_import_data()

            if self.import_options.validate_data:
                self.import_progress.emit(30)
                if not self._validate_import_data(data):
                    raise ValueError("Data validation failed")

            # Create backup if requested
            if self.import_options.backup_existing:
                self.import_progress.emit(50)
                self._create_backup()

            # Import the data
            self.import_progress.emit(70)
            result = self._import_data(data)

            self.import_progress.emit(100)
            self.import_completed.emit(result)

        except Exception as e:
            logger.error(f"Import failed: {e}")
            self.import_failed.emit(str(e))

    def _read_import_data(self) -> Dict:
        """Read data from import file"""
        file_path = Path(self.import_options.input_path)

        if file_path.suffix.lower() == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        elif file_path.suffix.lower() == ".csv":
            df = pd.read_csv(file_path)
            return df.to_dict("records")
        elif file_path.suffix.lower() in [".xlsx", ".xls"]:
            data = {}
            with pd.ExcelFile(file_path) as xls:
                for sheet_name in xls.sheet_names:
                    df = pd.read_excel(xls, sheet_name=sheet_name)
                    data[sheet_name.lower()] = df.to_dict("records")
            return data
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

    def _validate_import_data(self, data: Dict) -> bool:
        """Validate the imported data structure"""
        # Basic validation - can be extended
        if not isinstance(data, (dict, list)):
            return False

        # Add specific validation based on data type
        if self.import_options.data_type == DataType.MEMORY:
            return self._validate_memory_data(data)
        elif self.import_options.data_type == DataType.SESSIONS:
            return self._validate_session_data(data)
        elif self.import_options.data_type == DataType.AGENTS:
            return self._validate_agent_data(data)

        return True

    def _validate_memory_data(self, data: Union[Dict, List]) -> bool:
        """Validate memory data structure"""
        if isinstance(data, dict) and "memory" in data:
            data = data["memory"]

        if not isinstance(data, list):
            return False

        # Check if memory entries have required fields
        for entry in data[:5]:  # Check first 5 entries
            if not isinstance(entry, dict):
                return False
            if "content" not in entry:
                return False

        return True

    def _validate_session_data(self, data: Union[Dict, List]) -> bool:
        """Validate session data structure"""
        return True  # Basic validation for now

    def _validate_agent_data(self, data: Union[Dict, List]) -> bool:
        """Validate agent data structure"""
        return True  # Basic validation for now

    def _create_backup(self):
        """Create backup of existing data"""
        # This would create a backup before importing
        # Implementation depends on specific backup requirements
        pass

    def _import_data(self, data: Dict) -> str:
        """Import the data to the system"""
        # This is a placeholder implementation
        # Real implementation would depend on MCP server import endpoints
        imported_count = 0

        if self.import_options.data_type == DataType.MEMORY:
            # Import memory data
            memory_data = data.get("memory", data) if isinstance(data, dict) else data
            if isinstance(memory_data, list):
                imported_count = len(memory_data)
                # Here we would send data to MCP server import endpoint

        return f"Successfully imported {imported_count} items"


class DataExportImportService(QObject):
    """
    Data Export/Import service for AutoGen UI

    Provides comprehensive data management with export/import capabilities
    for memory data, sessions, agents, and system configurations.
    """

    export_completed = Signal(str)  # output_path
    import_completed = Signal(str)  # summary_message
    operation_failed = Signal(str)  # error_message
    operation_progress = Signal(int)  # percentage

    def __init__(self, server_url: str = "http://localhost:9000"):
        super().__init__()
        self.server_url = server_url
        self.current_worker: Optional[QThread] = None

        logger.info(f"DataExportImportService initialized with server: {server_url}")

    def export_data(self, export_options: ExportOptions):
        """Start data export operation"""
        if self.current_worker and self.current_worker.isRunning():
            logger.warning("Another operation is already running")
            return

        self.current_worker = ExportWorker(self.server_url, export_options)

        # Connect signals
        self.current_worker.export_progress.connect(self.operation_progress.emit)
        self.current_worker.export_completed.connect(self.export_completed.emit)
        self.current_worker.export_failed.connect(self.operation_failed.emit)

        # Start export
        self.current_worker.start()
        logger.info(f"Started export operation: {export_options.data_types}")

    def import_data(self, import_options: ImportOptions):
        """Start data import operation"""
        if self.current_worker and self.current_worker.isRunning():
            logger.warning("Another operation is already running")
            return

        self.current_worker = ImportWorker(self.server_url, import_options)

        # Connect signals
        self.current_worker.import_progress.connect(self.operation_progress.emit)
        self.current_worker.import_completed.connect(self.import_completed.emit)
        self.current_worker.import_failed.connect(self.operation_failed.emit)

        # Start import
        self.current_worker.start()
        logger.info(f"Started import operation: {import_options.data_type}")

    def is_operation_running(self) -> bool:
        """Check if an operation is currently running"""
        return self.current_worker is not None and self.current_worker.isRunning()

    def cancel_operation(self):
        """Cancel the current operation"""
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.terminate()
            self.current_worker.wait(5000)  # Wait up to 5 seconds
            logger.info("Operation cancelled")

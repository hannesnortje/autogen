"""
Memory Browser Widget - Clean Implementation
Browse and search Qdrant memory collections
"""

import logging
import requests
from typing import Dict, List
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLineEdit,
    QPushButton,
    QComboBox,
    QSpinBox,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
    QTextEdit,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QFrame,
    QMessageBox,
    QCheckBox,
    QFileDialog,
    QProgressBar,
)
from PySide6.QtCore import QTimer, Signal, QThread
from PySide6.QtGui import QFont

logger = logging.getLogger(__name__)


class MemoryWorker(QThread):
    """Worker thread for memory operations"""

    search_completed = Signal(list)
    stats_completed = Signal(dict)
    collections_completed = Signal(list)
    upload_completed = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, server_url: str):
        super().__init__()
        self.server_url = server_url
        self.operation = None
        self.params = {}

    def search_memory(self, query: str, collection: str, limit: int = 10):
        """Search memory entries"""
        self.operation = "search"
        self.params = {"query": query, "collection": collection, "limit": limit}
        self.start()

    def get_stats(self):
        """Get memory statistics"""
        self.operation = "stats"
        self.params = {}
        self.start()

    def get_collections(self):
        """Get available collections"""
        self.operation = "collections"
        self.params = {}
        self.start()

    def upload_file(self, file_path: str, project: str, scope: str):
        """Upload file to memory"""
        self.operation = "upload"
        self.params = {"file_path": file_path, "project": project, "scope": scope}
        self.start()

    def run(self):
        """Execute the operation"""
        try:
            if self.operation == "search":
                self._search()
            elif self.operation == "stats":
                self._get_stats()
            elif self.operation == "collections":
                self._get_collections()
            elif self.operation == "upload":
                self._upload_file()
        except Exception as e:
            self.error_occurred.emit(str(e))

    def _search(self):
        """Perform memory search"""
        try:
            response = requests.post(
                f"{self.server_url}/memory/search",
                json={
                    "query": self.params["query"],
                    "collection": self.params["collection"],
                    "k": self.params["limit"],
                },
                timeout=30,
            )
            if response.status_code == 200:
                results = response.json()
                self.search_completed.emit(results.get("results", []))
            else:
                self.error_occurred.emit(f"Search failed: {response.status_code}")
        except requests.RequestException as e:
            self.error_occurred.emit(f"Search request failed: {e}")

    def _get_stats(self):
        """Get memory statistics"""
        try:
            response = requests.get(f"{self.server_url}/memory/stats", timeout=10)
            if response.status_code == 200:
                self.stats_completed.emit(response.json())
            else:
                self.error_occurred.emit(f"Stats failed: {response.status_code}")
        except requests.RequestException as e:
            self.error_occurred.emit(f"Stats request failed: {e}")

    def _get_collections(self):
        """Get available collections"""
        try:
            response = requests.get(f"{self.server_url}/collections", timeout=10)
            if response.status_code == 200:
                data = response.json()
                collections = data.get("collections", [])
                self.collections_completed.emit(collections)
            else:
                self.error_occurred.emit(f"Collections failed: {response.status_code}")
        except requests.RequestException as e:
            self.error_occurred.emit(f"Collections request failed: {e}")

    def _upload_file(self):
        """Upload file to memory"""
        try:
            file_path = self.params["file_path"]
            project = self.params["project"]
            scope = self.params["scope"]

            # Read file content
            with open(file_path, "rb") as f:
                files = {"file": (file_path.split("/")[-1], f, "text/markdown")}
                data = {"project": project, "scope": scope}

                response = requests.post(
                    f"{self.server_url}/memory/upload",
                    files=files,
                    data=data,
                    timeout=60,  # Longer timeout for file upload
                )

            if response.status_code == 200:
                result = response.json()
                self.upload_completed.emit(result)
            else:
                self.error_occurred.emit(
                    f"Upload failed: {response.status_code} - {response.text}"
                )

        except requests.RequestException as e:
            self.error_occurred.emit(f"Upload request failed: {e}")
        except FileNotFoundError:
            self.error_occurred.emit(f"File not found: {file_path}")
        except Exception as e:
            self.error_occurred.emit(f"Upload error: {e}")


class MemoryBrowserWidget(QWidget):
    """Advanced memory browser with search and analytics"""

    memory_selected = Signal(dict)

    def __init__(self, server_url: str):
        super().__init__()
        self.server_url = server_url
        self.worker = MemoryWorker(server_url)
        self.collections = []
        self.current_results = []

        self.setup_ui()
        self.setup_connections()
        self.setup_timer()

        # Add startup delay to prevent connection errors
        self._startup_delay_timer = QTimer()
        self._startup_delay_timer.setSingleShot(True)
        self._startup_delay_timer.timeout.connect(self.refresh_data)
        self._startup_delay_timer.start(3000)  # Wait 3 seconds before first load

    def setup_ui(self):
        """Set up the memory browser UI"""
        layout = QVBoxLayout(self)

        # Connection status
        self.setup_status_bar(layout)

        # Search controls
        self.setup_search_controls(layout)

        # Main content area with tabs
        self.setup_main_content(layout)

    def setup_status_bar(self, layout):
        """Set up memory connection status"""
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.StyledPanel)
        status_frame.setMaximumHeight(35)
        status_layout = QHBoxLayout(status_frame)

        self.status_label = QLabel("Memory: Connecting...")
        self.status_label.setStyleSheet(
            "QLabel { color: orange; font-weight: bold; padding: 4px; }"
        )

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setMaximumWidth(80)
        self.refresh_btn.clicked.connect(self.refresh_data)

        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.refresh_btn)

        layout.addWidget(status_frame)

    def setup_search_controls(self, layout):
        """Set up search interface"""
        search_group = QGroupBox("Memory Search")
        search_layout = QVBoxLayout(search_group)

        # Search input row
        search_row = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter search query...")
        self.search_input.returnPressed.connect(self.perform_search)

        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self.perform_search)
        self.search_btn.setMaximumWidth(80)

        search_row.addWidget(self.search_input)
        search_row.addWidget(self.search_btn)
        search_layout.addLayout(search_row)

        # Search options
        options_row = QHBoxLayout()

        options_row.addWidget(QLabel("Collection:"))
        self.collection_combo = QComboBox()
        self.collection_combo.setMinimumWidth(120)
        options_row.addWidget(self.collection_combo)

        options_row.addWidget(QLabel("Limit:"))
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(1, 100)
        self.limit_spin.setValue(10)
        self.limit_spin.setMaximumWidth(60)
        options_row.addWidget(self.limit_spin)

        self.auto_search_cb = QCheckBox("Auto-search")
        self.auto_search_cb.setToolTip("Automatically search as you type")
        options_row.addWidget(self.auto_search_cb)

        options_row.addStretch()
        search_layout.addLayout(options_row)

        layout.addWidget(search_group)

    def setup_main_content(self, layout):
        """Set up main tabbed content area"""
        self.tab_widget = QTabWidget()

        # Results tab
        self.setup_results_tab()

        # Upload tab - NEW
        self.setup_upload_tab()

        # Statistics tab
        self.setup_statistics_tab()

        # Collections tab
        self.setup_collections_tab()

        layout.addWidget(self.tab_widget)

    def setup_results_tab(self):
        """Set up search results tab"""
        results_widget = QWidget()
        results_layout = QVBoxLayout(results_widget)

        # Results header
        header_layout = QHBoxLayout()
        self.results_label = QLabel("No search performed")
        header_layout.addWidget(self.results_label)
        header_layout.addStretch()

        self.clear_btn = QPushButton("Clear Results")
        self.clear_btn.clicked.connect(self.clear_results)
        self.clear_btn.setMaximumWidth(100)
        header_layout.addWidget(self.clear_btn)

        results_layout.addLayout(header_layout)

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(
            ["Score", "Content", "Metadata", "Timestamp"]
        )
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.itemSelectionChanged.connect(self.on_result_selected)

        results_layout.addWidget(self.results_table)

        # Selected result details
        details_group = QGroupBox("Selected Result Details")
        details_layout = QVBoxLayout(details_group)

        self.details_text = QTextEdit()
        self.details_text.setMaximumHeight(150)
        self.details_text.setReadOnly(True)
        details_layout.addWidget(self.details_text)

        results_layout.addWidget(details_group)

        self.tab_widget.addTab(results_widget, "Search Results")

    def setup_upload_tab(self):
        """Set up file upload tab"""
        upload_widget = QWidget()
        upload_layout = QVBoxLayout(upload_widget)

        # Upload instructions
        instructions_group = QGroupBox("File Upload Instructions")
        instructions_layout = QVBoxLayout(instructions_group)

        instructions_text = QTextEdit()
        instructions_text.setReadOnly(True)
        instructions_text.setMaximumHeight(100)
        instructions_text.setHtml(
            """
        <b>Upload Markdown Files to Memory</b><br>
        • Select .md files to add to the knowledge base<br>
        • Files will be chunked and indexed for search<br>
        • Choose appropriate project and scope settings
        """
        )
        instructions_layout.addWidget(instructions_text)
        upload_layout.addWidget(instructions_group)

        # File selection
        file_group = QGroupBox("File Selection")
        file_layout = QVBoxLayout(file_group)

        # File path display
        file_path_layout = QHBoxLayout()
        self.file_path_label = QLabel("No file selected")
        self.file_path_label.setStyleSheet("color: gray; font-style: italic;")
        file_path_layout.addWidget(QLabel("Selected File:"))
        file_path_layout.addWidget(self.file_path_label, 1)

        self.browse_btn = QPushButton("Browse Files...")
        self.browse_btn.clicked.connect(self.browse_files)
        file_path_layout.addWidget(self.browse_btn)

        file_layout.addLayout(file_path_layout)
        upload_layout.addWidget(file_group)

        # Upload settings
        settings_group = QGroupBox("Upload Settings")
        settings_layout = QHBoxLayout(settings_group)

        settings_layout.addWidget(QLabel("Project:"))
        self.project_input = QLineEdit("default")
        self.project_input.setPlaceholderText("Enter project name")
        settings_layout.addWidget(self.project_input)

        settings_layout.addWidget(QLabel("Scope:"))
        self.scope_combo = QComboBox()
        self.scope_combo.addItems(["project", "global", "artifacts"])
        settings_layout.addWidget(self.scope_combo)

        upload_layout.addWidget(settings_group)

        # Upload controls
        controls_layout = QHBoxLayout()

        self.upload_btn = QPushButton("Upload to Memory")
        self.upload_btn.setEnabled(False)
        self.upload_btn.clicked.connect(self.upload_file)
        controls_layout.addWidget(self.upload_btn)

        controls_layout.addStretch()

        self.clear_selection_btn = QPushButton("Clear Selection")
        self.clear_selection_btn.clicked.connect(self.clear_file_selection)
        controls_layout.addWidget(self.clear_selection_btn)

        upload_layout.addLayout(controls_layout)

        # Upload progress
        progress_group = QGroupBox("Upload Progress")
        progress_layout = QVBoxLayout(progress_group)

        self.upload_progress = QProgressBar()
        self.upload_progress.setVisible(False)
        progress_layout.addWidget(self.upload_progress)

        self.upload_status = QTextEdit()
        self.upload_status.setReadOnly(True)
        self.upload_status.setMaximumHeight(100)
        self.upload_status.setPlaceholderText("Upload status will appear here...")
        progress_layout.addWidget(self.upload_status)

        upload_layout.addWidget(progress_group)

        upload_layout.addStretch()

        self.tab_widget.addTab(upload_widget, "Upload Files")

    def setup_statistics_tab(self):
        """Set up memory statistics tab"""
        stats_widget = QWidget()
        stats_layout = QVBoxLayout(stats_widget)

        # Statistics display
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setFont(QFont("monospace"))
        stats_layout.addWidget(self.stats_text)

        # Refresh button
        refresh_stats_btn = QPushButton("Refresh Statistics")
        refresh_stats_btn.clicked.connect(self.refresh_stats)
        stats_layout.addWidget(refresh_stats_btn)

        self.tab_widget.addTab(stats_widget, "Statistics")

    def setup_collections_tab(self):
        """Set up collections management tab"""
        collections_widget = QWidget()
        collections_layout = QVBoxLayout(collections_widget)

        # Collections tree
        self.collections_tree = QTreeWidget()
        self.collections_tree.setHeaderLabels(
            ["Collection", "Documents", "Vectors", "Status"]
        )
        collections_layout.addWidget(self.collections_tree)

        # Collection actions
        actions_layout = QHBoxLayout()

        refresh_collections_btn = QPushButton("Refresh Collections")
        refresh_collections_btn.clicked.connect(self.refresh_collections)
        actions_layout.addWidget(refresh_collections_btn)

        actions_layout.addStretch()
        collections_layout.addLayout(actions_layout)

        self.tab_widget.addTab(collections_widget, "Collections")

    def setup_connections(self):
        """Set up signal connections"""
        # Worker signals
        self.worker.search_completed.connect(self.on_search_completed)
        self.worker.stats_completed.connect(self.on_stats_completed)
        self.worker.collections_completed.connect(self.on_collections_completed)
        self.worker.upload_completed.connect(self.on_upload_completed)
        self.worker.error_occurred.connect(self.on_error_occurred)

        # Auto-search
        self.search_input.textChanged.connect(self.on_search_text_changed)

    def setup_timer(self):
        """Set up periodic refresh timer"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_stats)
        self.timer.start(30000)  # Refresh stats every 30 seconds

    def refresh_data(self):
        """Refresh all data"""
        self.refresh_collections()
        self.refresh_stats()

    def refresh_collections(self):
        """Refresh collections list"""
        self.worker.get_collections()

    def refresh_stats(self):
        """Refresh memory statistics"""
        # Add a small delay to prevent connection errors during startup
        if (
            hasattr(self, "_startup_delay_timer")
            and self._startup_delay_timer.isActive()
        ):
            return  # Still in startup delay, skip this request

        self.worker.get_stats()

    def perform_search(self):
        """Perform memory search"""
        query = self.search_input.text().strip()
        if not query:
            return

        collection = self.collection_combo.currentText()
        if not collection:
            QMessageBox.warning(self, "Warning", "Please select a collection")
            return

        limit = self.limit_spin.value()

        self.results_label.setText("Searching...")
        self.search_btn.setEnabled(False)

        self.worker.search_memory(query, collection, limit)

    def clear_results(self):
        """Clear search results"""
        self.results_table.setRowCount(0)
        self.details_text.clear()
        self.results_label.setText("Results cleared")
        self.current_results = []

    def on_search_text_changed(self):
        """Handle search text changes for auto-search"""
        if self.auto_search_cb.isChecked():
            # Debounce auto-search
            if hasattr(self, "auto_search_timer"):
                self.auto_search_timer.stop()
            else:
                self.auto_search_timer = QTimer()
                self.auto_search_timer.setSingleShot(True)
                self.auto_search_timer.timeout.connect(self.perform_search)

            self.auto_search_timer.start(500)  # 500ms delay

    def on_search_completed(self, results: List[Dict]):
        """Handle search completion"""
        self.search_btn.setEnabled(True)
        self.current_results = results

        self.results_table.setRowCount(len(results))

        for row, result in enumerate(results):
            # Score
            score_item = QTableWidgetItem(f"{result.get('score', 0.0):.3f}")
            self.results_table.setItem(row, 0, score_item)

            # Content preview
            content = result.get("payload", {}).get("content", "No content")
            # Truncate long content for preview
            if len(content) > 100:
                content_preview = content[:100] + "..."
            else:
                content_preview = content
            content_item = QTableWidgetItem(content_preview)
            self.results_table.setItem(row, 1, content_item)

            # Metadata
            metadata = result.get("payload", {})
            metadata_str = f"Scope: {metadata.get('scope', 'N/A')}"
            metadata_item = QTableWidgetItem(metadata_str)
            self.results_table.setItem(row, 2, metadata_item)

            # Timestamp
            timestamp = metadata.get("timestamp", "N/A")
            timestamp_item = QTableWidgetItem(str(timestamp))
            self.results_table.setItem(row, 3, timestamp_item)

        self.results_label.setText(f"Found {len(results)} results")

        # Auto-resize columns
        self.results_table.resizeColumnsToContents()

    def on_stats_completed(self, stats: Dict):
        """Handle statistics completion"""
        self.status_label.setText("Memory: Connected")
        self.status_label.setStyleSheet(
            "QLabel { color: green; font-weight: bold; padding: 4px; }"
        )

        # Format statistics
        stats_text = "Memory Statistics\n"
        stats_text += "=" * 50 + "\n\n"

        # New simplified stats format from API
        if isinstance(stats, dict) and (
            "total_documents" in stats or "total_collections" in stats
        ):
            total_docs = stats.get("total_documents", 0)
            total_cols = stats.get("total_collections", 0)
            ready_cols = stats.get("collections_ready", 0)
            status = stats.get("status", "unknown")
            message = stats.get("message", "")

            stats_text += f"Status: {status}\n"
            stats_text += f"Total Collections: {total_cols}\n"
            stats_text += f"Collections Ready: {ready_cols}\n"
            stats_text += f"Total Documents: {total_docs}\n"
            if message:
                stats_text += f"Message: {message}\n"

        else:
            # Legacy per-collection dict format (backward compatibility)
            for collection, data in stats.items():
                if isinstance(data, dict):
                    stats_text += f"Collection: {collection}\n"
                    stats_text += f"  Documents: {data.get('documents_count', 0)}\n"
                    stats_text += f"  Vectors: {data.get('vectors_count', 0)}\n"
                    stats_text += f"  Points: {data.get('points_count', 0)}\n"
                    stats_text += f"  Indexed: {data.get('indexed_vectors_count', 0)}\n"
                    stats_text += "\n"

        self.stats_text.setPlainText(stats_text)

    def on_collections_completed(self, collections: List[Dict] | List[str]):
        """Handle collections list completion

        Supports both formats:
        - List[str]: ["collection_a", "collection_b", ...]
                        - List[dict]:
                            {"name": str, "documents": int,
                             "vectors": int, "status": str}, ...
        """
        # Normalize to names list for the combo box
        names: List[str] = []
        if collections and isinstance(collections[0], dict):
            # type: ignore[index] for heterogeneous list typing at runtime
            names = [c.get("name", "") for c in collections]
        else:
            names = [str(c) for c in collections]

        self.collections = names

        # Update combo box
        current_selection = self.collection_combo.currentText()
        self.collection_combo.clear()
        self.collection_combo.addItems(names)

        # Restore selection if possible
        if current_selection in names:
            index = names.index(current_selection)
            self.collection_combo.setCurrentIndex(index)
        elif names:
            self.collection_combo.setCurrentIndex(0)

        # Update collections tree with details if available
        self.collections_tree.clear()
        if collections and isinstance(collections[0], dict):
            for col in collections:  # type: ignore[assignment]
                name = col.get("name", "unknown")
                docs = str(col.get("documents", 0))
                vecs = str(col.get("vectors", 0))
                status = col.get("status", "Active")
                item = QTreeWidgetItem([name, docs, vecs, status])
                self.collections_tree.addTopLevelItem(item)
        else:
            for name in names:
                item = QTreeWidgetItem(
                    [
                        name,
                        "Loading...",
                        "Loading...",
                        "Active",
                    ]
                )
                self.collections_tree.addTopLevelItem(item)

    def on_error_occurred(self, error: str):
        """Handle worker errors"""
        self.search_btn.setEnabled(True)
        self.status_label.setText("Memory: Error")
        self.status_label.setStyleSheet(
            "QLabel { color: red; font-weight: bold; padding: 4px; }"
        )

        # Show error in stats tab
        self.stats_text.setPlainText(f"Error: {error}")

        # Handle upload errors
        if hasattr(self, "upload_progress"):
            self.upload_progress.setVisible(False)
            self.upload_btn.setEnabled(True)
            self.upload_status.append(f"❌ ERROR: {error}")

        logger.error(f"Memory browser error: {error}")

    def on_result_selected(self):
        """Handle result selection"""
        current_row = self.results_table.currentRow()
        if 0 <= current_row < len(self.current_results):
            result = self.current_results[current_row]

            # Format detailed view
            details = "Selected Memory Entry\n"
            details += "=" * 30 + "\n\n"

            details += f"Score: {result.get('score', 'N/A')}\n"
            details += f"ID: {result.get('id', 'N/A')}\n\n"

            payload = result.get("payload", {})
            details += f"Content:\n{payload.get('content', 'No content')}\n\n"

            details += "Metadata:\n"
            for key, value in payload.items():
                if key != "content":
                    details += f"  {key}: {value}\n"

            self.details_text.setPlainText(details)

            # Emit signal for external handling
            self.memory_selected.emit(result)

    def browse_files(self):
        """Open file dialog to select markdown files"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Markdown File",
            "",
            "Markdown files (*.md);;All files (*.*)",
        )

        if file_path:
            self.file_path_label.setText(file_path)
            self.file_path_label.setStyleSheet("color: black;")
            self.upload_btn.setEnabled(True)
            self.selected_file_path = file_path

    def clear_file_selection(self):
        """Clear the selected file"""
        self.file_path_label.setText("No file selected")
        self.file_path_label.setStyleSheet("color: gray; font-style: italic;")
        self.upload_btn.setEnabled(False)
        self.selected_file_path = None
        self.upload_status.clear()

    def upload_file(self):
        """Upload the selected file to memory"""
        if not hasattr(self, "selected_file_path") or not self.selected_file_path:
            QMessageBox.warning(self, "Warning", "Please select a file first")
            return

        project = self.project_input.text().strip() or "default"
        scope = self.scope_combo.currentText()

        # Show progress
        self.upload_progress.setVisible(True)
        self.upload_progress.setRange(0, 0)  # Indeterminate progress
        self.upload_btn.setEnabled(False)

        # Add status message
        self.upload_status.append(f"Uploading {self.selected_file_path}...")
        self.upload_status.append(f"Project: {project}, Scope: {scope}")

        # Start upload
        self.worker.upload_file(self.selected_file_path, project, scope)

    def on_upload_completed(self, result: dict):
        """Handle upload completion"""
        self.upload_progress.setVisible(False)
        self.upload_btn.setEnabled(True)

        # Show success message
        filename = result.get("filename", "Unknown")
        chunks = result.get("chunks_processed", 0)
        message = result.get("message", "Upload completed")

        self.upload_status.append(f"✅ SUCCESS: {message}")
        self.upload_status.append(f"📄 File: {filename}")
        self.upload_status.append(f"📝 Chunks processed: {chunks}")

        # Show success dialog
        QMessageBox.information(
            self,
            "Upload Successful",
            (
                f"Successfully uploaded {filename}\n"
                f"Processed {chunks} chunks\n\n{message}"
            ),
        )

        # Refresh data to show updated statistics
        self.refresh_data()

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
)
from PySide6.QtCore import QTimer, Signal, QThread
from PySide6.QtGui import QFont

logger = logging.getLogger(__name__)


class MemoryWorker(QThread):
    """Worker thread for memory operations"""

    search_completed = Signal(list)
    stats_completed = Signal(dict)
    collections_completed = Signal(list)
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

    def run(self):
        """Execute the operation"""
        try:
            if self.operation == "search":
                self._search()
            elif self.operation == "stats":
                self._get_stats()
            elif self.operation == "collections":
                self._get_collections()
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

        # Initial load
        self.refresh_data()

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
            content_preview = (content[:100] + "...") if len(content) > 100 else content
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

        for collection, data in stats.items():
            if isinstance(data, dict):
                stats_text += f"Collection: {collection}\n"
                stats_text += f"  Documents: {data.get('documents_count', 0)}\n"
                stats_text += f"  Vectors: {data.get('vectors_count', 0)}\n"
                stats_text += f"  Points: {data.get('points_count', 0)}\n"
                stats_text += f"  Indexed: {data.get('indexed_vectors_count', 0)}\n"
                stats_text += "\n"

        self.stats_text.setPlainText(stats_text)

    def on_collections_completed(self, collections: List[str]):
        """Handle collections list completion"""
        self.collections = collections

        # Update combo box
        current_selection = self.collection_combo.currentText()
        self.collection_combo.clear()
        self.collection_combo.addItems(collections)

        # Restore selection if possible
        if current_selection in collections:
            index = collections.index(current_selection)
            self.collection_combo.setCurrentIndex(index)
        elif collections:
            self.collection_combo.setCurrentIndex(0)

        # Update collections tree
        self.collections_tree.clear()
        for collection in collections:
            item = QTreeWidgetItem([collection, "Loading...", "Loading...", "Active"])
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

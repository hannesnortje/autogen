"""Memory browser widget for AutoGen UI.

This module provides a comprehensive memory browser interface for viewing,
searching, and managing Qdrant memory entries with real-time updates.
"""

import asyncio
from typing import List, Dict, Any
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QTableWidget,
    QTableWidgetItem,
    QLineEdit,
    QComboBox,
    QPushButton,
    QLabel,
    QGroupBox,
    QProgressBar,
    QTextEdit,
    QTabWidget,
    QFrame,
    QAbstractItemView,
    QMessageBox,
    QSpinBox,
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread
from PySide6.QtGui import QFont

from autogen_ui.services import MemoryService, IntegrationConfig


class MemoryWorker(QThread):
    """Worker thread for memory operations to avoid blocking UI."""

    # Signals for thread-safe communication
    search_completed = Signal(list)
    stats_updated = Signal(dict)
    health_updated = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, memory_service: MemoryService):
        super().__init__()
        self.memory_service = memory_service
        self.operation = None
        self.params = {}

    def search_memory(self, query: str, scope: str, k: int, threshold: float):
        """Schedule memory search operation."""
        self.operation = "search"
        self.params = {"query": query, "scope": scope, "k": k, "threshold": threshold}
        self.start()

    def get_stats(self):
        """Schedule memory stats retrieval."""
        self.operation = "stats"
        self.params = {}
        self.start()

    def get_health(self):
        """Schedule memory health check."""
        self.operation = "health"
        self.params = {}
        self.start()

    def run(self):
        """Execute the scheduled operation."""
        try:
            if self.operation == "search":
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                results = loop.run_until_complete(
                    self.memory_service.search_memory(**self.params)
                )
                self.search_completed.emit(results)
            elif self.operation == "stats":
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                stats = loop.run_until_complete(self.memory_service.get_memory_stats())
                self.stats_updated.emit(stats)
            elif self.operation == "health":
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                health = loop.run_until_complete(
                    self.memory_service.get_memory_health()
                )
                self.health_updated.emit(health)
        except Exception as e:
            self.error_occurred.emit(str(e))


class MemoryBrowserWidget(QWidget):
    """Comprehensive memory browser for Qdrant integration.

    Features:
    - Hierarchical memory view by scope (conversation/project/global)
    - Real-time search with filters
    - Memory statistics and health monitoring
    - Memory entry details and metadata view
    """

    # Signals for external communication
    memory_selected = Signal(dict)  # memory_entry
    search_performed = Signal(str, str)  # query, scope

    def __init__(self, parent=None):
        super().__init__(parent)
        self.memory_service = None
        self.memory_worker = None
        self.current_memories = []

        self._setup_ui()
        self._setup_connections()
        self._setup_timers()

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Connection status bar
        self._setup_connection_status(layout)

        # Search controls
        self._setup_search_controls(layout)

        # Main content area
        self._setup_main_content(layout)

        # Statistics panel
        self._setup_statistics_panel(layout)

    def _setup_connection_status(self, layout):
        """Set up memory connection status indicator."""
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.StyledPanel)
        status_frame.setMaximumHeight(40)
        status_layout = QHBoxLayout(status_frame)

        self.connection_status = QLabel("Memory: Connecting...")
        self.connection_status.setStyleSheet(
            """
            QLabel {
                color: orange;
                font-weight: bold;
                padding: 4px 8px;
                border-radius: 4px;
                background-color: rgba(255, 165, 0, 0.1);
            }
        """
        )

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setMaximumWidth(80)
        self.refresh_button.clicked.connect(self._refresh_data)

        status_layout.addWidget(self.connection_status)
        status_layout.addStretch()
        status_layout.addWidget(self.refresh_button)

        layout.addWidget(status_frame)

    def _setup_search_controls(self, layout):
        """Set up memory search controls."""
        search_group = QGroupBox("Memory Search")
        search_layout = QVBoxLayout(search_group)

        # Search input row
        search_row = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter search query...")
        self.search_input.returnPressed.connect(self._perform_search)

        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self._perform_search)
        self.search_button.setMaximumWidth(80)

        search_row.addWidget(self.search_input)
        search_row.addWidget(self.search_button)
        search_layout.addLayout(search_row)

        # Search options row
        options_row = QHBoxLayout()

        # Scope selector
        options_row.addWidget(QLabel("Scope:"))
        self.scope_combo = QComboBox()
        self.scope_combo.addItems(["conversation", "project", "global"])
        self.scope_combo.setMaximumWidth(120)
        options_row.addWidget(self.scope_combo)

        # Results limit
        options_row.addWidget(QLabel("Results:"))
        self.limit_spinner = QSpinBox()
        self.limit_spinner.setRange(1, 100)
        self.limit_spinner.setValue(10)
        self.limit_spinner.setMaximumWidth(70)
        options_row.addWidget(self.limit_spinner)

        # Threshold
        options_row.addWidget(QLabel("Threshold:"))
        self.threshold_combo = QComboBox()
        self.threshold_combo.addItems(["0.0", "0.3", "0.5", "0.7", "0.9"])
        self.threshold_combo.setCurrentText("0.5")
        self.threshold_combo.setMaximumWidth(60)
        options_row.addWidget(self.threshold_combo)

        options_row.addStretch()
        search_layout.addLayout(options_row)

        layout.addWidget(search_group)

    def _setup_main_content(self, layout):
        """Set up main content area with splitter."""
        main_splitter = QSplitter(Qt.Horizontal)

        # Memory tree (left side)
        self._setup_memory_tree(main_splitter)

        # Memory details (right side)
        self._setup_memory_details(main_splitter)

        # Set splitter proportions
        main_splitter.setSizes([300, 400])

        layout.addWidget(main_splitter)

    def _setup_memory_tree(self, parent):
        """Set up hierarchical memory tree."""
        tree_widget = QWidget()
        tree_layout = QVBoxLayout(tree_widget)

        tree_label = QLabel("Memory Entries")
        tree_label.setFont(QFont("", 10, QFont.Bold))
        tree_layout.addWidget(tree_label)

        self.memory_tree = QTreeWidget()
        self.memory_tree.setHeaderLabels(["Content", "Scope", "Score", "Date"])
        self.memory_tree.setAlternatingRowColors(True)
        self.memory_tree.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.memory_tree.itemSelectionChanged.connect(self._on_memory_selected)

        # Configure columns
        header = self.memory_tree.header()
        header.resizeSection(0, 200)  # Content
        header.resizeSection(1, 80)  # Scope
        header.resizeSection(2, 60)  # Score
        header.resizeSection(3, 100)  # Date

        tree_layout.addWidget(self.memory_tree)
        parent.addWidget(tree_widget)

    def _setup_memory_details(self, parent):
        """Set up memory details panel."""
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)

        details_label = QLabel("Memory Details")
        details_label.setFont(QFont("", 10, QFont.Bold))
        details_layout.addWidget(details_label)

        # Tabbed details view
        details_tabs = QTabWidget()

        # Content tab
        self.content_text = QTextEdit()
        self.content_text.setReadOnly(True)
        self.content_text.setPlaceholderText("Select a memory entry to view content...")
        details_tabs.addTab(self.content_text, "Content")

        # Metadata tab
        self.metadata_table = QTableWidget()
        self.metadata_table.setColumnCount(2)
        self.metadata_table.setHorizontalHeaderLabels(["Property", "Value"])
        self.metadata_table.horizontalHeader().setStretchLastSection(True)
        details_tabs.addTab(self.metadata_table, "Metadata")

        details_layout.addWidget(details_tabs)
        parent.addWidget(details_widget)

    def _setup_statistics_panel(self, layout):
        """Set up memory statistics panel."""
        stats_group = QGroupBox("Memory Statistics")
        stats_layout = QHBoxLayout(stats_group)

        # Entry count
        self.total_entries_label = QLabel("Entries: --")
        stats_layout.addWidget(self.total_entries_label)

        # Memory usage
        self.memory_usage_label = QLabel("Usage: --")
        stats_layout.addWidget(self.memory_usage_label)

        # Health status
        self.health_status_label = QLabel("Health: Unknown")
        stats_layout.addWidget(self.health_status_label)

        # Progress bar for operations
        self.operation_progress = QProgressBar()
        self.operation_progress.setVisible(False)
        stats_layout.addWidget(self.operation_progress)

        stats_layout.addStretch()
        layout.addWidget(stats_group)

    def _setup_connections(self):
        """Set up signal connections."""
        pass

    def _setup_timers(self):
        """Set up refresh timers."""
        # Stats refresh timer
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self._refresh_stats)
        self.stats_timer.start(10000)  # Refresh every 10 seconds

        # Health check timer
        self.health_timer = QTimer()
        self.health_timer.timeout.connect(self._check_health)
        self.health_timer.start(30000)  # Check every 30 seconds

    def initialize_memory_service(self, config: IntegrationConfig):
        """Initialize memory service with configuration."""
        try:
            self.memory_service = MemoryService(config, self)
            self.memory_worker = MemoryWorker(self.memory_service)

            # Connect worker signals
            self.memory_worker.search_completed.connect(self._on_search_completed)
            self.memory_worker.stats_updated.connect(self._on_stats_updated)
            self.memory_worker.health_updated.connect(self._on_health_updated)
            self.memory_worker.error_occurred.connect(self._on_error_occurred)

            # Connect service signals
            self.memory_service.connection_status_changed.connect(
                self._on_connection_status_changed
            )

            # Initialize service in background thread
            # Note: Async initialization handled by service itself
            try:
                # Try direct sync initialization for now
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.memory_service.initialize())
                loop.close()
            except Exception as init_error:
                msg = f"Service initialization failed: {init_error}"
                print(f"Warning: {msg}")  # Simple fallback logging

            # Initial data refresh
            self._refresh_data()

        except Exception as e:
            self._show_error(f"Failed to initialize memory service: {e}")

    def _perform_search(self):
        """Perform memory search."""
        if not self.memory_worker:
            self._show_error("Memory service not initialized")
            return

        query = self.search_input.text().strip()
        scope = self.scope_combo.currentText()
        k = self.limit_spinner.value()
        threshold = float(self.threshold_combo.currentText())

        if not query:
            self._refresh_memories()  # Browse all if no query
            return

        # Show progress
        self.operation_progress.setVisible(True)
        self.operation_progress.setRange(0, 0)  # Indeterminate progress

        # Perform search in worker thread
        self.memory_worker.search_memory(query, scope, k, threshold)

        # Emit signal for external listeners
        self.search_performed.emit(query, scope)

    def _refresh_memories(self):
        """Refresh memory list (browse all)."""
        if not self.memory_worker:
            return

        # Use empty query to browse all memories
        scope = self.scope_combo.currentText()
        k = 50  # Browse limit

        self.memory_worker.search_memory("", scope, k, 0.0)

    def _refresh_stats(self):
        """Refresh memory statistics."""
        if self.memory_worker and not self.memory_worker.isRunning():
            self.memory_worker.get_stats()

    def _check_health(self):
        """Check memory system health."""
        if self.memory_worker and not self.memory_worker.isRunning():
            self.memory_worker.get_health()

    def _refresh_data(self):
        """Refresh all data."""
        self._refresh_memories()
        self._refresh_stats()
        self._check_health()

    def _on_search_completed(self, results: List[Dict[str, Any]]):
        """Handle search results."""
        self.operation_progress.setVisible(False)
        self.current_memories = results
        self._populate_memory_tree(results)

    def _on_stats_updated(self, stats: Dict[str, Any]):
        """Handle updated statistics."""
        total = stats.get("total_entries", 0)
        self.total_entries_label.setText(f"Entries: {total}")

        usage = stats.get("memory_usage", {})
        usage_mb = usage.get("total_mb", 0)
        self.memory_usage_label.setText(f"Usage: {usage_mb:.1f} MB")

    def _on_health_updated(self, health: Dict[str, Any]):
        """Handle updated health status."""
        status = health.get("status", "unknown")
        self.health_status_label.setText(f"Health: {status.title()}")

        # Update status color
        color = (
            "green"
            if status == "healthy"
            else "orange" if status == "warning" else "red"
        )
        self.health_status_label.setStyleSheet(f"color: {color}; font-weight: bold;")

    def _on_connection_status_changed(self, is_connected: bool):
        """Handle connection status changes."""
        if is_connected:
            self.connection_status.setText("Memory: Connected")
            self.connection_status.setStyleSheet(
                """
                QLabel {
                    color: green;
                    font-weight: bold;
                    padding: 4px 8px;
                    border-radius: 4px;
                    background-color: rgba(0, 255, 0, 0.1);
                }
            """
            )
        else:
            self.connection_status.setText("Memory: Disconnected")
            self.connection_status.setStyleSheet(
                """
                QLabel {
                    color: red;
                    font-weight: bold;
                    padding: 4px 8px;
                    border-radius: 4px;
                    background-color: rgba(255, 0, 0, 0.1);
                }
            """
            )

    def _on_error_occurred(self, error_msg: str):
        """Handle worker thread errors."""
        self.operation_progress.setVisible(False)
        self._show_error(error_msg)

    def _populate_memory_tree(self, memories: List[Dict[str, Any]]):
        """Populate memory tree with results."""
        self.memory_tree.clear()

        for memory in memories:
            item = QTreeWidgetItem()

            # Truncate content for display
            content = memory.get("content", "")
            if len(content) > 60:
                content = content[:57] + "..."
            item.setText(0, content)

            item.setText(1, memory.get("metadata", {}).get("scope", "unknown"))
            item.setText(2, f"{memory.get('score', 0):.3f}")

            # Format timestamp
            timestamp = memory.get("timestamp", "")
            if timestamp:
                try:
                    from datetime import datetime

                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    formatted_date = dt.strftime("%Y-%m-%d %H:%M")
                    item.setText(3, formatted_date)
                except (ValueError, TypeError):
                    item.setText(3, timestamp[:10])  # Just date part

            # Store full memory data
            item.setData(0, Qt.UserRole, memory)

            self.memory_tree.addTopLevelItem(item)

    def _on_memory_selected(self):
        """Handle memory selection change."""
        selected_items = self.memory_tree.selectedItems()
        if not selected_items:
            self._clear_details()
            return

        memory_data = selected_items[0].data(0, Qt.UserRole)
        if memory_data:
            self._show_memory_details(memory_data)
            self.memory_selected.emit(memory_data)

    def _show_memory_details(self, memory: Dict[str, Any]):
        """Show detailed memory information."""
        # Content tab
        content = memory.get("content", "No content")
        self.content_text.setPlainText(content)

        # Metadata tab
        metadata = memory.get("metadata", {})
        self.metadata_table.setRowCount(
            len(metadata) + 3
        )  # +3 for id, score, timestamp

        row = 0
        # Add core properties
        core_props = [
            ("ID", memory.get("id", "N/A")),
            ("Score", f"{memory.get('score', 0):.6f}"),
            ("Timestamp", memory.get("timestamp", "N/A")),
        ]

        for key, value in core_props:
            self.metadata_table.setItem(row, 0, QTableWidgetItem(key))
            self.metadata_table.setItem(row, 1, QTableWidgetItem(str(value)))
            row += 1

        # Add metadata properties
        for key, value in metadata.items():
            self.metadata_table.setItem(row, 0, QTableWidgetItem(key))
            self.metadata_table.setItem(row, 1, QTableWidgetItem(str(value)))
            row += 1

    def _clear_details(self):
        """Clear memory details display."""
        self.content_text.clear()
        self.metadata_table.setRowCount(0)

    def _show_error(self, message: str):
        """Show error message to user."""
        QMessageBox.warning(self, "Memory Browser Error", message)

    def closeEvent(self, event):
        """Clean up on widget close."""
        if self.memory_worker:
            self.memory_worker.quit()
            self.memory_worker.wait()

        if self.memory_service:
            asyncio.create_task(self.memory_service.close())

        super().closeEvent(event)

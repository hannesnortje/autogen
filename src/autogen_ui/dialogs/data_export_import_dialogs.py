"""
Data Export/Import Dialog Components for AutoGen UI

Provides user-friendly dialogs for data export and import operations
with format selection, filtering options, and progress tracking.
"""

import logging
from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QComboBox,
    QCheckBox,
    QLineEdit,
    QGroupBox,
    QProgressBar,
    QTextEdit,
    QFileDialog,
    QDateEdit,
    QMessageBox,
    QTabWidget,
    QWidget,
    QFormLayout,
)
from PySide6.QtCore import QDate, Qt

from ..services.data_export_import_service import (
    DataExportImportService,
    ExportFormat,
    DataType,
    ExportOptions,
    ImportOptions,
)

logger = logging.getLogger(__name__)


class ExportDialog(QDialog):
    """
    Dialog for configuring and executing data export operations
    """

    def __init__(self, service: DataExportImportService, parent=None):
        super().__init__(parent)
        self.service = service
        self.setWindowTitle("Export Data")
        self.setModal(True)
        self.resize(600, 500)

        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout(self)

        # Create tabs
        tab_widget = QTabWidget()

        # Data Selection Tab
        data_tab = self._create_data_selection_tab()
        tab_widget.addTab(data_tab, "Data Selection")

        # Export Options Tab
        options_tab = self._create_export_options_tab()
        tab_widget.addTab(options_tab, "Export Options")

        # Progress Tab
        progress_tab = self._create_progress_tab()
        tab_widget.addTab(progress_tab, "Progress")

        layout.addWidget(tab_widget)

        # Button layout
        button_layout = QHBoxLayout()

        self.cancel_button = QPushButton("Cancel")
        self.export_button = QPushButton("Export")
        self.export_button.setDefault(True)

        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.export_button)

        layout.addLayout(button_layout)

    def _create_data_selection_tab(self) -> QWidget:
        """Create the data selection tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Data types selection
        data_group = QGroupBox("Data Types to Export")
        data_layout = QVBoxLayout(data_group)

        self.data_checkboxes = {}
        for data_type in DataType:
            if data_type != DataType.ALL:  # Handle ALL separately
                checkbox = QCheckBox(data_type.value.replace("_", " ").title())
                checkbox.setChecked(True)  # Default to all selected
                self.data_checkboxes[data_type] = checkbox
                data_layout.addWidget(checkbox)

        # Add "Select All" option
        self.select_all_checkbox = QCheckBox("Select All")
        self.select_all_checkbox.setChecked(True)
        self.select_all_checkbox.stateChanged.connect(self._on_select_all_changed)
        data_layout.insertWidget(0, self.select_all_checkbox)

        layout.addWidget(data_group)

        # Filtering options
        filter_group = QGroupBox("Filtering Options")
        filter_layout = QFormLayout(filter_group)

        # Date range filtering
        self.enable_date_filter = QCheckBox("Filter by Date Range")
        filter_layout.addRow(self.enable_date_filter)

        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.start_date.setEnabled(False)
        filter_layout.addRow("Start Date:", self.start_date)

        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setEnabled(False)
        filter_layout.addRow("End Date:", self.end_date)

        self.enable_date_filter.toggled.connect(self.start_date.setEnabled)
        self.enable_date_filter.toggled.connect(self.end_date.setEnabled)

        # Memory collection filter
        self.enable_collection_filter = QCheckBox("Filter by Collection")
        filter_layout.addRow(self.enable_collection_filter)

        self.collection_name = QLineEdit()
        self.collection_name.setPlaceholderText("Enter collection name")
        self.collection_name.setEnabled(False)
        filter_layout.addRow("Collection Name:", self.collection_name)

        self.enable_collection_filter.toggled.connect(self.collection_name.setEnabled)

        layout.addWidget(filter_group)
        layout.addStretch()

        return widget

    def _create_export_options_tab(self) -> QWidget:
        """Create the export options tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Format selection
        format_group = QGroupBox("Export Format")
        format_layout = QVBoxLayout(format_group)

        self.format_combo = QComboBox()
        for format_type in ExportFormat:
            self.format_combo.addItem(format_type.value.upper(), format_type)
        format_layout.addWidget(self.format_combo)

        # Format-specific options
        self.format_options = QGroupBox("Format Options")
        self.format_options_layout = QVBoxLayout(self.format_options)

        self.include_timestamps = QCheckBox("Include Timestamps")
        self.include_timestamps.setChecked(True)
        self.format_options_layout.addWidget(self.include_timestamps)

        self.include_metadata = QCheckBox("Include Export Metadata")
        self.include_metadata.setChecked(True)
        self.format_options_layout.addWidget(self.include_metadata)

        layout.addWidget(format_group)
        layout.addWidget(self.format_options)

        # Output location
        output_group = QGroupBox("Output Location")
        output_layout = QFormLayout(output_group)

        output_row_layout = QHBoxLayout()
        self.output_path = QLineEdit()
        default_path = Path.home() / "Downloads" / "autogen_export"
        self.output_path.setText(str(default_path))

        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self._browse_output_path)

        output_row_layout.addWidget(self.output_path)
        output_row_layout.addWidget(self.browse_button)
        output_layout.addRow("Output Path:", output_row_layout)

        layout.addWidget(output_group)
        layout.addStretch()

        return widget

    def _create_progress_tab(self) -> QWidget:
        """Create the progress tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Status text
        self.status_label = QLabel("Ready to export")
        layout.addWidget(self.status_label)

        # Log text area
        log_group = QGroupBox("Export Log")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        log_layout.addWidget(self.log_text)

        layout.addWidget(log_group)
        layout.addStretch()

        return widget

    def connect_signals(self):
        """Connect signals to slots"""
        self.cancel_button.clicked.connect(self.reject)
        self.export_button.clicked.connect(self._start_export)

        # Connect service signals
        self.service.export_completed.connect(self._on_export_completed)
        self.service.operation_failed.connect(self._on_export_failed)
        self.service.operation_progress.connect(self._on_progress_update)

    def _on_select_all_changed(self, state):
        """Handle select all checkbox change"""
        checked = state == Qt.CheckState.Checked
        for checkbox in self.data_checkboxes.values():
            checkbox.setChecked(checked)

    def _browse_output_path(self):
        """Browse for output path"""
        current_path = self.output_path.text() or str(Path.home())
        path = QFileDialog.getSaveFileName(
            self, "Select Export Location", current_path, "All Files (*)"
        )[0]

        if path:
            # Remove extension if present, will be added by service
            path = Path(path).with_suffix("")
            self.output_path.setText(str(path))

    def _start_export(self):
        """Start the export operation"""
        try:
            # Get selected data types
            selected_types = []
            for data_type, checkbox in self.data_checkboxes.items():
                if checkbox.isChecked():
                    selected_types.append(data_type)

            if not selected_types:
                QMessageBox.warning(
                    self, "Warning", "Please select at least one data type to export."
                )
                return

            # Get export format
            export_format = self.format_combo.currentData()

            # Get output path
            output_path = self.output_path.text().strip()
            if not output_path:
                QMessageBox.warning(self, "Warning", "Please specify an output path.")
                return

            # Build filter criteria
            filter_criteria = {}
            if self.enable_date_filter.isChecked():
                filter_criteria["date_range"] = (
                    self.start_date.date().toPython(),
                    self.end_date.date().toPython(),
                )

            if (
                self.enable_collection_filter.isChecked()
                and self.collection_name.text()
            ):
                filter_criteria["collection"] = self.collection_name.text()

            # Create export options
            export_options = ExportOptions(
                data_types=selected_types,
                format=export_format,
                output_path=output_path,
                include_timestamps=self.include_timestamps.isChecked(),
                filter_criteria=filter_criteria if filter_criteria else None,
            )

            # Update UI for export
            self.export_button.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.status_label.setText("Starting export...")
            self._log_message("Export started")

            # Start export
            self.service.export_data(export_options)

        except Exception as e:
            logger.error(f"Failed to start export: {e}")
            QMessageBox.critical(self, "Error", f"Failed to start export: {e}")

    def _on_export_completed(self, output_path: str):
        """Handle export completion"""
        self.progress_bar.setValue(100)
        self.status_label.setText(f"Export completed: {output_path}")
        self._log_message(f"Export completed successfully: {output_path}")

        # Show completion message
        reply = QMessageBox.question(
            self,
            "Export Complete",
            f"Export completed successfully!\n\nFile saved to:\n{output_path}\n\nWould you like to open the folder?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            import subprocess
            import platform

            folder_path = str(Path(output_path).parent)
            if platform.system() == "Windows":
                subprocess.run(["explorer", folder_path])
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", folder_path])
            else:  # Linux
                subprocess.run(["xdg-open", folder_path])

        self.accept()

    def _on_export_failed(self, error_message: str):
        """Handle export failure"""
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"Export failed: {error_message}")
        self._log_message(f"Export failed: {error_message}")
        self.export_button.setEnabled(True)

        QMessageBox.critical(
            self, "Export Failed", f"Export operation failed:\n\n{error_message}"
        )

    def _on_progress_update(self, percentage: int):
        """Handle progress updates"""
        self.progress_bar.setValue(percentage)
        self._log_message(f"Progress: {percentage}%")

    def _log_message(self, message: str):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")


class ImportDialog(QDialog):
    """
    Dialog for configuring and executing data import operations
    """

    def __init__(self, service: DataExportImportService, parent=None):
        super().__init__(parent)
        self.service = service
        self.setWindowTitle("Import Data")
        self.setModal(True)
        self.resize(500, 400)

        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout(self)

        # File selection
        file_group = QGroupBox("Import File")
        file_layout = QFormLayout(file_group)

        file_row_layout = QHBoxLayout()
        self.file_path = QLineEdit()
        self.file_path.setPlaceholderText("Select file to import...")

        self.browse_file_button = QPushButton("Browse...")
        self.browse_file_button.clicked.connect(self._browse_import_file)

        file_row_layout.addWidget(self.file_path)
        file_row_layout.addWidget(self.browse_file_button)
        file_layout.addRow("File:", file_row_layout)

        layout.addWidget(file_group)

        # Import options
        options_group = QGroupBox("Import Options")
        options_layout = QFormLayout(options_group)

        self.data_type_combo = QComboBox()
        for data_type in DataType:
            if data_type != DataType.ALL:
                self.data_type_combo.addItem(
                    data_type.value.replace("_", " ").title(), data_type
                )
        options_layout.addRow("Data Type:", self.data_type_combo)

        self.merge_strategy_combo = QComboBox()
        self.merge_strategy_combo.addItems(["Append", "Replace", "Update"])
        options_layout.addRow("Merge Strategy:", self.merge_strategy_combo)

        self.validate_data = QCheckBox("Validate imported data")
        self.validate_data.setChecked(True)
        options_layout.addRow(self.validate_data)

        self.backup_existing = QCheckBox("Backup existing data")
        self.backup_existing.setChecked(True)
        options_layout.addRow(self.backup_existing)

        layout.addWidget(options_group)

        # Progress section
        progress_group = QGroupBox("Import Progress")
        progress_layout = QVBoxLayout(progress_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Ready to import")
        progress_layout.addWidget(self.status_label)

        layout.addWidget(progress_group)

        # Button layout
        button_layout = QHBoxLayout()

        self.cancel_button = QPushButton("Cancel")
        self.import_button = QPushButton("Import")
        self.import_button.setDefault(True)
        self.import_button.setEnabled(False)  # Enable when file selected

        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.import_button)

        layout.addLayout(button_layout)

    def connect_signals(self):
        """Connect signals to slots"""
        self.cancel_button.clicked.connect(self.reject)
        self.import_button.clicked.connect(self._start_import)
        self.file_path.textChanged.connect(self._on_file_path_changed)

        # Connect service signals
        self.service.import_completed.connect(self._on_import_completed)
        self.service.operation_failed.connect(self._on_import_failed)
        self.service.operation_progress.connect(self._on_progress_update)

    def _browse_import_file(self):
        """Browse for import file"""
        file_path = QFileDialog.getOpenFileName(
            self,
            "Select Import File",
            str(Path.home()),
            "Data Files (*.json *.csv *.xlsx);;JSON Files (*.json);;CSV Files (*.csv);;Excel Files (*.xlsx);;All Files (*)",
        )[0]

        if file_path:
            self.file_path.setText(file_path)

    def _on_file_path_changed(self, text: str):
        """Handle file path change"""
        self.import_button.setEnabled(bool(text.strip()))

    def _start_import(self):
        """Start the import operation"""
        try:
            file_path = self.file_path.text().strip()
            if not file_path or not Path(file_path).exists():
                QMessageBox.warning(
                    self, "Warning", "Please select a valid import file."
                )
                return

            # Get import options
            data_type = self.data_type_combo.currentData()
            merge_strategy = self.merge_strategy_combo.currentText().lower()

            import_options = ImportOptions(
                data_type=data_type,
                input_path=file_path,
                validate_data=self.validate_data.isChecked(),
                merge_strategy=merge_strategy,
                backup_existing=self.backup_existing.isChecked(),
            )

            # Update UI for import
            self.import_button.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.status_label.setText("Starting import...")

            # Start import
            self.service.import_data(import_options)

        except Exception as e:
            logger.error(f"Failed to start import: {e}")
            QMessageBox.critical(self, "Error", f"Failed to start import: {e}")

    def _on_import_completed(self, summary: str):
        """Handle import completion"""
        self.progress_bar.setValue(100)
        self.status_label.setText("Import completed")

        QMessageBox.information(
            self, "Import Complete", f"Import completed successfully!\n\n{summary}"
        )

        self.accept()

    def _on_import_failed(self, error_message: str):
        """Handle import failure"""
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"Import failed: {error_message}")
        self.import_button.setEnabled(True)

        QMessageBox.critical(
            self, "Import Failed", f"Import operation failed:\n\n{error_message}"
        )

    def _on_progress_update(self, percentage: int):
        """Handle progress updates"""
        self.progress_bar.setValue(percentage)


def show_export_dialog(service: DataExportImportService, parent=None) -> bool:
    """
    Show the export dialog and return True if export was started
    """
    dialog = ExportDialog(service, parent)
    return dialog.exec() == QDialog.DialogCode.Accepted


def show_import_dialog(service: DataExportImportService, parent=None) -> bool:
    """
    Show the import dialog and return True if import was started
    """
    dialog = ImportDialog(service, parent)
    return dialog.exec() == QDialog.DialogCode.Accepted

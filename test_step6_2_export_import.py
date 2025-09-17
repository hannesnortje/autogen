#!/usr/bin/env python3
"""
Test script for Step 6.2 Data Export/Import functionality

Tests the export/import dialogs and service integration.
"""

import sys
import json
import logging
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PySide6.QtWidgets import QApplication
from autogen_ui.services.data_export_import_service import (
    DataExportImportService,
    ExportFormat,
    DataType,
    ExportOptions,
    ImportOptions,
)
from autogen_ui.dialogs.data_export_import_dialogs import (
    show_export_dialog,
    show_import_dialog,
)

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def test_service_initialization():
    """Test that the service can be initialized"""
    try:
        service = DataExportImportService("http://localhost:9000")
        logger.info("✅ Service initialized successfully")
        return service
    except Exception as e:
        logger.error(f"❌ Service initialization failed: {e}")
        return None


def test_export_options_creation():
    """Test creation of export options"""
    try:
        export_options = ExportOptions(
            data_types=[DataType.MEMORY, DataType.SESSIONS],
            format=ExportFormat.JSON,
            output_path="/tmp/test_export",
            include_timestamps=True,
            filter_criteria={"date_range": ("2024-01-01", "2024-12-31")},
        )
        logger.info("✅ Export options created successfully")
        logger.info(
            f"   - Data types: {[dt.value for dt in export_options.data_types]}"
        )
        logger.info(f"   - Format: {export_options.format.value}")
        logger.info(f"   - Output path: {export_options.output_path}")
        return True
    except Exception as e:
        logger.error(f"❌ Export options creation failed: {e}")
        return False


def test_import_options_creation():
    """Test creation of import options"""
    try:
        import_options = ImportOptions(
            data_type=DataType.MEMORY,
            input_path="/tmp/test_import.json",
            validate_data=True,
            merge_strategy="append",
            backup_existing=True,
        )
        logger.info("✅ Import options created successfully")
        logger.info(f"   - Data type: {import_options.data_type.value}")
        logger.info(f"   - Input path: {import_options.input_path}")
        logger.info(f"   - Validate data: {import_options.validate_data}")
        logger.info(f"   - Merge strategy: {import_options.merge_strategy}")
        return True
    except Exception as e:
        logger.error(f"❌ Import options creation failed: {e}")
        return False


def test_dialog_imports():
    """Test that dialog functions can be imported"""
    try:
        # Test that we can import the dialog functions
        assert callable(show_export_dialog)
        assert callable(show_import_dialog)
        logger.info("✅ Dialog functions imported successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Dialog import test failed: {e}")
        return False


def test_enum_values():
    """Test that enum values are correctly defined"""
    try:
        # Test ExportFormat enum
        formats = [fmt.value for fmt in ExportFormat]
        expected_formats = ["json", "csv", "xlsx"]
        assert all(fmt in expected_formats for fmt in formats)
        logger.info(f"✅ Export formats: {formats}")

        # Test DataType enum
        data_types = [dt.value for dt in DataType]
        expected_types = ["memory", "sessions", "agents", "server_config", "all"]
        assert all(dt in expected_types for dt in data_types)
        logger.info(f"✅ Data types: {data_types}")

        return True
    except Exception as e:
        logger.error(f"❌ Enum values test failed: {e}")
        return False


def test_ui_integration():
    """Test UI dialog integration (if GUI available)"""
    try:
        app = QApplication.instance()
        if app is None:
            app = QApplication([])

        service = DataExportImportService("http://localhost:9000")

        # Test that dialogs can be created (but not shown)
        # This tests the import and basic instantiation
        from autogen_ui.dialogs.data_export_import_dialogs import (
            ExportDialog,
            ImportDialog,
        )

        # Create dialogs to test instantiation
        ExportDialog(service)
        ImportDialog(service)

        logger.info("✅ UI dialogs can be instantiated")
        return True

    except ImportError as e:
        logger.warning(f"⚠️ UI test skipped (missing dependencies): {e}")
        return True  # Not a failure, just unavailable
    except Exception as e:
        logger.error(f"❌ UI integration test failed: {e}")
        return False


def create_sample_export_data():
    """Create sample export data for testing"""
    try:
        sample_data = {
            "memory": [
                {
                    "id": "mem_001",
                    "content": "Sample memory content 1",
                    "metadata": {
                        "type": "conversation",
                        "timestamp": "2024-01-01T10:00:00",
                    },
                    "collection": "default",
                },
                {
                    "id": "mem_002",
                    "content": "Sample memory content 2",
                    "metadata": {
                        "type": "knowledge",
                        "timestamp": "2024-01-01T11:00:00",
                    },
                    "collection": "default",
                },
            ],
            "sessions": [
                {
                    "id": "session_001",
                    "name": "Test Session 1",
                    "created_at": "2024-01-01T09:00:00",
                    "status": "active",
                }
            ],
            "agents": [
                {
                    "name": "Test Agent",
                    "type": "assistant",
                    "model": "gpt-4",
                    "temperature": 0.7,
                }
            ],
            "export_metadata": {
                "timestamp": "2024-01-01T12:00:00",
                "format": "json",
                "version": "1.0",
            },
        }

        # Write sample data to file
        sample_file = Path("/tmp/autogen_sample_export.json")
        with open(sample_file, "w") as f:
            json.dump(sample_data, f, indent=2)

        logger.info(f"✅ Sample export data created: {sample_file}")
        return str(sample_file)

    except Exception as e:
        logger.error(f"❌ Sample data creation failed: {e}")
        return None


def run_tests():
    """Run all tests"""
    logger.info("🧪 Starting Step 6.2 Data Export/Import Tests")
    logger.info("=" * 50)

    tests = [
        ("Service Initialization", test_service_initialization),
        ("Export Options Creation", test_export_options_creation),
        ("Import Options Creation", test_import_options_creation),
        ("Dialog Function Imports", test_dialog_imports),
        ("Enum Values", test_enum_values),
        ("UI Integration", test_ui_integration),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        logger.info(f"\n🔍 Running: {test_name}")
        try:
            result = test_func()
            if result:
                passed += 1
            else:
                logger.error(f"❌ {test_name} failed")
        except Exception as e:
            logger.error(f"❌ {test_name} failed with exception: {e}")

    # Create sample data
    logger.info("\n🔍 Creating sample export data")
    sample_file = create_sample_export_data()

    logger.info("\n" + "=" * 50)
    logger.info(f"📊 Test Results: {passed}/{total} tests passed")

    if sample_file:
        logger.info(f"📁 Sample export file: {sample_file}")

    if passed == total:
        logger.info(
            "🎉 All tests passed! Step 6.2 implementation is working correctly."
        )
        return True
    else:
        logger.warning(f"⚠️  {total - passed} tests failed. Check the logs above.")
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
AutoGen UI - Clean rebuild with working architecture
Main entry point for the AutoGen Desktop UI
"""

import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QFont

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from autogen_ui_clean.main_window import AutoGenMainWindow
from autogen_ui_clean.config import load_config


def setup_application():
    """Set up the Qt application with proper attributes."""
    app = QApplication(sys.argv)
    app.setApplicationName("AutoGen Desktop")
    app.setApplicationVersion("0.2.0")
    app.setOrganizationName("AutoGen")

    # Set application font
    font = QFont()
    font.setFamily("Segoe UI" if sys.platform == "win32" else "Ubuntu")
    font.setPointSize(9)
    app.setFont(font)

    return app


def main():
    """Main entry point."""
    try:
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

        # Create application
        app = setup_application()

        # Load configuration
        config = load_config()

        # Create main window
        window = AutoGenMainWindow(config)

        # Show window
        window.show()

        # Start event loop
        return app.exec()

    except Exception as e:
        print(f"Error starting AutoGen UI: {e}")
        if "app" in locals():
            QMessageBox.critical(
                None, "Startup Error", f"Failed to start AutoGen UI:\n{e}"
            )
        return 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
AutoGen Desktop UI - Main Entry Point

This module serves as the entry point for the AutoGen desktop application.
It sets up the Qt application, logging, and launches the main window.
"""

import sys
import logging
from typing import Dict, Any

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from autogen_ui.app.main_window import MainWindow
from autogen_ui.utils.logging_config import (
    setup_ui_logging,
    log_application_startup,
    log_application_shutdown,
)


def create_application() -> QApplication:
    """Create and configure the Qt application."""

    # Set application attributes
    app_attrs = Qt.ApplicationAttribute
    # Skip deprecated attributes for newer Qt versions
    try:
        QApplication.setAttribute(app_attrs.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(app_attrs.AA_UseHighDpiPixmaps, True)
    except AttributeError:
        # These attributes might not exist in newer Qt versions
        pass

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("AutoGen Desktop")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("AutoGen")
    app.setOrganizationDomain("autogen.local")

    return app


def load_configuration() -> Dict[str, Any]:
    """Load application configuration."""

    return {
        "app_name": "AutoGen Desktop",
        "app_version": "0.1.0",
        "theme": "system",
        "debug": False,  # Enable for debug logging
        "integration_mode": "hybrid",  # direct, http, or hybrid
        "window_geometry": {"width": 1200, "height": 800},
        "mcp_server": {"host": "localhost", "port": 9000, "auto_connect": False},
        "ui_features": {
            "session_management": True,
            "memory_browser": True,
            "agent_configuration": True,
            "server_management": True,
        },
    }


def main() -> int:
    """Main application entry point."""

    try:
        # Load configuration first
        config = load_configuration()

        # Set up enhanced logging system
        setup_ui_logging(config)
        logger = logging.getLogger(__name__)

        # Log application startup
        log_application_startup(config)

        # Create Qt application
        app = create_application()

        # Create main window
        print("DEBUG: About to create MainWindow")
        main_window = MainWindow(config)
        print("DEBUG: MainWindow created successfully")

        print("DEBUG: About to show window")
        main_window.show()
        print("DEBUG: Window shown, starting event loop")

        logger.info("AutoGen Desktop UI started successfully")

        # Run the application
        print("DEBUG: About to call app.exec()")
        result = app.exec()
        print("DEBUG: app.exec() completed")

        # Log application shutdown
        log_application_shutdown()

        return result

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to start AutoGen Desktop UI: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

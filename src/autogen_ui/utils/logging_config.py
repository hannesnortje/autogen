"""
AutoGen Desktop UI - Logging Configuration

This module provides enhanced logging configuration that integrates with
the existing MCP server logging patterns and extends them for UI components.
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from PySide6.QtCore import qInstallMessageHandler, QtMsgType


def get_shared_logs_directory() -> Path:
    """Get the shared logs directory used by both UI and MCP server."""

    # Use the same logs directory as the MCP server
    project_root = Path(__file__).parent.parent.parent.parent
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)

    return logs_dir


def setup_qt_message_handler() -> None:
    """Configure Qt logging to integrate with Python logging."""

    def qt_message_handler(mode: QtMsgType, context, message: str) -> None:
        """Handle Qt log messages through Python logging."""

        logger = logging.getLogger("Qt")

        # Filter out some noisy Qt messages
        if any(
            pattern in message.lower()
            for pattern in ["qt.pointer.dispatch", "qt.qpa.xcb", "libpng warning"]
        ):
            return

        # Map Qt log levels to Python logging levels
        if mode == QtMsgType.QtDebugMsg:
            logger.debug(f"Qt: {message}")
        elif mode == QtMsgType.QtInfoMsg:
            logger.info(f"Qt: {message}")
        elif mode == QtMsgType.QtWarningMsg:
            logger.warning(f"Qt: {message}")
        elif mode == QtMsgType.QtCriticalMsg:
            logger.error(f"Qt: {message}")
        elif mode == QtMsgType.QtFatalMsg:
            logger.critical(f"Qt: {message}")

    qInstallMessageHandler(qt_message_handler)


def create_ui_log_formatter() -> logging.Formatter:
    """Create a consistent log formatter for UI components."""

    return logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [UI] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def setup_ui_logging(config: Dict[str, Any]) -> None:
    """
    Set up comprehensive logging for the UI application.

    This integrates with existing MCP server logging while adding
    UI-specific handlers and formatters.
    """

    logs_dir = get_shared_logs_directory()

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Create formatter
    formatter = create_ui_log_formatter()

    # Console handler for development
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler for UI logs
    ui_log_file = logs_dir / "ui.log"
    ui_file_handler = logging.FileHandler(ui_log_file, mode="a")
    ui_file_handler.setLevel(logging.DEBUG)
    ui_file_handler.setFormatter(formatter)
    root_logger.addHandler(ui_file_handler)

    # Shared log file for both UI and MCP server
    shared_log_file = logs_dir / "autogen.log"
    shared_file_handler = logging.FileHandler(shared_log_file, mode="a")
    shared_file_handler.setLevel(logging.INFO)
    shared_file_handler.setFormatter(formatter)
    root_logger.addHandler(shared_file_handler)

    # Error log file for critical issues
    error_log_file = logs_dir / "errors.log"
    error_file_handler = logging.FileHandler(error_log_file, mode="a")
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(formatter)
    root_logger.addHandler(error_file_handler)

    # Configure specific loggers
    setup_logger_levels(config)

    # Set up Qt logging integration
    setup_qt_message_handler()

    # Log initialization
    logger = logging.getLogger(__name__)
    logger.info("UI logging system initialized")
    logger.info(f"Logs directory: {logs_dir}")
    logger.info("Log files: ui.log, autogen.log, errors.log")


def setup_logger_levels(config: Dict[str, Any]) -> None:
    """Configure log levels for different components."""

    # UI component loggers
    logging.getLogger("autogen_ui").setLevel(logging.DEBUG)
    logging.getLogger("autogen_ui.app").setLevel(logging.INFO)
    logging.getLogger("autogen_ui.widgets").setLevel(logging.INFO)
    logging.getLogger("autogen_ui.services").setLevel(logging.DEBUG)

    # Qt loggers
    logging.getLogger("Qt").setLevel(logging.WARNING)

    # External libraries
    logging.getLogger("PySide6").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.INFO)

    # MCP server loggers (when running in hybrid mode)
    logging.getLogger("autogen_mcp").setLevel(logging.INFO)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)

    # Adjust based on debug mode
    if config.get("debug", False):
        logging.getLogger("autogen_ui").setLevel(logging.DEBUG)
        logging.getLogger("Qt").setLevel(logging.DEBUG)


def get_logger(name: str) -> logging.Logger:
    """Get a properly configured logger for UI components."""

    return logging.getLogger(f"autogen_ui.{name}")


def log_application_startup(config: Dict[str, Any]) -> None:
    """Log application startup information."""

    logger = get_logger("startup")

    logger.info("=" * 60)
    logger.info("AutoGen Desktop UI Starting")
    logger.info("=" * 60)
    logger.info(f"Application: {config.get('app_name', 'AutoGen Desktop')}")
    logger.info(f"Version: {config.get('app_version', '0.1.0')}")
    logger.info(f"Theme: {config.get('theme', 'system')}")
    logger.info(f"Integration mode: {config.get('integration_mode', 'hybrid')}")
    logger.info(f"Window size: {config.get('window_geometry', {})}")
    logger.info("=" * 60)


def log_application_shutdown() -> None:
    """Log application shutdown information."""

    logger = get_logger("shutdown")

    logger.info("=" * 60)
    logger.info("AutoGen Desktop UI Shutting Down")
    logger.info("=" * 60)


class UILogHandler(logging.Handler):
    """
    Custom log handler that can send log messages to UI components.

    This allows displaying log messages in the UI for real-time monitoring.
    """

    def __init__(self, level: int = logging.NOTSET):
        super().__init__(level)
        self.log_signals: Dict[str, Any] = {}

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record to connected UI components."""

        try:
            message = self.format(record)

            # Emit to any connected UI log viewers
            for name, signal in self.log_signals.items():
                if hasattr(signal, "emit"):
                    signal.emit(message)

        except Exception:
            # Don't let logging errors crash the application
            self.handleError(record)

    def connect_log_viewer(self, name: str, signal) -> None:
        """Connect a UI log viewer to receive log messages."""

        self.log_signals[name] = signal

    def disconnect_log_viewer(self, name: str) -> None:
        """Disconnect a UI log viewer."""

        if name in self.log_signals:
            del self.log_signals[name]


# Global UI log handler instance
ui_log_handler: Optional[UILogHandler] = None


def get_ui_log_handler() -> UILogHandler:
    """Get the global UI log handler, creating it if needed."""

    global ui_log_handler

    if ui_log_handler is None:
        ui_log_handler = UILogHandler()
        ui_log_handler.setLevel(logging.INFO)
        ui_log_handler.setFormatter(create_ui_log_formatter())

        # Add to root logger
        logging.getLogger().addHandler(ui_log_handler)

    return ui_log_handler

"""
Notification Service for AutoGen UI

Provides native desktop notifications and in-app notification management
for real-time updates and important events.
"""

import logging
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Callable
from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWidgets import (
    QSystemTrayIcon,
    QMenu,
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QDialog,
    QCheckBox,
    QGroupBox,
)
from PySide6.QtGui import QIcon, QPixmap, QColor
from PySide6.QtCore import Qt

logger = logging.getLogger(__name__)


class NotificationLevel(Enum):
    """Notification severity levels"""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class Notification:
    """Notification data structure"""

    id: str
    level: NotificationLevel
    title: str
    message: str
    timestamp: float
    category: str = "general"
    persistent: bool = False
    action_callback: Optional[Callable] = None
    action_text: Optional[str] = None


class NotificationWidget(QFrame):
    """Individual notification widget for in-app display"""

    dismissed = Signal(str)  # notification_id

    def __init__(self, notification: Notification):
        super().__init__()
        self.notification = notification
        self._setup_ui()

    def _setup_ui(self):
        """Set up the notification widget UI"""
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet(self._get_style_for_level())

        layout = QHBoxLayout()
        layout.setContentsMargins(12, 8, 12, 8)

        # Icon (could be enhanced with actual icons)
        icon_label = QLabel(self._get_icon_text())
        icon_label.setFixedSize(24, 24)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-weight: bold; font-size: 14px;")

        # Content
        content_layout = QVBoxLayout()
        content_layout.setSpacing(2)

        title_label = QLabel(self.notification.title)
        title_label.setStyleSheet("font-weight: bold; font-size: 12px;")

        message_label = QLabel(self.notification.message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("font-size: 11px;")

        content_layout.addWidget(title_label)
        content_layout.addWidget(message_label)

        # Action button (if provided)
        if self.notification.action_callback and self.notification.action_text:
            action_btn = QPushButton(self.notification.action_text)
            action_btn.clicked.connect(self.notification.action_callback)
            action_btn.setMaximumHeight(24)
            content_layout.addWidget(action_btn)

        # Dismiss button
        dismiss_btn = QPushButton("×")
        dismiss_btn.setFixedSize(24, 24)
        dismiss_btn.clicked.connect(self._dismiss)
        dismiss_btn.setStyleSheet(
            """
            QPushButton {
                border: none;
                background: transparent;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.1);
                border-radius: 12px;
            }
        """
        )

        layout.addWidget(icon_label)
        layout.addLayout(content_layout, 1)
        layout.addWidget(dismiss_btn)

        self.setLayout(layout)

        # Auto-dismiss timer (if not persistent)
        if not self.notification.persistent:
            self.auto_dismiss_timer = QTimer()
            self.auto_dismiss_timer.timeout.connect(self._dismiss)
            dismiss_time = 5000  # 5 seconds default
            if self.notification.level == NotificationLevel.ERROR:
                dismiss_time = 8000  # 8 seconds for errors
            self.auto_dismiss_timer.start(dismiss_time)

    def _get_style_for_level(self) -> str:
        """Get styling based on notification level"""
        styles = {
            NotificationLevel.INFO: """
                QFrame {
                    background-color: #e3f2fd;
                    border: 1px solid #2196f3;
                    border-radius: 4px;
                }
            """,
            NotificationLevel.SUCCESS: """
                QFrame {
                    background-color: #e8f5e8;
                    border: 1px solid #4caf50;
                    border-radius: 4px;
                }
            """,
            NotificationLevel.WARNING: """
                QFrame {
                    background-color: #fff3e0;
                    border: 1px solid #ff9800;
                    border-radius: 4px;
                }
            """,
            NotificationLevel.ERROR: """
                QFrame {
                    background-color: #ffebee;
                    border: 1px solid #f44336;
                    border-radius: 4px;
                }
            """,
        }
        return styles.get(self.notification.level, styles[NotificationLevel.INFO])

    def _get_icon_text(self) -> str:
        """Get icon text for notification level"""
        icons = {
            NotificationLevel.INFO: "ℹ",
            NotificationLevel.SUCCESS: "✓",
            NotificationLevel.WARNING: "⚠",
            NotificationLevel.ERROR: "✗",
        }
        return icons.get(self.notification.level, "ℹ")

    def _dismiss(self):
        """Dismiss the notification"""
        if hasattr(self, "auto_dismiss_timer"):
            self.auto_dismiss_timer.stop()
        self.dismissed.emit(self.notification.id)


class NotificationPreferencesDialog(QDialog):
    """Dialog for configuring notification preferences"""

    def __init__(self, current_settings: dict, parent=None):
        super().__init__(parent)
        self.current_settings = current_settings
        self.setWindowTitle("Notification Preferences")
        self.setModal(True)
        self.resize(400, 300)
        self._setup_ui()

    def _setup_ui(self):
        """Set up the preferences dialog"""
        layout = QVBoxLayout()

        # Desktop notifications group
        desktop_group = QGroupBox("Desktop Notifications")
        desktop_layout = QVBoxLayout()

        self.desktop_enabled = QCheckBox("Enable desktop notifications")
        self.desktop_enabled.setChecked(
            self.current_settings.get("desktop_enabled", True)
        )

        self.session_updates = QCheckBox("Session status updates")
        self.session_updates.setChecked(
            self.current_settings.get("session_updates", True)
        )

        self.memory_updates = QCheckBox("Memory updates")
        self.memory_updates.setChecked(
            self.current_settings.get("memory_updates", False)
        )

        self.agent_updates = QCheckBox("Agent status changes")
        self.agent_updates.setChecked(self.current_settings.get("agent_updates", True))

        self.error_notifications = QCheckBox("Error notifications")
        self.error_notifications.setChecked(
            self.current_settings.get("error_notifications", True)
        )

        desktop_layout.addWidget(self.desktop_enabled)
        desktop_layout.addWidget(self.session_updates)
        desktop_layout.addWidget(self.memory_updates)
        desktop_layout.addWidget(self.agent_updates)
        desktop_layout.addWidget(self.error_notifications)
        desktop_group.setLayout(desktop_layout)

        # In-app notifications group
        inapp_group = QGroupBox("In-App Notifications")
        inapp_layout = QVBoxLayout()

        self.inapp_enabled = QCheckBox("Enable in-app notifications")
        self.inapp_enabled.setChecked(self.current_settings.get("inapp_enabled", True))

        inapp_layout.addWidget(self.inapp_enabled)
        inapp_group.setLayout(inapp_layout)

        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")

        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)

        layout.addWidget(desktop_group)
        layout.addWidget(inapp_group)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def get_settings(self) -> dict:
        """Get the configured settings"""
        return {
            "desktop_enabled": self.desktop_enabled.isChecked(),
            "session_updates": self.session_updates.isChecked(),
            "memory_updates": self.memory_updates.isChecked(),
            "agent_updates": self.agent_updates.isChecked(),
            "error_notifications": self.error_notifications.isChecked(),
            "inapp_enabled": self.inapp_enabled.isChecked(),
        }


class NotificationService(QObject):
    """
    Notification management service for AutoGen UI

    Handles both desktop notifications via system tray and in-app
    notifications for real-time feedback.
    """

    notification_added = Signal(Notification)
    notification_removed = Signal(str)  # notification_id

    def __init__(self, parent_widget: QWidget):
        super().__init__()
        self.parent_widget = parent_widget
        self.notifications: List[Notification] = []
        self.notification_counter = 0

        # Default settings
        self.settings = {
            "desktop_enabled": True,
            "session_updates": True,
            "memory_updates": False,
            "agent_updates": True,
            "error_notifications": True,
            "inapp_enabled": True,
        }

        # System tray setup
        self.system_tray = None
        self._setup_system_tray()

        logger.info("NotificationService initialized")

    def _setup_system_tray(self):
        """Set up system tray for desktop notifications"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.system_tray = QSystemTrayIcon()

            # Use a simple icon (could be enhanced with actual app icon)
            icon = self._create_simple_icon()
            self.system_tray.setIcon(icon)

            # Context menu
            menu = QMenu()
            show_action = menu.addAction("Show AutoGen UI")
            show_action.triggered.connect(self._show_main_window)
            menu.addSeparator()
            quit_action = menu.addAction("Quit")
            quit_action.triggered.connect(QApplication.quit)

            self.system_tray.setContextMenu(menu)
            self.system_tray.show()

            logger.info("System tray initialized")
        else:
            logger.warning("System tray not available")

    def _create_simple_icon(self) -> QIcon:
        """Create a simple icon for the system tray"""
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(33, 150, 243))  # Blue color
        return QIcon(pixmap)

    def _show_main_window(self):
        """Show the main application window"""
        if self.parent_widget:
            self.parent_widget.show()
            self.parent_widget.raise_()
            self.parent_widget.activateWindow()

    def show_notification(
        self,
        level: str,
        title: str,
        message: str,
        category: str = "general",
        persistent: bool = False,
        action_callback: Optional[Callable] = None,
        action_text: Optional[str] = None,
    ):
        """Show a notification"""
        try:
            level_enum = NotificationLevel(level.lower())
        except ValueError:
            level_enum = NotificationLevel.INFO

        # Create notification
        notification_id = f"notif_{self.notification_counter}"
        self.notification_counter += 1

        notification = Notification(
            id=notification_id,
            level=level_enum,
            title=title,
            message=message,
            timestamp=QTimer().time(),
            category=category,
            persistent=persistent,
            action_callback=action_callback,
            action_text=action_text,
        )

        # Desktop notification
        if self._should_show_desktop_notification(category, level_enum):
            self._show_desktop_notification(notification)

        # In-app notification
        if self.settings.get("inapp_enabled", True):
            self.notifications.append(notification)
            self.notification_added.emit(notification)

        logger.info(f"Notification shown: {title}")

    def _should_show_desktop_notification(
        self, category: str, level: NotificationLevel
    ) -> bool:
        """Check if desktop notification should be shown"""
        if not self.settings.get("desktop_enabled", True):
            return False

        category_mapping = {
            "session": "session_updates",
            "memory": "memory_updates",
            "agent": "agent_updates",
        }

        if category in category_mapping:
            return self.settings.get(category_mapping[category], True)

        if level == NotificationLevel.ERROR:
            return self.settings.get("error_notifications", True)

        return True

    def _show_desktop_notification(self, notification: Notification):
        """Show desktop notification via system tray"""
        if self.system_tray and self.system_tray.supportsMessages():
            icon_mapping = {
                NotificationLevel.INFO: QSystemTrayIcon.Information,
                NotificationLevel.SUCCESS: QSystemTrayIcon.Information,
                NotificationLevel.WARNING: QSystemTrayIcon.Warning,
                NotificationLevel.ERROR: QSystemTrayIcon.Critical,
            }

            icon = icon_mapping.get(notification.level, QSystemTrayIcon.Information)

            self.system_tray.showMessage(
                notification.title,
                notification.message,
                icon,
                5000,  # 5 seconds
            )

    def dismiss_notification(self, notification_id: str):
        """Dismiss a notification"""
        self.notifications = [n for n in self.notifications if n.id != notification_id]
        self.notification_removed.emit(notification_id)

    def clear_all_notifications(self):
        """Clear all notifications"""
        notification_ids = [n.id for n in self.notifications]
        self.notifications.clear()
        for notification_id in notification_ids:
            self.notification_removed.emit(notification_id)

    def get_notifications(self) -> List[Notification]:
        """Get all current notifications"""
        return self.notifications.copy()

    def show_preferences_dialog(self) -> bool:
        """Show notification preferences dialog"""
        dialog = NotificationPreferencesDialog(self.settings, self.parent_widget)
        if dialog.exec() == QDialog.Accepted:
            self.settings = dialog.get_settings()
            logger.info("Notification preferences updated")
            return True
        return False

    def update_settings(self, new_settings: dict):
        """Update notification settings"""
        self.settings.update(new_settings)
        logger.info("Notification settings updated")

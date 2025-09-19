"""
Notification Panel Widget for AutoGen UI

Displays in-app notifications with real-time updates and user interaction.
"""

import logging
from typing import List
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QScrollArea,
    QLabel,
    QPushButton,
    QHBoxLayout,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ..services.notification_service import (
    NotificationService,
    Notification,
    NotificationWidget,
)

logger = logging.getLogger(__name__)


class NotificationPanel(QWidget):
    """
    Panel widget for displaying in-app notifications

    Shows notifications in a scrollable list with dismiss capabilities.
    """

    def __init__(self, notification_service: NotificationService):
        super().__init__()
        self.notification_service = notification_service
        self.notification_widgets: List[NotificationWidget] = []

        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        """Set up the notification panel UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # Header with title and clear all button
        header_layout = QHBoxLayout()

        title_label = QLabel("Notifications")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)

        self.clear_all_btn = QPushButton("Clear All")
        self.clear_all_btn.clicked.connect(self.clear_all_notifications)
        self.clear_all_btn.setMaximumWidth(80)

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.clear_all_btn)

        layout.addLayout(header_layout)

        # Scrollable notification area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Container widget for notifications
        self.notification_container = QWidget()
        self.notification_layout = QVBoxLayout(self.notification_container)
        self.notification_layout.setContentsMargins(0, 0, 0, 0)
        self.notification_layout.setSpacing(4)

        # Add stretch to push notifications to top
        self.notification_layout.addStretch()

        self.scroll_area.setWidget(self.notification_container)
        layout.addWidget(self.scroll_area)

        # Empty state message
        self.empty_label = QLabel("No notifications")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.empty_label)

        self.update_empty_state()

    def connect_signals(self):
        """Connect notification service signals"""
        self.notification_service.notification_added.connect(self.add_notification)
        self.notification_service.notification_removed.connect(self.remove_notification)

    def add_notification(self, notification: Notification):
        """Add a new notification to the panel"""
        # Create notification widget
        notification_widget = NotificationWidget(notification)
        notification_widget.dismissed.connect(self.on_notification_dismissed)

        # Insert at the beginning (newest first)
        self.notification_layout.insertWidget(0, notification_widget)
        self.notification_widgets.insert(0, notification_widget)

        self.update_empty_state()

        # Scroll to top to show new notification
        self.scroll_area.verticalScrollBar().setValue(0)

        logger.info(f"Added notification: {notification.title}")

    def remove_notification(self, notification_id: str):
        """Remove a notification from the panel"""
        for i, widget in enumerate(self.notification_widgets):
            if widget.notification.id == notification_id:
                # Remove from layout and widget list
                self.notification_layout.removeWidget(widget)
                widget.deleteLater()
                del self.notification_widgets[i]
                break

        self.update_empty_state()
        logger.info(f"Removed notification: {notification_id}")

    def on_notification_dismissed(self, notification_id: str):
        """Handle notification dismissal"""
        self.notification_service.dismiss_notification(notification_id)

    def clear_all_notifications(self):
        """Clear all notifications"""
        self.notification_service.clear_all_notifications()

    def update_empty_state(self):
        """Update empty state visibility"""
        has_notifications = len(self.notification_widgets) > 0
        self.empty_label.setVisible(not has_notifications)
        self.clear_all_btn.setEnabled(has_notifications)

    def get_notification_count(self) -> int:
        """Get current notification count"""
        return len(self.notification_widgets)

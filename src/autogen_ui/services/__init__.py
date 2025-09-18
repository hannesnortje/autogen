"""
Services Package for AutoGen UI

Provides centralized services for real-time communication,
notifications, memory operations, and other cross-widget functionality.
"""

from .session_service import SessionService
from .memory_service import MemoryService

__all__ = ["SessionService", "MemoryService"]

"""
AutoGen PySide6 Desktop UI

A desktop application for managing AutoGen multi-agent workflows with Qdrant
memory integration. Provides a comprehensive dashboard and management interface
using PySide6 (Qt6 for Python).

Features:
- Hybrid integration with MCP server (direct imports + HTTP API)
- Real-time session monitoring via WebSocket
- Three-tier memory management and analytics
- Agent configuration and performance monitoring
- Cross-platform desktop application

Architecture:
- Direct integration mode: Import MCP server components for optimal performance
- HTTP integration mode: Network API calls for deployment flexibility
- Hybrid mode: Configurable mix with automatic fallback support
"""

__version__ = "0.1.0"
__author__ = "hannesnortje"

# Export main application class for easy imports
# from .app.application import AutoGenApp  # Uncomment when app exists

__all__ = ["__version__", "__author__"]

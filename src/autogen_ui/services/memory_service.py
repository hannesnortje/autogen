"""
Memory Service for AutoGen UI

Provides a unified interface for memory operations in the UI layer,
supporting both HTTP API and direct local integration modes.
"""

import logging
from typing import Dict, List
from PySide6.QtCore import QObject, Signal

from autogen_mcp.multi_memory import MultiScopeMemoryService
from autogen_mcp.memory_collections import CollectionManager

logger = logging.getLogger(__name__)


class MemoryService(QObject):
    """
    Memory service that bridges the UI with the memory backend.
    Handles both HTTP API calls and direct local integration.
    """
    
    # Signals for UI updates
    search_completed = Signal(list)
    stats_completed = Signal(dict)
    collections_completed = Signal(list)
    error_occurred = Signal(str)
    initialization_completed = Signal(bool)

    def __init__(self, server_url: str = "http://localhost:9000"):
        super().__init__()
        self.server_url = server_url
        self.local_mode = False
        self._initialized = False
        
        # Local components (lazy loaded)
        self._collection_manager = None
        self._memory_service = None
        
        logger.info("[UI] MemoryService initialized")

    async def initialize(self, local_mode: bool = False):
        """Initialize the memory service"""
        self.local_mode = local_mode
        
        try:
            if local_mode:
                await self._initialize_direct()
            else:
                await self._initialize_http()
                
            self._initialized = True
            self.initialization_completed.emit(True)
            logger.info("[UI] Memory service initialized successfully")
            
        except Exception as e:
            error_msg = f"Failed to initialize memory service: {str(e)}"
            logger.error(f"[UI] {error_msg}")
            self.error_occurred.emit(error_msg)
            self.initialization_completed.emit(False)
            raise

    async def _initialize_direct(self):
        """Initialize direct local integration"""
        try:
            # Initialize collection manager
            self._collection_manager = CollectionManager()
            
            # Initialize memory service
            self._memory_service = MultiScopeMemoryService(
                self._collection_manager
            )
            
            # Try to initialize collections - don't fail if Qdrant unavailable
            try:
                # Only initialize collections, not seed global knowledge
                self._collection_manager.initialize_all_collections()
                self._memory_service._initialized = True
                logger.info("[UI] Direct memory service initialized")
            except Exception as e:
                logger.warning(
                    f"[UI] Collections init failed, service available: {e}"
                )
                # Mark as initialized anyway so searches can attempt to work
                self._memory_service._initialized = True
                
        except Exception as e:
            logger.error(f"[UI] Direct initialization failed: {e}")
            raise

    async def _initialize_http(self):
        """Initialize HTTP API integration"""
        import aiohttp
        
        try:
            # Test connection to server
            async with aiohttp.ClientSession() as session:
                health_url = f"{self.server_url}/health"
                async with session.get(health_url) as response:
                    if response.status == 200:
                        logger.info("[UI] HTTP memory service connected")
                    else:
                        raise RuntimeError(
                            f"Server returned status {response.status}"
                        )
                        
        except Exception as e:
            logger.error(f"[UI] HTTP initialization failed: {e}")
            raise

    async def search_memory(
        self, query: str, scope: str, limit: int = 10
    ) -> List[Dict]:
        """Search memory with the given parameters"""
        if not self._initialized:
            error_msg = "Memory service not initialized. Call initialize()."
            logger.error(f"[UI] Memory search failed: {error_msg}")
            self.error_occurred.emit(error_msg)
            return []

        try:
            if self.local_mode:
                return await self._search_memory_direct(query, scope, limit)
            else:
                return await self._search_memory_http(query, scope, limit)
                
        except Exception as e:
            error_msg = f"Memory search failed: {str(e)}"
            logger.error(f"[UI] {error_msg}")
            self.error_occurred.emit(error_msg)
            return []

    async def _search_memory_direct(
        self, query: str, collection: str, limit: int
    ) -> List[Dict]:
        """Direct local search using MultiScopeMemoryService"""
        try:
            # Map collection name to scope for MultiScopeMemoryService
            def _scope_from_collection(name: str) -> str:
                n = (name or "").lower()
                if n.startswith("autogen_project_"):
                    return "project"
                if n == "autogen_global":
                    return "global"
                if n == "autogen_agent":
                    return "agent"
                if n == "autogen_thread":
                    return "thread"
                if n == "autogen_objectives":
                    return "objectives"
                if n == "autogen_artifacts":
                    return "artifacts"
                return "global"  # Default fallback
                
            scope = _scope_from_collection(collection)
            logger.info(f"[UI] Searching collection '{collection}' -> scope '{scope}'")
            
            # Set project ID if needed for project scope
            if scope == "project":
                # Extract project ID from collection name
                if collection.startswith("autogen_project_"):
                    project_id = collection.replace("autogen_project_", "")
                    if project_id == "default":
                        project_id = "default"
                    logger.info(f"[UI] Setting project ID: {project_id}")
                    self._memory_service.set_project(project_id)
            
            # Use correct parameter name 'limit' for MultiScopeMemoryService
            results = self._memory_service.search(
                query=query,
                scope=scope,
                limit=limit  # Changed from 'k' to 'limit' to match API
            )
            
            # Transform results to expected format
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "id": result.get("id"),
                    "score": result.get("score", 0.0),
                    "content": result.get("content", ""),  # Add content at top level
                    "payload": {
                        "content": result.get("content", ""),
                        **result.get("metadata", {})
                    }
                })
                
            msg = f"Direct search returned {len(formatted_results)} results"
            logger.info(f"[UI] {msg}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"[UI] Direct search failed: {e}")
            raise

    async def _search_http(
        self, query: str, scope: str, limit: int
    ) -> List[Dict]:
        """HTTP API search"""
        import aiohttp
        
        try:
            payload = {
                "query": query,
                "scope": scope,
                "k": limit  # HTTP API expects 'k' parameter
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.server_url}/memory/search",
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = data.get("results", [])
                        msg = f"HTTP search returned {len(results)} results"
                        logger.info(f"[UI] {msg}")
                        return results
                    else:
                        text = await response.text()
                        raise RuntimeError(f"HTTP {response.status}: {text}")
                        
        except Exception as e:
            logger.error(f"[UI] HTTP search failed: {e}")
            raise

    async def get_collections(self) -> List[Dict]:
        """Get available collections"""
        if not self._initialized:
            self.error_occurred.emit("Memory service not initialized")
            return []

        try:
            if self.local_mode:
                return await self._get_collections_direct()
            else:
                return await self._get_collections_http()
                
        except Exception as e:
            error_msg = f"Failed to get collections: {str(e)}"
            logger.error(f"[UI] {error_msg}")
            self.error_occurred.emit(error_msg)
            return []

    async def _get_collections_direct(self) -> List[Dict]:
        """Get collections via direct access"""
        try:
            if not self._collection_manager:
                return []
                
            # Get collection names
            collection_names = []
            try:
                client = self._collection_manager.client
                if client:
                    raw_collections = client.list_collections()
                    collection_names = raw_collections or []
            except Exception as e:
                logger.warning(f"[UI] Could not list collections: {e}")
                # Try direct Qdrant API as fallback
                try:
                    import requests
                    url = "http://localhost:6333/collections"
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        result = data.get("result", {})
                        collections_list = result.get("collections", [])
                        if collections_list:
                            names = [c["name"] for c in collections_list]
                            collection_names = names
                    else:
                        status = response.status_code
                        msg = f"[UI] Qdrant API returned status {status}"
                        logger.warning(msg)
                except Exception as api_error:
                    msg = f"[UI] Qdrant API fallback failed: {api_error}"
                    logger.warning(msg)
                
                # Final fallback to known collection names if all else fails
                if not collection_names:
                    collection_names = [
                        "autogen_global",
                        "autogen_agent",
                        "autogen_thread",
                        "autogen_objectives",
                        "autogen_artifacts"
                    ]

            # Format as expected by UI
            collections = []
            for name in collection_names:
                # Get actual document count from Qdrant
                doc_count = 0
                try:
                    import requests
                    url = f"http://localhost:6333/collections/{name}"
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        result = data.get("result", {})
                        doc_count = result.get("points_count", 0)
                except Exception as e:
                    logger.warning(f"[UI] Could not get count for {name}: {e}")
                
                collections.append({
                    "name": name,
                    "documents": doc_count,
                    "vectors": doc_count,  # Assume same as documents
                    "status": "Active"
                })
                
            msg = f"Direct collections returned {len(collections)} collections"
            logger.info(f"[UI] {msg}")
            return collections
            
        except Exception as e:
            logger.error(f"[UI] Direct collections failed: {e}")
            raise

    async def _get_collections_http(self) -> List[Dict]:
        """Get collections via HTTP API"""
        import aiohttp
        
        try:
            async with aiohttp.ClientSession() as session:
                collections_url = f"{self.server_url}/collections"
                async with session.get(collections_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Handle both list and dict responses
                        if isinstance(data, list):
                            collections = data
                        else:
                            collections = data.get(
                                "collections", data.get("result", [])
                            )
                        msg = f"HTTP collections returned {len(collections)}"
                        logger.info(f"[UI] {msg}")
                        return collections
                    else:
                        text = await response.text()
                        raise RuntimeError(f"HTTP {response.status}: {text}")
                        
        except Exception as e:
            logger.error(f"[UI] HTTP collections failed: {e}")
            raise

    async def get_stats(self) -> Dict:
        """Get memory statistics"""
        if not self._initialized:
            self.error_occurred.emit("Memory service not initialized")
            return {}

        try:
            if self.local_mode:
                return await self._get_stats_direct()
            else:
                return await self._get_stats_http()
                
        except Exception as e:
            error_msg = f"Failed to get memory stats: {str(e)}"
            logger.error(f"[UI] {error_msg}")
            self.error_occurred.emit(error_msg)
            return {"status": "error", "message": str(e)}

    async def _get_stats_direct(self) -> Dict:
        """Get stats via direct access"""
        try:
            collections = await self._get_collections_direct()
            total_docs = sum(c.get("documents", 0) for c in collections)
            total_collections = len(collections)
            ready_collections = sum(
                1 for c in collections if c.get("documents", 0) > 0
            )
            
            return {
                "status": "ready" if total_docs > 0 else "empty",
                "total_collections": total_collections,
                "total_documents": total_docs,
                "collections_ready": ready_collections,
                "message": (
                    f"Found {total_docs} documents in {ready_collections} "
                    "active collections"
                )
            }
            
        except Exception as e:
            logger.error(f"[UI] Direct stats failed: {e}")
            raise

    async def _get_stats_http(self) -> Dict:
        """Get stats via HTTP API"""
        import aiohttp
        
        try:
            async with aiohttp.ClientSession() as session:
                stats_url = f"{self.server_url}/memory/stats"
                async with session.get(stats_url) as response:
                    if response.status == 200:
                        stats = await response.json()
                        logger.info("[UI] HTTP stats retrieved successfully")
                        return stats
                    else:
                        text = await response.text()
                        raise RuntimeError(f"HTTP {response.status}: {text}")
                        
        except Exception as e:
            logger.error(f"[UI] HTTP stats failed: {e}")
            raise

    def is_initialized(self) -> bool:
        """Check if service is initialized"""
        return self._initialized

    def set_local_mode(self, enabled: bool):
        """Set local mode on/off"""
        if self.local_mode != enabled:
            self.local_mode = enabled
            self._initialized = False  # Require re-initialization
            logger.info(f"[UI] Local mode set to {enabled}")

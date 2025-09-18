import os
import asyncio
from datetime import datetime, timezone
import uuid
import json
import re
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv
from fastapi import (
    FastAPI,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    UploadFile,
    File,
)
from pydantic import BaseModel

from autogen_mcp.multi_memory import MultiScopeMemoryService
from autogen_mcp.memory_collections import CollectionManager, MemoryScope
from autogen_mcp.knowledge_seeder import KnowledgeSeeder
from autogen_mcp.hybrid_search_service import HybridSearchService, HybridConfig
from autogen_mcp.orchestrator import AgentOrchestrator
from autogen_mcp.gemini_client import GeminiClient
from autogen_mcp.observability import get_logger
from autogen_mcp.artifact_memory import ArtifactMemoryService
from autogen_mcp.cross_project_learning import CrossProjectLearningService
from autogen_mcp.memory_analytics import MemoryAnalyticsService, PruningStrategy

# Load environment variables from .env file
load_dotenv()

# Initialize services
logger = get_logger("autogen.mcp_server")
collection_manager = CollectionManager()
memory_service = MultiScopeMemoryService(collection_manager)
knowledge_seeder = KnowledgeSeeder(collection_manager)
hybrid_search = HybridSearchService(HybridConfig())

# Initialize artifact memory and cross-project learning services
artifact_service = ArtifactMemoryService(memory_service)
cross_project_service = CrossProjectLearningService(memory_service, artifact_service)

# Initialize memory analytics service
memory_analytics_service = MemoryAnalyticsService(memory_service)

# Initialize Gemini client only if API key is available
try:
    gemini_client = GeminiClient()
except RuntimeError as e:
    logger.warning(f"Gemini client initialization failed: {e}")
    gemini_client = None

# Global session storage (in production, use Redis or database)
active_sessions: dict[str, dict] = {}


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected for session {session_id}")

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected for session {session_id}")

    async def send_personal_message(self, message: str, session_id: str):
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            await websocket.send_text(message)

    async def broadcast_session_update(self, session_id: str, update: dict):
        message = json.dumps(
            {"type": "session_update", "session_id": session_id, "data": update}
        )
        await self.send_personal_message(message, session_id)


manager = ConnectionManager()

app = FastAPI(title="AutoGen MCP Server")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/workspace")
def workspace():
    # Return the workspace folder path (could be set via env or config)
    workspace_path = os.getenv("MCP_WORKSPACE", os.getcwd())
    return {"workspace": workspace_path}


# --- Agent Orchestration Endpoints ---


class OrchestrateRequest(BaseModel):
    project: str
    agents: list[str]
    objective: str
    working_directory: Optional[str] = None


class OrchestrateResponse(BaseModel):
    session_id: str
    status: str


class SessionInfo(BaseModel):
    session_id: str
    project: str
    objective: str
    working_directory: Optional[str] = None
    status: str
    agents: list[str]
    created_at: str


class SessionsResponse(BaseModel):
    sessions: list[SessionInfo]


@app.post("/orchestrate/start", response_model=OrchestrateResponse)
async def start_orchestration(req: OrchestrateRequest):
    try:
        logger.info(
            "Starting orchestration",
            extra={
                "extra": {
                    "project": req.project,
                    "agents": req.agents,
                    "objective": req.objective,
                    "working_directory": req.working_directory,
                }
            },
        )

        session_id = str(uuid.uuid4())

        # Determine working directory for this session
        working_dir = req.working_directory or os.getenv("MCP_WORKSPACE", os.getcwd())

        # Validate and create working directory if needed
        if not os.path.exists(working_dir):
            try:
                os.makedirs(working_dir, exist_ok=True)
                logger.info(f"Created working directory: {working_dir}")
            except Exception as e:
                logger.error(f"Failed to create working directory {working_dir}: {e}")
                raise HTTPException(
                    status_code=400, detail=f"Invalid working directory: {working_dir}"
                )

        # Configure agent configs based on request
        agent_configs = [
            {"role": role, "name": f"{role.lower()}_{session_id[:8]}"}
            for role in req.agents
        ]

        # Create orchestrator for this session
        if gemini_client is None:
            raise HTTPException(
                status_code=503,
                detail="Gemini client not available. Set GEMINI_API_KEY.",
            )

        orchestrator = AgentOrchestrator(agent_configs, gemini_client)

        # Start the session with the objective
        orchestrator.start_session(req.objective)

        # Store session with working directory
        active_sessions[session_id] = {
            "orchestrator": orchestrator,
            "project": req.project,
            "objective": req.objective,
            "working_directory": working_dir,
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        # Start the initial conversation with the objective
        try:
            # Give the agents the initial prompt to start working
            initial_prompt = f"Begin working on this objective: {req.objective}"
            orchestrator.run_turn(initial_prompt, session_id)
            logger.info(
                "Initial agent conversation started",
                extra={"extra": {"session_id": session_id, "objective": req.objective}},
            )
        except Exception as e:
            logger.warning(
                "Failed to start initial conversation",
                extra={"extra": {"session_id": session_id, "error": str(e)}},
            )

        logger.info(
            "Orchestration started", extra={"extra": {"session_id": session_id}}
        )
        # Broadcast session started update
        try:
            await manager.broadcast_session_update(
                session_id,
                {
                    "status": "started",
                    "project": req.project,
                    "agents": [
                        c.get("role", c.get("name", "unknown")) for c in agent_configs
                    ],
                },
            )
        except Exception as be:
            logger.warning(
                "Broadcast failed on start", extra={"extra": {"error": str(be)}}
            )

        # Start a background task to periodically broadcast session progress
        async def _progress_loop():
            step = 0
            try:
                while (
                    session_id in active_sessions
                    and active_sessions[session_id].get("status") == "active"
                ):
                    step += 1
                    update = {
                        "status": "active",
                        "progress_step": step,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                    try:
                        await manager.broadcast_session_update(session_id, update)
                    except Exception as pe:
                        logger.warning(
                            "Broadcast failed on progress",
                            extra={"extra": {"error": str(pe)}},
                        )
                    await asyncio.sleep(2)
            except asyncio.CancelledError:
                # graceful stop
                pass

        task = asyncio.create_task(_progress_loop())
        active_sessions[session_id]["progress_task"] = task
        return {"session_id": session_id, "status": "started"}

    except Exception as e:
        logger.error(
            "Failed to start orchestration", extra={"extra": {"error": str(e)}}
        )
        raise HTTPException(status_code=500, detail=f"Orchestration failed: {str(e)}")


class StopRequest(BaseModel):
    session_id: str


@app.post("/orchestrate/stop")
async def stop_orchestration(req: StopRequest):
    try:
        logger.info(
            "Stopping orchestration", extra={"extra": {"session_id": req.session_id}}
        )

        if req.session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")

        # Update session status
        active_sessions[req.session_id]["status"] = "stopped"
        # Cancel progress task if running
        task = active_sessions[req.session_id].get("progress_task")
        if task:
            try:
                task.cancel()
            except Exception:
                pass

        logger.info(
            "Orchestration stopped", extra={"extra": {"session_id": req.session_id}}
        )
        # Broadcast session stopped update
        try:
            await manager.broadcast_session_update(
                req.session_id,
                {"status": "stopped"},
            )
        except Exception as be:
            logger.warning(
                "Broadcast failed on stop", extra={"extra": {"error": str(be)}}
            )
        return {"session_id": req.session_id, "status": "stopped"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to stop orchestration", extra={"extra": {"error": str(e)}})
        raise HTTPException(status_code=500, detail=f"Stop failed: {str(e)}")


@app.get("/orchestrate/sessions", response_model=SessionsResponse)
async def list_sessions():
    """List all active and stopped orchestration sessions."""
    try:
        sessions = []
        for session_id, session_data in active_sessions.items():
            # Extract agent roles from the orchestrator
            agent_roles = []
            if "orchestrator" in session_data:
                orchestrator = session_data["orchestrator"]
                if hasattr(orchestrator, "agent_configs"):
                    agent_roles = [
                        config.get("role", config.get("name", "unknown"))
                        for config in orchestrator.agent_configs
                    ]

            session_info = SessionInfo(
                session_id=session_id,
                project=session_data.get("project", "unknown"),
                objective=session_data.get("objective", ""),
                working_directory=session_data.get("working_directory"),
                status=session_data.get("status", "unknown"),
                agents=agent_roles,
                created_at=session_data.get(
                    "created_at", datetime.utcnow().isoformat() + "Z"
                ),
            )
            sessions.append(session_info)

        logger.info(
            "Listed sessions", extra={"extra": {"session_count": len(sessions)}}
        )
        return SessionsResponse(sessions=sessions)

    except Exception as e:
        logger.error("Failed to list sessions", extra={"extra": {"error": str(e)}})
        raise HTTPException(status_code=500, detail=f"Session listing failed: {str(e)}")


class MemorySearchRequest(BaseModel):
    query: str
    scope: str = "project"
    k: int = 5


@app.post("/memory/search")
async def memory_search(req: MemorySearchRequest):
    try:
        logger.info(
            "Memory search request",
            extra={
                "extra": {
                    "query": req.query,
                    "scope": req.scope,
                    "k": req.k,
                }
            },
        )

        # Map scope to our memory scope enum
        scope_mapping = {
            "global": MemoryScope.GLOBAL,
            "project": MemoryScope.PROJECT,
            "agent": MemoryScope.AGENT,
            "thread": MemoryScope.THREAD,
            "objectives": MemoryScope.OBJECTIVES,
            "artifacts": MemoryScope.ARTIFACTS,
        }

        memory_scope = scope_mapping.get(req.scope.lower(), MemoryScope.PROJECT)

        # Get project context
        workspace_path = os.getenv("MCP_WORKSPACE", os.getcwd())
        project_name = os.path.basename(workspace_path)

        # Set project context if needed
        if memory_scope == MemoryScope.PROJECT:
            memory_service.set_project(project_name)

        # Get collection name with proper project ID
        project_id = project_name if memory_scope == MemoryScope.PROJECT else None
        collection_name = collection_manager.get_collection_name(
            memory_scope, project_id
        )
        search_results = hybrid_search.search(
            collection=collection_name,
            query=req.query,
            k=req.k,
            scopes=[req.scope.lower()],
        )

        # Format results for response
        results = [
            {
                "id": result.get("id"),
                "score": result.get("score", 0.0),
                "text": result.get("metadata", {}).get("text", ""),
                "scope": result.get("scope", req.scope),
                "metadata": result.get("metadata", {}),
            }
            for result in search_results
        ]

        logger.info(
            "Memory search completed",
            extra={"extra": {"results_count": len(results)}},
        )
        return {
            "results": results,
            "query": req.query,
            "scope": req.scope,
            "k": req.k,
        }

    except Exception as e:
        logger.error("Memory search failed", extra={"extra": {"error": str(e)}})
        raise HTTPException(status_code=500, detail=f"Memory search failed: {str(e)}")


class MemoryDeleteRequest(BaseModel):
    point_ids: List[str]
    collection: str
    backup: bool = True


class FilteredDeleteRequest(BaseModel):
    collection: str
    filters: dict
    max_count: int = 100
    backup: bool = True


class DeleteResponse(BaseModel):
    success: bool
    deleted_count: int
    message: str
    backup_created: bool = False


@app.delete("/memory/point/{collection_name}/{point_id}")
async def delete_memory_point(collection_name: str, point_id: str):
    """Delete a specific memory point by ID"""
    try:
        logger.info(
            "Deleting memory point",
            extra={
                "extra": {
                    "collection": collection_name,
                    "point_id": point_id,
                }
            },
        )

        # Use the collection manager to get the proper collection
        if collection_manager.collection_exists(collection_name):
            # Delete point using qdrant client
            result = collection_manager.q.delete_point(collection_name, point_id)

            logger.info(
                "Memory point deleted",
                extra={
                    "extra": {
                        "collection": collection_name,
                        "point_id": point_id,
                        "result": result,
                    }
                },
            )

            return DeleteResponse(
                success=True,
                deleted_count=1,
                message=f"Memory point {point_id} deleted successfully",
            )
        else:
            raise HTTPException(
                status_code=404, detail=f"Collection {collection_name} not found"
            )

    except Exception as e:
        logger.error(
            "Failed to delete memory point",
            extra={
                "extra": {
                    "collection": collection_name,
                    "point_id": point_id,
                    "error": str(e),
                }
            },
        )
        raise HTTPException(
            status_code=500, detail=f"Memory point deletion failed: {str(e)}"
        )


@app.delete("/memory/collection/{collection_name}")
async def delete_memory_collection(collection_name: str, confirm: bool = False):
    """Delete entire memory collection"""
    try:
        if not confirm:
            raise HTTPException(
                status_code=400,
                detail="Collection deletion requires confirmation parameter: ?confirm=true",
            )

        logger.info(
            "Deleting memory collection",
            extra={"extra": {"collection": collection_name}},
        )

        if collection_manager.collection_exists(collection_name):
            # Get collection info for logging
            collection_info = collection_manager.q.get_collection_info(collection_name)
            points_count = collection_info.get("points_count", 0)

            # Delete collection
            result = collection_manager.q.delete_collection(collection_name)

            logger.info(
                "Memory collection deleted",
                extra={
                    "extra": {
                        "collection": collection_name,
                        "points_deleted": points_count,
                        "result": result,
                    }
                },
            )

            return DeleteResponse(
                success=True,
                deleted_count=points_count,
                message=f"Collection {collection_name} with {points_count} points deleted successfully",
            )
        else:
            raise HTTPException(
                status_code=404, detail=f"Collection {collection_name} not found"
            )

    except Exception as e:
        logger.error(
            "Failed to delete memory collection",
            extra={
                "extra": {
                    "collection": collection_name,
                    "error": str(e),
                }
            },
        )
        raise HTTPException(
            status_code=500, detail=f"Memory collection deletion failed: {str(e)}"
        )


@app.post("/memory/delete/batch")
async def batch_delete_memory_points(req: MemoryDeleteRequest):
    """Delete multiple memory points by IDs"""
    try:
        logger.info(
            "Batch deleting memory points",
            extra={
                "extra": {
                    "collection": req.collection,
                    "point_count": len(req.point_ids),
                    "backup": req.backup,
                }
            },
        )

        if not collection_manager.collection_exists(req.collection):
            raise HTTPException(
                status_code=404, detail=f"Collection {req.collection} not found"
            )

        # Delete multiple points
        result = collection_manager.q.delete_points(req.collection, req.point_ids)

        logger.info(
            "Batch memory points deleted",
            extra={
                "extra": {
                    "collection": req.collection,
                    "deleted_count": len(req.point_ids),
                    "result": result,
                }
            },
        )

        return DeleteResponse(
            success=True,
            deleted_count=len(req.point_ids),
            message=f"Successfully deleted {len(req.point_ids)} memory points",
        )

    except Exception as e:
        logger.error(
            "Batch memory point deletion failed",
            extra={
                "extra": {
                    "collection": req.collection,
                    "error": str(e),
                }
            },
        )
        raise HTTPException(
            status_code=500, detail=f"Batch memory deletion failed: {str(e)}"
        )


@app.post("/memory/delete/filtered")
async def delete_filtered_memory(req: FilteredDeleteRequest):
    """Delete memory entries matching specific criteria"""
    try:
        logger.info(
            "Filtered memory deletion",
            extra={
                "extra": {
                    "collection": req.collection,
                    "filters": req.filters,
                    "max_count": req.max_count,
                    "backup": req.backup,
                }
            },
        )

        if not collection_manager.collection_exists(req.collection):
            raise HTTPException(
                status_code=404, detail=f"Collection {req.collection} not found"
            )

        # Use scroll to find matching points first
        scroll_result = collection_manager.q.scroll(
            collection=req.collection,
            must=[req.filters],
            limit=req.max_count,
            with_payload=True,
        )

        points = scroll_result.get("result", {}).get("points", [])
        point_ids = [point.get("id") for point in points if point.get("id")]

        if not point_ids:
            return DeleteResponse(
                success=True,
                deleted_count=0,
                message="No memory entries matched the filter criteria",
            )

        # Delete the matching points
        result = collection_manager.q.delete_points(req.collection, point_ids)

        logger.info(
            "Filtered memory deletion completed",
            extra={
                "extra": {
                    "collection": req.collection,
                    "deleted_count": len(point_ids),
                    "result": result,
                }
            },
        )

        return DeleteResponse(
            success=True,
            deleted_count=len(point_ids),
            message=f"Successfully deleted {len(point_ids)} memory entries matching criteria",
        )

    except Exception as e:
        logger.error(
            "Filtered memory deletion failed",
            extra={
                "extra": {
                    "collection": req.collection,
                    "error": str(e),
                }
            },
        )
        raise HTTPException(
            status_code=500, detail=f"Filtered memory deletion failed: {str(e)}"
        )


class ObjectiveAddRequest(BaseModel):
    objective: str
    project: str


@app.post("/objective/add")
async def objective_add(req: ObjectiveAddRequest):
    try:
        logger.info(
            "Adding objective",
            extra={
                "extra": {
                    "objective": req.objective,
                    "project": req.project,
                }
            },
        )

        # Write objective to memory using new multi-scope system
        thread_id = f"objectives_{req.project}"
        memory_service.set_project(req.project)

        # Use the new write_objectives method
        objective_id = memory_service.write_objectives(
            thread_id=thread_id,
            text=req.objective,
            metadata={"type": "objective", "project": req.project},
        )

        logger.info(
            "Objective added",
            extra={"extra": {"objective_id": objective_id}},
        )
        return {
            "status": "added",
            "objective": req.objective,
            "project": req.project,
            "objective_id": objective_id,
        }

    except Exception as e:
        logger.error(
            "Failed to add objective",
            extra={"extra": {"error": str(e)}},
        )
        raise HTTPException(status_code=500, detail=f"Add objective failed: {str(e)}")


# --- Memory File Upload Endpoint ---


def chunk_markdown_content(content: str, filename: str) -> List[dict]:
    """
    Chunk markdown content into meaningful sections.

    Args:
        content: The markdown content to chunk
        filename: Name of the source file

    Returns:
        List of chunks with metadata
    """
    chunks = []

    # Split by markdown headers (## sections)
    sections = re.split(r"\n(?=#{1,3}\s)", content)

    for i, section in enumerate(sections):
        if not section.strip():
            continue

        # Extract section title if it exists
        title_match = re.match(r"^(#{1,3})\s+(.+?)(?:\n|$)", section)
        title = title_match.group(2) if title_match else f"Section {i + 1}"

        # Split section into smaller chunks if it's too long (>2000 chars)
        if len(section) > 2000:
            # Split by paragraphs (double newlines)
            paragraphs = section.split("\n\n")

            current_chunk = ""
            chunk_index = 0

            for paragraph in paragraphs:
                if len(current_chunk + paragraph) > 1500 and current_chunk:
                    # Save current chunk
                    chunks.append(
                        {
                            "content": current_chunk.strip(),
                            "metadata": {
                                "filename": filename,
                                "section_title": title,
                                "chunk_index": chunk_index,
                                "total_sections": len(sections),
                                "type": "markdown_chunk",
                                "upload_date": datetime.now(timezone.utc).isoformat(),
                            },
                        }
                    )
                    current_chunk = paragraph
                    chunk_index += 1
                else:
                    if current_chunk:
                        current_chunk += f"\n\n{paragraph}"
                    else:
                        current_chunk = paragraph

            # Add final chunk if there's remaining content
            if current_chunk.strip():
                chunks.append(
                    {
                        "content": current_chunk.strip(),
                        "metadata": {
                            "filename": filename,
                            "section_title": title,
                            "chunk_index": chunk_index,
                            "total_sections": len(sections),
                            "type": "markdown_chunk",
                            "upload_date": datetime.now(timezone.utc).isoformat(),
                        },
                    }
                )
        else:
            # Section is small enough, use as single chunk
            chunks.append(
                {
                    "content": section.strip(),
                    "metadata": {
                        "filename": filename,
                        "section_title": title,
                        "chunk_index": i,
                        "total_sections": len(sections),
                        "type": "markdown_chunk",
                        "upload_date": datetime.now(timezone.utc).isoformat(),
                    },
                }
            )

    return chunks


class FileUploadResponse(BaseModel):
    status: str
    filename: str
    chunks_processed: int
    total_size: int
    message: str


@app.post("/memory/upload", response_model=FileUploadResponse)
async def upload_file_to_memory(
    file: UploadFile = File(...), project: str = "default", scope: str = "project"
):
    """
    Upload and process a markdown file into memory.

    Args:
        file: The uploaded file (must be .md extension)
        project: Project context for the file
        scope: Memory scope (project, global, etc.)

    Returns:
        Upload status and processing details
    """
    try:
        # Validate file type
        if not file.filename.endswith(".md"):
            raise HTTPException(
                status_code=400, detail="Only markdown (.md) files are supported"
            )

        # Read file content
        content = await file.read()
        content_str = content.decode("utf-8")

        logger.info(
            "Processing uploaded file",
            extra={
                "extra": {
                    "filename": file.filename,
                    "size": len(content),
                    "project": project,
                    "scope": scope,
                }
            },
        )

        # Chunk the content
        chunks = chunk_markdown_content(content_str, file.filename)

        if not chunks:
            raise HTTPException(
                status_code=400, detail="No content could be extracted from the file"
            )

        # Map scope to memory scope enum
        scope_mapping = {
            "global": MemoryScope.GLOBAL,
            "project": MemoryScope.PROJECT,
            "agent": MemoryScope.AGENT,
            "thread": MemoryScope.THREAD,
            "objectives": MemoryScope.OBJECTIVES,
            "artifacts": MemoryScope.ARTIFACTS,
        }

        memory_scope = scope_mapping.get(scope.lower(), MemoryScope.PROJECT)

        # Set project context
        memory_service.set_project(project)

        # Process each chunk
        processed_count = 0
        thread_id = f"upload_{project}_{uuid.uuid4().hex[:8]}"

        for chunk in chunks:
            try:
                # Write chunk to appropriate memory scope
                if memory_scope == MemoryScope.GLOBAL:
                    memory_service.write_global(
                        thread_id=thread_id,
                        text=chunk["content"],
                        metadata=chunk["metadata"],
                    )
                elif memory_scope == MemoryScope.PROJECT:
                    memory_service.write_project(
                        thread_id=thread_id,
                        text=chunk["content"],
                        metadata=chunk["metadata"],
                    )
                elif memory_scope == MemoryScope.ARTIFACTS:
                    memory_service.write_artifacts(
                        thread_id=thread_id,
                        text=chunk["content"],
                        metadata=chunk["metadata"],
                    )
                else:
                    # Default to project scope
                    memory_service.write_project(
                        thread_id=thread_id,
                        text=chunk["content"],
                        metadata=chunk["metadata"],
                    )

                processed_count += 1

            except Exception as chunk_error:
                logger.error(
                    "Failed to process chunk - detailed error",
                    extra={
                        "extra": {
                            "filename": file.filename,
                            "chunk_index": chunk.get("metadata", {}).get(
                                "chunk_index", 0
                            ),
                            "error": str(chunk_error),
                            "chunk_content_preview": (
                                chunk["content"][:100] + "..."
                                if len(chunk["content"]) > 100
                                else chunk["content"]
                            ),
                            "memory_scope": memory_scope.value,
                            "project": project,
                            "thread_id": thread_id,
                        }
                    },
                )
                # Don't silently continue - if chunks are failing, we need to know why
                # For debugging, let's re-raise the first few errors
                if processed_count == 0:  # First chunk failed
                    logger.error(f"First chunk failed with error: {chunk_error}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Memory write failed: {str(chunk_error)}",
                    )

        logger.info(
            "File upload completed",
            extra={
                "extra": {
                    "filename": file.filename,
                    "chunks_processed": processed_count,
                    "total_chunks": len(chunks),
                    "project": project,
                    "scope": scope,
                }
            },
        )

        return FileUploadResponse(
            status="success",
            filename=file.filename,
            chunks_processed=processed_count,
            total_size=len(content),
            message=(
                f"Successfully processed {processed_count} chunks from {file.filename}"
            ),
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(
            "File upload failed",
            extra={
                "extra": {
                    "error": str(e),
                    "filename": getattr(file, "filename", "unknown"),
                }
            },
        )
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")


# --- File Operations Endpoints ---


class WriteFileRequest(BaseModel):
    file_path: str
    content: str
    project: str


class ListFilesResponse(BaseModel):
    files: List[str]
    directories: List[str]


@app.post("/workspace/write")
async def write_file(req: WriteFileRequest):
    try:
        logger.info(
            "Writing file",
            extra={"extra": {"file_path": req.file_path, "project": req.project}},
        )

        workspace_path = os.getenv("MCP_WORKSPACE", os.getcwd())
        full_path = Path(workspace_path) / req.file_path

        # Ensure directory exists
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(req.content)

        # Log to memory using new multi-scope system
        memory_service.set_project(req.project)
        memory_service.write_artifacts(
            thread_id=f"files_{req.project}",
            text=f"Created file: {req.file_path}",
            metadata={
                "type": "file_write",
                "file_path": req.file_path,
                "project": req.project,
            },
        )

        logger.info(
            "File written successfully", extra={"extra": {"file_path": req.file_path}}
        )
        return {
            "status": "success",
            "file_path": req.file_path,
            "size": len(req.content),
        }

    except Exception as e:
        logger.error("Failed to write file", extra={"extra": {"error": str(e)}})
        raise HTTPException(status_code=500, detail=f"File write failed: {str(e)}")


@app.get("/workspace/files", response_model=ListFilesResponse)
async def list_files():
    try:
        workspace_path = Path(os.getenv("MCP_WORKSPACE", os.getcwd()))

        files = []
        directories = []

        for item in workspace_path.rglob("*"):
            if item.is_file():
                # Get relative path from workspace
                rel_path = item.relative_to(workspace_path)
                files.append(str(rel_path))
            elif item.is_dir() and item != workspace_path:
                rel_path = item.relative_to(workspace_path)
                directories.append(str(rel_path))

        logger.info(
            "Listed workspace files",
            extra={"extra": {"file_count": len(files), "dir_count": len(directories)}},
        )
        return ListFilesResponse(files=files, directories=directories)

    except Exception as e:
        logger.error("Failed to list files", extra={"extra": {"error": str(e)}})
        raise HTTPException(status_code=500, detail=f"File listing failed: {str(e)}")


# --- Cross-Project Learning Endpoints ---


class RegisterProjectRequest(BaseModel):
    project_id: str
    name: str
    description: str
    tech_stack: list[str]
    domain: str


class ProjectRecommendationsRequest(BaseModel):
    project_id: str


class MemoryOptimizationRequest(BaseModel):
    strategy: str = "hybrid"  # lru, importance, frequency, hybrid
    target_reduction_percent: float = 15.0
    dry_run: bool = False


@app.post("/cross-project/register")
async def register_project(req: RegisterProjectRequest):
    """Register a project for cross-project learning"""
    try:
        logger.info(
            "Registering project for cross-project learning",
            extra={
                "extra": {
                    "project_id": req.project_id,
                    "name": req.name,
                    "domain": req.domain,
                    "tech_stack": req.tech_stack,
                }
            },
        )

        project_profile = cross_project_service.register_project(
            project_id=req.project_id,
            name=req.name,
            description=req.description,
            tech_stack=req.tech_stack,
            domain=req.domain,
        )

        logger.info(
            "Project registered successfully",
            extra={"extra": {"project_id": req.project_id}},
        )

        return {
            "project_id": project_profile.project_id,
            "name": project_profile.name,
            "domain": project_profile.domain,
            "patterns_detected": project_profile.patterns_used,
            "success_metrics": project_profile.success_metrics,
            "status": "registered",
        }

    except Exception as e:
        logger.error(
            "Failed to register project",
            extra={"extra": {"error": str(e), "project_id": req.project_id}},
        )
        raise HTTPException(
            status_code=500, detail=f"Project registration failed: {str(e)}"
        )


@app.post("/cross-project/recommendations")
async def get_project_recommendations(req: ProjectRecommendationsRequest):
    """Get cross-project learning recommendations for a project"""
    try:
        logger.info(
            "Getting cross-project recommendations",
            extra={"extra": {"project_id": req.project_id}},
        )

        recommendations = cross_project_service.get_project_recommendations(
            req.project_id
        )

        logger.info(
            "Generated cross-project recommendations",
            extra={
                "extra": {
                    "project_id": req.project_id,
                    "similar_projects_count": len(
                        recommendations.get("similar_projects", [])
                    ),
                    "solutions_count": len(
                        recommendations.get("recommended_solutions", [])
                    ),
                    "practices_count": len(
                        recommendations.get("recommended_practices", [])
                    ),
                }
            },
        )

        return recommendations

    except Exception as e:
        logger.error(
            "Failed to get project recommendations",
            extra={"extra": {"error": str(e), "project_id": req.project_id}},
        )
        raise HTTPException(
            status_code=500,
            detail=f"Project recommendations failed: {str(e)}",
        )


@app.get("/cross-project/analysis")
async def get_cross_project_analysis():
    """Get cross-project pattern analysis and insights"""
    try:
        logger.info("Getting cross-project analysis")

        analysis = cross_project_service.analyze_cross_project_patterns()

        logger.info(
            "Generated cross-project analysis",
            extra={
                "extra": {
                    "total_projects": analysis.get("total_projects", 0),
                    "insights_count": len(analysis.get("cross_project_insights", [])),
                }
            },
        )

        return analysis

    except Exception as e:
        logger.error(
            "Failed to get cross-project analysis",
            extra={"extra": {"error": str(e)}},
        )
        raise HTTPException(
            status_code=500,
            detail=f"Cross-project analysis failed: {str(e)}",
        )


# --- Memory Analytics Endpoints ---


@app.get("/memory/stats")
async def get_memory_stats():
    """Get basic memory statistics for UI"""
    try:
        logger.info("Getting memory stats for UI")

        # Check if memory service is initialized
        if (
            not hasattr(memory_service, "collection_manager")
            or not memory_service.collection_manager
        ):
            logger.warning("Memory service not fully initialized")
            return {
                "status": "initializing",
                "message": "Memory service is starting up...",
            }

        # Check if Qdrant client is available
        if (
            not hasattr(memory_service.collection_manager, "client")
            or not memory_service.collection_manager.client
        ):
            logger.warning("Qdrant client not available")
            return {
                "status": "connecting",
                "message": "Connecting to memory database...",
            }

        # Get basic collection stats
        stats = {}
        total_documents = 0

        # Get stats from Qdrant directly
        for scope in [
            "global",
            "project",
            "agent",
            "thread",
            "objectives",
            "artifacts",
        ]:
            try:
                collection_name = collection_manager.get_collection_name(
                    getattr(MemoryScope, scope.upper()), None
                )

                # Check if collection exists before getting info
                try:
                    info = memory_service.collection_manager.client.get_collection(
                        collection_name
                    )
                    stats[collection_name] = {
                        "documents_count": info.points_count,
                        "vectors_count": info.points_count,
                        "points_count": info.points_count,
                        "indexed_vectors_count": info.points_count,
                        "status": "green" if info.status == "green" else "yellow",
                    }
                    total_documents += info.points_count
                except Exception as collection_error:
                    logger.debug(
                        f"Collection {collection_name} not ready or doesn't exist: {collection_error}"
                    )
                    stats[collection_name] = {
                        "documents_count": 0,
                        "vectors_count": 0,
                        "points_count": 0,
                        "indexed_vectors_count": 0,
                        "status": "not_ready",
                    }
            except Exception as e:
                logger.warning(f"Failed to get stats for {scope}: {e}")
                stats[f"autogen_{scope}"] = {
                    "documents_count": 0,
                    "vectors_count": 0,
                    "points_count": 0,
                    "indexed_vectors_count": 0,
                    "status": "error",
                }

        # Add summary stats
        stats["summary"] = {
            "total_documents": total_documents,
            "collections_ready": len(
                [
                    s
                    for s in stats.values()
                    if isinstance(s, dict) and s.get("status") == "green"
                ]
            ),
            "total_collections": len(stats) - 1,  # Exclude the summary itself
            "overall_status": "ready" if total_documents > 0 else "empty",
        }

        logger.info("Memory stats retrieved successfully")
        return stats

    except Exception as e:
        logger.error("Failed to get memory stats", extra={"extra": {"error": str(e)}})
        # Return a safe fallback instead of raising an exception
        return {
            "status": "error",
            "message": f"Failed to get memory statistics: {str(e)}",
            "collections": 0,
            "total_documents": 0,
        }


@app.get("/memory/analytics/report")
async def get_memory_analytics_report():
    """Get comprehensive memory analytics report"""
    try:
        logger.info("Generating memory analytics report")

        report = await memory_analytics_service.get_analytics_report()

        logger.info(
            "Memory analytics report generated",
            extra={
                "extra": {
                    "total_entries": report["metrics"]["storage"]["total_entries"],
                    "memory_utilization": report["metrics"]["health"][
                        "memory_utilization"
                    ],
                    "health_status": report["health_status"],
                    "alerts_count": len(report["alerts"]),
                }
            },
        )

        return {"report": report, "timestamp": datetime.now(timezone.utc).isoformat()}

    except Exception as e:
        logger.error(
            "Failed to generate memory analytics report",
            extra={"extra": {"error": str(e)}},
        )
        raise HTTPException(
            status_code=500,
            detail=f"Memory analytics report failed: {str(e)}",
        )


@app.get("/memory/analytics/health")
async def get_memory_health():
    """Get memory system health status and alerts"""
    try:
        logger.info("Checking memory health")

        (
            health_status,
            alerts,
        ) = await memory_analytics_service.health_monitor.check_health()

        health_report = {
            "status": health_status,
            "alerts": [
                {
                    "severity": alert.severity,
                    "message": alert.message,
                    "metric": alert.metric_name,
                    "current_value": alert.current_value,
                    "threshold": alert.threshold,
                    "recommendations": alert.recommendations,
                    "timestamp": alert.timestamp.isoformat(),
                }
                for alert in alerts
            ],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(
            "Memory health check completed",
            extra={
                "extra": {
                    "status": health_status,
                    "alerts_count": len(alerts),
                }
            },
        )

        return health_report

    except Exception as e:
        logger.error(
            "Failed to check memory health",
            extra={"extra": {"error": str(e)}},
        )
        raise HTTPException(
            status_code=500,
            detail=f"Memory health check failed: {str(e)}",
        )


@app.post("/memory/analytics/optimize")
async def optimize_memory(req: MemoryOptimizationRequest):
    """Execute memory optimization with specified strategy"""
    try:
        logger.info(
            "Starting memory optimization",
            extra={
                "extra": {
                    "strategy": req.strategy,
                    "target_reduction": req.target_reduction_percent,
                    "dry_run": req.dry_run,
                }
            },
        )

        # Validate strategy
        valid_strategies = ["lru", "importance", "frequency", "hybrid"]
        if req.strategy not in valid_strategies:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid strategy. Must be one of: {valid_strategies}",
            )

        # Map string to enum
        strategy_mapping = {
            "lru": PruningStrategy.LRU,
            "importance": PruningStrategy.IMPORTANCE_BASED,
            "frequency": PruningStrategy.ACCESS_FREQUENCY,
            "hybrid": PruningStrategy.HYBRID,
        }

        strategy = strategy_mapping[req.strategy]

        optimization_report = await memory_analytics_service.optimize_memory(
            strategy=strategy,
            target_reduction_percent=req.target_reduction_percent,
            dry_run=req.dry_run,
        )

        logger.info(
            "Memory optimization completed",
            extra={
                "extra": {
                    "entries_removed": optimization_report["results"][
                        "entries_removed"
                    ],
                    "bytes_freed": optimization_report["results"]["bytes_freed"],
                    "execution_time_ms": optimization_report["results"][
                        "execution_time_ms"
                    ],
                    "dry_run": req.dry_run,
                }
            },
        )

        return {
            "optimization_report": optimization_report,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to optimize memory",
            extra={"extra": {"error": str(e)}},
        )
        raise HTTPException(
            status_code=500,
            detail=f"Memory optimization failed: {str(e)}",
        )


@app.get("/memory/analytics/metrics")
async def get_memory_metrics():
    """Get detailed memory metrics"""
    try:
        logger.info("Collecting memory metrics")

        metrics = await memory_analytics_service.metrics_collector.collect_metrics()

        metrics_response = {
            "storage": {
                "total_entries": metrics.total_entries,
                "total_size_bytes": metrics.total_size_bytes,
                "total_size_mb": metrics.total_size_bytes / 1024 / 1024,
                "collections_count": metrics.collections_count,
                "average_entry_size_bytes": metrics.average_entry_size,
            },
            "performance": {
                "average_search_time_ms": metrics.average_search_time_ms,
                "average_write_time_ms": metrics.average_write_time_ms,
                "cache_hit_ratio": metrics.cache_hit_ratio,
                "query_success_rate": metrics.query_success_rate,
            },
            "access_patterns": {
                "read_operations": metrics.read_operations,
                "write_operations": metrics.write_operations,
                "search_operations": metrics.search_operations,
            },
            "health": {
                "memory_utilization": metrics.memory_utilization,
                "fragmentation_ratio": metrics.fragmentation_ratio,
                "oldest_entry_age_days": metrics.oldest_entry_age_days,
                "stale_entries_count": metrics.stale_entries_count,
            },
            "scope_metrics": {
                scope.value: scope_data
                for scope, scope_data in metrics.scope_metrics.items()
            },
            "collected_at": metrics.collected_at.isoformat(),
        }

        logger.info(
            "Memory metrics collected",
            extra={
                "extra": {
                    "total_entries": metrics.total_entries,
                    "total_size_mb": metrics.total_size_bytes / 1024 / 1024,
                    "collections_count": metrics.collections_count,
                }
            },
        )

        return metrics_response

    except Exception as e:
        logger.error(
            "Failed to collect memory metrics",
            extra={"extra": {"error": str(e)}},
        )
        raise HTTPException(
            status_code=500,
            detail=f"Memory metrics collection failed: {str(e)}",
        )


# --- WebSocket Endpoints ---


@app.websocket("/ws/session/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)

            # Echo back for now - in production, handle different message types
            await manager.send_personal_message(
                json.dumps({"type": "echo", "data": message}), session_id
            )
    except WebSocketDisconnect:
        manager.disconnect(session_id)


# --- Server Startup ---


async def startup_event():
    """Initialize memory system on server startup."""
    try:
        logger.info("Initializing memory system...")

        # Initialize all collections
        collection_manager.initialize_all_collections()

        # Seed global knowledge
        knowledge_seeder.seed_global_knowledge()

        # Start memory analytics monitoring
        await memory_analytics_service.start_monitoring()

        # Verify system health
        health_status = collection_manager.health_check()
        logger.info(
            "Memory system initialized",
            extra={"extra": {"collections_healthy": health_status}},
        )

    except Exception as e:
        logger.error(
            "Failed to initialize memory system",
            extra={"extra": {"error": str(e)}},
        )
        # Don't fail server startup, but log the issue
        pass


# Add startup event
app.add_event_handler("startup", startup_event)

if __name__ == "__main__":
    import uvicorn

    logger.info("Starting AutoGen MCP Server...")
    logger.info(f"Gemini client available: {gemini_client is not None}")

    uvicorn.run(app, host="0.0.0.0", port=9000, log_level="info")

import os
import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from autogen_mcp.memory import MemoryService
from autogen_mcp.orchestrator import AgentOrchestrator
from autogen_mcp.gemini_client import GeminiClient
from autogen_mcp.observability import get_logger

# Initialize services
logger = get_logger("autogen.mcp_server")
memory_service = MemoryService()

# Initialize Gemini client only if API key is available
try:
    gemini_client = GeminiClient()
except RuntimeError as e:
    logger.warning(f"Gemini client initialization failed: {e}")
    gemini_client = None

# Global session storage (in production, use Redis or database)
active_sessions: dict[str, dict] = {}

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


class OrchestrateResponse(BaseModel):
    session_id: str
    status: str


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
                }
            },
        )

        session_id = str(uuid.uuid4())

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

        # Store session
        active_sessions[session_id] = {
            "orchestrator": orchestrator,
            "project": req.project,
            "objective": req.objective,
            "status": "active",
        }

        logger.info(
            "Orchestration started", extra={"extra": {"session_id": session_id}}
        )
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

        logger.info(
            "Orchestration stopped", extra={"extra": {"session_id": req.session_id}}
        )
        return {"session_id": req.session_id, "status": "stopped"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to stop orchestration", extra={"extra": {"error": str(e)}})
        raise HTTPException(status_code=500, detail=f"Stop failed: {str(e)}")


class MemorySearchRequest(BaseModel):
    query: str
    scope: str = "project"
    k: int = 5


@app.post("/memory/search")
async def memory_search(req: MemorySearchRequest):
    try:
        logger.info(
            "Memory search request",
            extra={"extra": {"query": req.query, "scope": req.scope, "k": req.k}},
        )

        # Set project scope if specified
        if req.scope == "project":
            workspace_path = os.getenv("MCP_WORKSPACE", os.getcwd())
            project_name = os.path.basename(workspace_path)
            memory_service.set_project(project_name)

        # For now, return dummy results - TODO: implement actual search
        # This requires hybrid search service integration
        results = []

        logger.info(
            "Memory search completed", extra={"extra": {"results_count": len(results)}}
        )
        return {"results": results, "query": req.query, "scope": req.scope, "k": req.k}

    except Exception as e:
        logger.error("Memory search failed", extra={"extra": {"error": str(e)}})
        raise HTTPException(status_code=500, detail=f"Memory search failed: {str(e)}")


class ObjectiveAddRequest(BaseModel):
    objective: str
    project: str


@app.post("/objective/add")
async def objective_add(req: ObjectiveAddRequest):
    try:
        logger.info(
            "Adding objective",
            extra={"extra": {"objective": req.objective, "project": req.project}},
        )

        # Write objective to memory
        thread_id = f"objectives_{req.project}"
        memory_service.set_project(req.project)
        objective_id = memory_service.write_event(
            scope="objectives",
            thread_id=thread_id,
            text=req.objective,
            metadata={"type": "objective", "project": req.project},
        )

        logger.info("Objective added", extra={"extra": {"objective_id": objective_id}})
        return {
            "status": "added",
            "objective": req.objective,
            "project": req.project,
            "objective_id": objective_id,
        }

    except Exception as e:
        logger.error("Failed to add objective", extra={"extra": {"error": str(e)}})
        raise HTTPException(status_code=500, detail=f"Add objective failed: {str(e)}")

import os
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Hardcoded default port
SETTINGS = {"port": 9000}


app = FastAPI(title="AutoGen MCP Server")


# Settings page for port configuration
@app.get("/settings", response_class=HTMLResponse)
def get_settings_page():
    return f"""
    <html>
    <body>
        <h2>Server Settings</h2>
        <form action="/settings" method="post">
            <label for="port">Server Port:</label>
            <input type="number" id="port" name="port" value="{SETTINGS['port']}" min="1" max="65535" />
            <input type="submit" value="Update" />
        </form>
        <p>Current port: <b>{SETTINGS['port']}</b></p>
        <p style="color:gray;">Note: Changing the port requires a server restart to take effect.</p>
    </body>
    </html>
    """


@app.post("/settings", response_class=HTMLResponse)
def update_settings_page(port: int = Form(...)):
    SETTINGS["port"] = port
    return f"""
    <html>
    <body>
        <h2>Server Settings Updated</h2>
        <form action="/settings" method="post">
            <label for="port">Server Port:</label>
            <input type="number" id="port" name="port" value="{SETTINGS['port']}" min="1" max="65535" />
            <input type="submit" value="Update" />
        </form>
        <p>Current port: <b>{SETTINGS['port']}</b></p>
        <p style="color:green;">Port updated. Please restart the server to apply changes.</p>
    </body>
    </html>
    """


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
    # Dummy implementation: generate session_id
    import uuid

    session_id = str(uuid.uuid4())
    return {"session_id": session_id, "status": "started"}


class StopRequest(BaseModel):
    session_id: str


@app.post("/orchestrate/stop")
async def stop_orchestration(req: StopRequest):
    # Dummy implementation
    return {"session_id": req.session_id, "status": "stopped"}


class MemorySearchRequest(BaseModel):
    query: str
    scope: str = "project"
    k: int = 5


@app.post("/memory/search")
async def memory_search(req: MemorySearchRequest):
    # Dummy implementation: return empty results
    return {"results": [], "query": req.query, "scope": req.scope, "k": req.k}


class ObjectiveAddRequest(BaseModel):
    objective: str
    project: str


@app.post("/objective/add")
async def objective_add(req: ObjectiveAddRequest):
    # Dummy implementation
    return {
        "status": "added",
        "objective": req.objective,
        "project": req.project,
    }

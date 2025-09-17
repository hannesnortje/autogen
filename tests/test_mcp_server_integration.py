from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Mock the services to avoid dependency on actual Qdrant and Gemini
with patch("autogen_mcp.mcp_server.memory_service"), patch(
    "autogen_mcp.mcp_server.gemini_client"
):
    from autogen_mcp.mcp_server import app

client = TestClient(app)


def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_workspace_endpoint():
    """Test the workspace info endpoint."""
    response = client.get("/workspace")
    assert response.status_code == 200
    assert "workspace" in response.json()


def test_memory_search_no_gemini():
    """Test memory search when Gemini client is not available."""
    with patch("autogen_mcp.mcp_server.gemini_client", None):
        response = client.post(
            "/memory/search", json={"query": "test query", "scope": "project", "k": 5}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "test query"
        assert data["scope"] == "project"
        assert data["k"] == 5
        assert "results" in data


def test_orchestrate_start_no_gemini():
    """Test orchestration start when Gemini client is not available."""
    with patch("autogen_mcp.mcp_server.gemini_client", None):
        response = client.post(
            "/orchestrate/start",
            json={
                "project": "test-project",
                "agents": ["Coder", "Reviewer"],
                "objective": "Test objective",
            },
        )
        assert response.status_code == 503
        assert "Gemini client not available" in response.json()["detail"]


def test_orchestrate_start_with_gemini():
    """Test orchestration start when Gemini client is available."""
    mock_gemini = MagicMock()
    with patch("autogen_mcp.mcp_server.gemini_client", mock_gemini), patch(
        "autogen_mcp.mcp_server.AgentOrchestrator"
    ) as mock_orchestrator:

        response = client.post(
            "/orchestrate/start",
            json={
                "project": "test-project",
                "agents": ["Coder", "Reviewer"],
                "objective": "Test objective",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "started"
        assert "session_id" in data
        mock_orchestrator.assert_called_once()


def test_orchestrate_stop():
    """Test orchestration stop endpoint."""
    # First start a session
    mock_gemini = MagicMock()
    with patch("autogen_mcp.mcp_server.gemini_client", mock_gemini), patch(
        "autogen_mcp.mcp_server.AgentOrchestrator"
    ):

        start_response = client.post(
            "/orchestrate/start",
            json={"project": "test-project", "agents": ["Coder"], "objective": "Test"},
        )
        session_id = start_response.json()["session_id"]

        # Now stop it
        stop_response = client.post(
            "/orchestrate/stop", json={"session_id": session_id}
        )
        assert stop_response.status_code == 200
        assert stop_response.json()["status"] == "stopped"


def test_orchestrate_stop_nonexistent_session():
    """Test stopping a non-existent session."""
    response = client.post(
        "/orchestrate/stop", json={"session_id": "nonexistent-session"}
    )
    assert response.status_code == 404
    assert "Session not found" in response.json()["detail"]


def test_objective_add():
    """Test adding an objective."""
    with patch("autogen_mcp.mcp_server.memory_service") as mock_memory:
        mock_memory.write_event.return_value = "objective-id-123"

        response = client.post(
            "/objective/add",
            json={
                "objective": "Implement user authentication",
                "project": "test-project",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "added"
        assert data["objective"] == "Implement user authentication"
        assert data["project"] == "test-project"
        assert data["objective_id"] == "objective-id-123"

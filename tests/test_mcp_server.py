from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)
from autogen_mcp.mcp_server import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_workspace():
    resp = client.get("/workspace")
    assert resp.status_code == 200
    assert "workspace" in resp.json()


def test_orchestrate_start():
    data = {"project": "demo", "agents": ["Coder"], "objective": "Test"}
    resp = client.post("/orchestrate/start", json=data)
    assert resp.status_code == 200
    j = resp.json()
    assert j["status"] == "started"
    assert "session_id" in j


def test_orchestrate_stop():
    data = {"session_id": "dummy-session"}
    resp = client.post("/orchestrate/stop", json=data)
    assert resp.status_code == 200
    j = resp.json()
    assert j["status"] == "stopped"
    assert j["session_id"] == "dummy-session"


def test_memory_search():
    data = {"query": "foo", "scope": "project", "k": 3}
    resp = client.post("/memory/search", json=data)
    assert resp.status_code == 200
    j = resp.json()
    assert j["results"] == []
    assert j["query"] == "foo"
    assert j["scope"] == "project"
    assert j["k"] == 3


def test_objective_add():
    data = {"objective": "Test objective", "project": "demo"}
    resp = client.post("/objective/add", json=data)
    assert resp.status_code == 200
    j = resp.json()
    assert j["status"] == "added"
    assert j["objective"] == "Test objective"
    assert j["project"] == "demo"

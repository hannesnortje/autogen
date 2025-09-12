import json
import tempfile
import os
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import patch

# Mock the services to avoid dependency on actual Qdrant and Gemini
with patch("autogen_mcp.mcp_server.memory_service"), patch(
    "autogen_mcp.mcp_server.gemini_client"
):
    from autogen_mcp.mcp_server import app

client = TestClient(app)


def test_write_file_endpoint():
    """Test the file write endpoint."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        with patch.dict(os.environ, {"MCP_WORKSPACE": tmp_dir}):
            response = client.post(
                "/workspace/write",
                json={
                    "file_path": "test/hello.py",
                    "content": "print('Hello, World!')",
                    "project": "test-project",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["file_path"] == "test/hello.py"
            assert data["size"] == len("print('Hello, World!')")

            # Verify file was actually written
            written_file = Path(tmp_dir) / "test" / "hello.py"
            assert written_file.exists()
            assert written_file.read_text() == "print('Hello, World!')"


def test_write_file_creates_directories():
    """Test that file write creates necessary directories."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        with patch.dict(os.environ, {"MCP_WORKSPACE": tmp_dir}):
            response = client.post(
                "/workspace/write",
                json={
                    "file_path": "deep/nested/path/file.txt",
                    "content": "test content",
                    "project": "test-project",
                },
            )

            assert response.status_code == 200

            # Verify nested directories were created
            written_file = Path(tmp_dir) / "deep" / "nested" / "path" / "file.txt"
            assert written_file.exists()
            assert written_file.read_text() == "test content"


def test_list_files_endpoint():
    """Test the file listing endpoint."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create some test files and directories
        test_dir = Path(tmp_dir)
        (test_dir / "file1.txt").write_text("content1")
        (test_dir / "file2.py").write_text("content2")
        (test_dir / "subdir").mkdir()
        (test_dir / "subdir" / "file3.txt").write_text("content3")

        with patch.dict(os.environ, {"MCP_WORKSPACE": tmp_dir}):
            response = client.get("/workspace/files")

            assert response.status_code == 200
            data = response.json()

            assert "files" in data
            assert "directories" in data

            # Check that files are listed
            files = data["files"]
            assert "file1.txt" in files
            assert "file2.py" in files
            assert (
                "subdir/file3.txt" in files or "subdir\\file3.txt" in files
            )  # OS path handling

            # Check that directories are listed
            directories = data["directories"]
            assert "subdir" in directories


def test_list_files_empty_workspace():
    """Test file listing in an empty workspace."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        with patch.dict(os.environ, {"MCP_WORKSPACE": tmp_dir}):
            response = client.get("/workspace/files")

            assert response.status_code == 200
            data = response.json()
            assert data["files"] == []
            assert data["directories"] == []


def test_websocket_connection():
    """Test WebSocket connection and basic messaging."""
    session_id = "test-session-123"

    with client.websocket_connect(f"/ws/session/{session_id}") as websocket:
        # Send a test message
        test_message = {"type": "test", "data": "hello"}
        websocket.send_text(json.dumps(test_message))

        # Receive echo response
        response = websocket.receive_text()
        response_data = json.loads(response)

        assert response_data["type"] == "echo"
        assert response_data["data"] == test_message


def test_websocket_multiple_sessions():
    """Test multiple WebSocket sessions can be handled."""
    session1_id = "session-1"
    session2_id = "session-2"

    with client.websocket_connect(
        f"/ws/session/{session1_id}"
    ) as ws1, client.websocket_connect(f"/ws/session/{session2_id}") as ws2:

        # Send different messages to each session
        ws1.send_text(json.dumps({"session": "1", "message": "hello from 1"}))
        ws2.send_text(json.dumps({"session": "2", "message": "hello from 2"}))

        # Each should receive their own echo
        response1 = json.loads(ws1.receive_text())
        response2 = json.loads(ws2.receive_text())

        assert response1["data"]["session"] == "1"
        assert response2["data"]["session"] == "2"


def test_file_write_logs_to_memory():
    """Test that file writes are logged to memory service."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        with patch("autogen_mcp.mcp_server.memory_service") as mock_memory:
            with patch.dict(os.environ, {"MCP_WORKSPACE": tmp_dir}):
                response = client.post(
                    "/workspace/write",
                    json={
                        "file_path": "test.py",
                        "content": "# Test file",
                        "project": "test-project",
                    },
                )

                assert response.status_code == 200

                # Verify memory service was called
                mock_memory.set_project.assert_called_with("test-project")
                mock_memory.write_event.assert_called_once()

                # Check the call arguments
                call_args = mock_memory.write_event.call_args
                assert call_args[1]["scope"] == "artifact"
                assert "Created file: test.py" in call_args[1]["text"]
                assert call_args[1]["metadata"]["type"] == "file_write"

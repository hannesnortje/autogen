#!/usr/bin/env python3
"""
AutoGen UI Memory Service Initialization
Ensures all required services are started before launching the UI
"""

import os
import sys
import time
import logging
import subprocess
import requests
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Import after path setup to avoid E402
from autogen_mcp.memory_collections import CollectionManager  # noqa: E402
from autogen_mcp.multi_memory import MultiScopeMemoryService  # noqa: E402

logger = logging.getLogger(__name__)


def check_qdrant_status():
    """Check if Qdrant is running and accessible"""
    try:
        response = requests.get("http://localhost:6333/collections", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False


def start_qdrant():
    """Start Qdrant service using Docker"""
    try:
        # Check if Docker is available
        subprocess.run(["docker", "--version"], capture_output=True, check=True)

        print("🚀 Starting Qdrant vector database...")

        # Start Qdrant container
        cmd = [
            "docker",
            "run",
            "-d",
            "--name",
            "autogen-qdrant",
            "-p",
            "6333:6333",
            "-p",
            "6334:6334",
            "-v",
            f"{project_root}/qdrant_data:/qdrant/storage",
            "qdrant/qdrant:latest",
        ]

        # Remove existing container if present
        subprocess.run(["docker", "rm", "-f", "autogen-qdrant"], capture_output=True)

        subprocess.run(cmd, check=True)

        # Wait for Qdrant to be ready
        print("⏳ Waiting for Qdrant to initialize...")
        for i in range(30):
            if check_qdrant_status():
                print("✅ Qdrant is ready!")
                return True
            time.sleep(1)

        print("❌ Qdrant failed to start within 30 seconds")
        return False

    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"❌ Failed to start Qdrant: {e}")
        print("💡 Please ensure Docker is installed and running")
        return False


def initialize_memory_service():
    """Initialize the memory service with collections"""
    try:
        print("🧠 Initializing memory service...")

        # Initialize collection manager
        collection_manager = CollectionManager()

        # Initialize memory service
        memory_service = MultiScopeMemoryService(collection_manager)

        # Initialize collections (without seeding to avoid errors)
        collection_manager.initialize_all_collections()
        memory_service._initialized = True

        print("✅ Memory service initialized successfully!")
        return True

    except Exception as e:
        print(f"❌ Memory service initialization failed: {e}")
        return False


def start_mcp_server():
    """Start the MCP server"""
    try:
        print("🌐 Starting MCP server...")

        # Change to project directory
        os.chdir(project_root)

        # Start server in background
        env = os.environ.copy()
        env["PYTHONPATH"] = str(project_root / "src")

        cmd = ["python", "-m", "autogen_mcp.mcp_server"]

        process = subprocess.Popen(
            cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )

        # Wait a moment for server to start
        time.sleep(3)

        # Check if server is running
        try:
            response = requests.get("http://localhost:9000/health", timeout=5)
            if response.status_code == 200:
                print("✅ MCP server is running!")
                print(f"Server PID: {process.pid}")
                return True
            else:
                status_code = response.status_code
                print(f"❌ MCP server health check failed: {status_code}")
                return False
        except requests.RequestException as e:
            print(f"❌ MCP server is not responding: {e}")
            return False

    except Exception as e:
        print(f"❌ Failed to start MCP server: {e}")
        return False


def main():
    """Main initialization sequence"""
    print("🔧 AutoGen UI Memory Service Initialization")
    print("=" * 50)

    # Step 1: Check/Start Qdrant
    if not check_qdrant_status():
        print("📡 Qdrant not found, attempting to start...")
        if not start_qdrant():
            print("\n⚠️  Qdrant could not be started.")
            print("The UI will work in limited mode without vector search.")
            print("To enable full functionality, start Qdrant manually:")
            cmd = "docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant:latest"
            print(cmd)
        else:
            print("✅ Qdrant is already running")

        # Step 2: Initialize Memory Service
        if not initialize_memory_service():
            print("⚠️  Memory service initialization failed")
            print("Some features may not work properly")

        # Step 3: Start MCP Server
        if not start_mcp_server():
            print("⚠️  MCP server could not be started")
            print("UI will work in local mode only")

        print("\n🎉 Initialization complete!")
        print("You can now launch the UI with: python src/autogen_ui/main.py")

        return True


if __name__ == "__main__":
    main()

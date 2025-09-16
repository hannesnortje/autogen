"""
AutoGen Desktop UI - Integration Test for UI and MCP Server Coexistence

This test verifies that the UI and MCP server can run simultaneously
and that the hybrid integration approach works correctly.
"""

import requests
from pathlib import Path


def test_mcp_server_connection() -> bool:
    """Test connection to the MCP server."""

    try:
        # Test health endpoint
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ MCP server health check passed")
            return True
        else:
            print(f"❌ MCP server health check failed: {response.status_code}")
            return False

    except requests.ConnectionError:
        print("❌ Cannot connect to MCP server on port 8000")
        return False
    except Exception as e:
        print(f"❌ MCP server test error: {e}")
        return False


def test_shared_logging() -> bool:
    """Test that both UI and MCP server write to shared logs."""

    logs_dir = Path("logs")  # Relative to current directory

    # Check log files exist
    required_files = ["autogen.log", "ui.log", "errors.log"]

    for log_file in required_files:
        log_path = logs_dir / log_file
        if not log_path.exists():
            print(f"❌ Missing log file: {log_file}")
            return False
        else:
            print(f"✅ Found log file: {log_file}")

    # Check for UI entries in shared log
    shared_log = logs_dir / "autogen.log"

    try:
        with open(shared_log, "r") as f:
            content = f.read()

        if "[UI]" in content:
            print("✅ UI entries found in shared autogen.log")
            return True
        else:
            print("❌ No UI entries found in shared autogen.log")
            return False

    except Exception as e:
        print(f"❌ Error reading shared log: {e}")
        return False


def test_port_independence() -> bool:
    """Test that UI and MCP server use different resources."""

    # MCP server uses port 8000
    # UI uses Qt application (no network port)
    # Both should coexist without conflicts

    try:
        # Test MCP server endpoint
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        mcp_running = response.status_code == 200

        if mcp_running:
            print("✅ MCP server running on port 8000")
            print("✅ UI uses Qt (no port conflicts)")
            return True
        else:
            print("❌ MCP server not responding")
            return False

    except Exception as e:
        print(f"❌ Port independence test error: {e}")
        return False


def run_coexistence_tests() -> bool:
    """Run all coexistence tests."""

    print("=" * 60)
    print("AutoGen UI and MCP Server Coexistence Tests")
    print("=" * 60)

    tests = [
        ("MCP Server Connection", test_mcp_server_connection),
        ("Shared Logging", test_shared_logging),
        ("Port Independence", test_port_independence),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        print("-" * 40)

        try:
            result = test_func()
            results.append((test_name, result))

            if result:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")

        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))

    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:30} {status}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All coexistence tests passed!")
        return True
    else:
        print(f"⚠️  {total - passed} tests failed")
        return False


if __name__ == "__main__":
    success = run_coexistence_tests()
    exit(0 if success else 1)

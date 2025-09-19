#!/usr/bin/env python3
"""
Quick test script to verify MCP server Gemini integration
"""

import requests


def test_mcp_server():
    url = "http://127.0.0.1:9000/conversation/send"
    data = {
        "session_id": "Smart Task Manager API",
        "content": "Hello ScrumMaster, can you help facilitate our Sprint Planning?",
        "target_agents": ["ScrumMaster"],
        "message_type": "user",
    }

    try:
        print("Testing MCP server...")
        response = requests.post(url, json=data, timeout=15)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}...")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    test_mcp_server()

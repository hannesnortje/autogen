import os
import pytest
from autogen_mcp.gemini_client import GeminiClient
from dotenv import load_dotenv


def test_gemini_connectivity():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("GEMINI_API_KEY not set in environment")
    client = GeminiClient(api_key=api_key)
    prompt = "Say hello in one short sentence."
    response = client.complete(prompt)
    assert isinstance(response, str)
    assert len(response.strip()) > 0
    assert "hello" in response.lower() or "hi" in response.lower()

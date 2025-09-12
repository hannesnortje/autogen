"""
Gemini LLM client for AutoGen MCP integration.
Loads API key from environment and provides a simple completion interface.
"""

import os
import requests
from typing import Optional

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"


class GeminiClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY not set in environment or provided.")

    def complete(self, prompt: str, **kwargs) -> str:
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key,
        }
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
        }
        data.update(kwargs)
        resp = requests.post(GEMINI_API_URL, headers=headers, json=data, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        # Extract the text from the response
        try:
            return result["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            raise RuntimeError(f"Unexpected Gemini response: {result}")

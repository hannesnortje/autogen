from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests

DEFAULT_QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
DEFAULT_QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")


@dataclass
class QdrantConfig:
    url: str = DEFAULT_QDRANT_URL
    api_key: Optional[str] = DEFAULT_QDRANT_API_KEY


class QdrantWrapper:
    """Minimal HTTP wrapper for Qdrant until we add the official client.

    Provides: health, list_collections, create_collection (schema-lite).
    """

    def __init__(self, config: Optional[QdrantConfig] = None) -> None:
        self.config = config or QdrantConfig()
        self.session = requests.Session()
        if self.config.api_key:
            self.session.headers.update({"api-key": self.config.api_key})

    def _url(self, path: str) -> str:
        return f"{self.config.url.rstrip('/')}{path}"

    def health(self) -> bool:
        try:
            resp = self.session.get(self._url("/readyz"), timeout=3)
            return resp.status_code == 200
        except Exception:
            return False

    def list_collections(self) -> List[str]:
        resp = self.session.get(self._url("/collections"), timeout=5)
        resp.raise_for_status()
        data = resp.json()
        collections = data.get("result", {}).get("collections", [])
        return [c["name"] for c in collections]

    def create_collection(
        self,
        name: str,
        vector_size: int = 384,
        distance: str = "Cosine",
    ) -> Dict[str, Any]:
        payload = {
            "vectors": {"size": vector_size, "distance": distance},
            # We'll extend this with payload_schema per-scope in later steps
        }
        resp = self.session.put(
            self._url(f"/collections/{name}"),
            json=payload,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def upsert_point(
        self,
        collection: str,
        point_id: str,
        vector: List[float],
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        body = {
            "points": [
                {
                    "id": point_id,
                    "vector": vector,
                    "payload": payload,
                }
            ]
        }
        resp = self.session.put(
            self._url(f"/collections/{collection}/points"),
            params={"wait": "true"},
            json=body,
            timeout=10,
        )
        try:
            resp.raise_for_status()
        except requests.HTTPError as e:
            # Include server message for easier debugging
            raise requests.HTTPError(f"{e}: {resp.text}") from e
        return resp.json()

    def search(
        self,
        collection: str,
        vector: List[float],
        limit: int = 5,
    ) -> Dict[str, Any]:
        body = {"vector": vector, "limit": limit}
        resp = self.session.post(
            self._url(f"/collections/{collection}/points/search"),
            json=body,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

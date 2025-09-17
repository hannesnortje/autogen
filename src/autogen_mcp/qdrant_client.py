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
        from autogen_mcp.security import is_url_allowed

        url = f"{self.config.url.rstrip('/')}{path}"
        if not is_url_allowed(url):
            raise RuntimeError(f"Outbound call to disallowed domain: {url}")
        return url

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

    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get information about a specific collection."""
        resp = self.session.get(self._url(f"/collections/{collection_name}"), timeout=5)
        resp.raise_for_status()
        data = resp.json()
        return data.get("result", {})

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

    def scroll(
        self,
        collection: str,
        must: Optional[List[Dict[str, Any]]] = None,
        limit: int = 100,
        with_payload: bool = True,
        with_vector: bool = False,
    ) -> Dict[str, Any]:
        body: Dict[str, Any] = {
            "limit": limit,
            "with_payload": with_payload,
            "with_vector": with_vector,
        }
        if must:
            body["filter"] = {"must": must}
        resp = self.session.post(
            self._url(f"/collections/{collection}/points/scroll"),
            json=body,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def retrieve_point(
        self,
        collection: str,
        point_id: str,
        with_payload: bool = True,
        with_vector: bool = False,
    ) -> Dict[str, Any]:
        """Retrieve a specific point by ID."""
        params = {}
        if with_payload:
            params["with_payload"] = "true"
        if with_vector:
            params["with_vectors"] = "true"

        resp = self.session.get(
            self._url(f"/collections/{collection}/points/{point_id}"),
            params=params,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def delete_point(
        self,
        collection: str,
        point_id: str,
    ) -> Dict[str, Any]:
        """Delete a specific point by ID."""
        resp = self.session.delete(
            self._url(f"/collections/{collection}/points/{point_id}"),
            params={"wait": "true"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def delete_points(
        self,
        collection: str,
        point_ids: List[str],
    ) -> Dict[str, Any]:
        """Delete multiple points by IDs."""
        body = {"points": point_ids}
        resp = self.session.post(
            self._url(f"/collections/{collection}/points/delete"),
            json=body,
            params={"wait": "true"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def delete_collection(self, collection_name: str) -> Dict[str, Any]:
        """Delete entire collection."""
        resp = self.session.delete(
            self._url(f"/collections/{collection_name}"),
            params={"timeout": "60"},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()

    def delete_points_by_filter(
        self,
        collection: str,
        filter_conditions: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Delete points matching filter conditions."""
        body = {
            "filter": filter_conditions,
            "wait": True,
        }
        resp = self.session.post(
            self._url(f"/collections/{collection}/points/delete"),
            json=body,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

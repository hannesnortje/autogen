from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Sequence

from autogen_mcp.embeddings import EmbeddingService
from autogen_mcp.qdrant_client import QdrantWrapper
from autogen_mcp.hybrid_search import SparseRetriever


@dataclass
class HybridConfig:
    top_k_dense: int = 5
    top_k_sparse: int = 5
    fuse_k: int = 5


class HybridSearchService:
    TIER_ORDER = ["thread", "project", "objective", "agent", "global"]

    def __init__(self, config: HybridConfig | None = None) -> None:
        self.config = config or HybridConfig()
        self.embed = EmbeddingService()
        self.qdrant = QdrantWrapper()
        self._sparse: SparseRetriever | None = None
        self._doc_ids: List[Any] = []

    def build_sparse(self, docs: Sequence[str], doc_ids: Sequence[Any]) -> None:
        self._sparse = SparseRetriever(list(docs), list(doc_ids))
        self._doc_ids = list(doc_ids)

    def index_dense(
        self, collection: str, ids: Sequence[Any], texts: Sequence[str]
    ) -> None:
        for pid, text in zip(ids, texts):
            vec = self.embed.encode_one(text)
            self.qdrant.upsert_point(
                collection,
                point_id=pid,
                vector=vec,
                payload={"text": text},
            )

    def _dense_search(
        self, collection: str, query: str, k: int, scope: str
    ) -> List[dict]:
        vec = self.embed.encode_one(query)
        # Filter by scope in Qdrant - IMPORTANT: with_vector=True to get vectors
        must = [{"key": "scope", "match": {"value": scope}}]
        res = self.qdrant.scroll(
            collection, must=must, limit=1000, with_payload=True, with_vector=True
        )
        points = res.get("result", {}).get("points", [])
        # If no points, return empty
        if not points:
            return []
        # Compute dense scores
        import numpy as np

        scored = []
        for p in points:
            v = p.get("vector")
            if v is None:
                continue
            score = float(
                np.dot(vec, v) / (np.linalg.norm(vec) * np.linalg.norm(v) + 1e-8)
            )
            scored.append(
                {
                    "id": p.get("id"),
                    "score": score,
                    "scope": scope,
                    "metadata": p.get("payload", {}),
                }
            )
        scored.sort(key=lambda x: -x["score"])
        return scored[:k]

    def _sparse_search(self, query: str, k: int, scope: str) -> List[dict]:
        if not self._sparse:
            return []
        # Only include docs with matching scope in metadata if available
        results = self._sparse.search(query, top_k=100)
        filtered = [
            {"id": rid, "score": score, "scope": scope, "metadata": {}}
            for rid, score in results
        ]
        filtered.sort(key=lambda x: -x["score"])
        return filtered[:k]

    def search(
        self, collection: str, query: str, k: int = 5, scopes: list[str] | None = None
    ) -> List[dict]:
        scopes = scopes or self.TIER_ORDER
        results = []
        for scope in scopes:
            dense = self._dense_search(
                collection, query, self.config.top_k_dense, scope
            )
            sparse = self._sparse_search(query, self.config.top_k_sparse, scope)
            # Fuse by id, sum scores if present in both
            by_id = {}
            for r in dense + sparse:
                if r["id"] not in by_id:
                    by_id[r["id"]] = r
                else:
                    by_id[r["id"]]["score"] += r["score"]
            tier_results = list(by_id.values())
            tier_results.sort(key=lambda x: -x["score"])
            results.extend(tier_results)
            if len(results) >= k:
                break
        # Return top-k with scores and scope/metadata
        return results[:k]

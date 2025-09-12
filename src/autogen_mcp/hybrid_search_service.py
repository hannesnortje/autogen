from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Sequence

from autogen_mcp.embeddings import EmbeddingService
from autogen_mcp.qdrant_client import QdrantWrapper
from autogen_mcp.hybrid_search import SparseRetriever, reciprocal_rank_fusion


@dataclass
class HybridConfig:
    top_k_dense: int = 5
    top_k_sparse: int = 5
    fuse_k: int = 5


class HybridSearchService:
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
        # Assumes collection exists with correct vector size
        for pid, text in zip(ids, texts):
            vec = self.embed.encode_one(text)
            self.qdrant.upsert_point(
                collection,
                point_id=pid,
                vector=vec,
                payload={"text": text},
            )

    def _dense_search_ids(self, collection: str, query: str, k: int) -> List[Any]:
        vec = self.embed.encode_one(query)
        res = self.qdrant.search(collection, vec, limit=k)
        hits = res.get("result", [])
        return [h.get("id") for h in hits]

    def _sparse_search_ids(self, query: str, k: int) -> List[Any]:
        if not self._sparse:
            return []
        results = self._sparse.search(query, top_k=k)
        return [rid for rid, _ in results]

    def search(self, collection: str, query: str, k: int = 5) -> List[Any]:
        dense_ids = self._dense_search_ids(collection, query, self.config.top_k_dense)
        sparse_ids = self._sparse_search_ids(query, self.config.top_k_sparse)
        fused = reciprocal_rank_fusion(dense_ids, sparse_ids, k=self.config.fuse_k)
        return fused[:k]

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np


def reciprocal_rank_fusion(*ranked_lists: List[List[Any]], k: int = 60) -> List[Any]:
    """Reciprocal Rank Fusion (RRF) for combining ranked lists."""
    scores: Dict[Any, float] = {}
    for ranked in ranked_lists:
        for rank, item in enumerate(ranked):
            scores[item] = scores.get(item, 0.0) + 1.0 / (60 + rank)
    sorted_items = sorted(scores.items(), key=lambda x: -x[1])
    return [item for item, _ in sorted_items][:k]


class SparseRetriever:
    def __init__(self, docs: List[str], doc_ids: List[Any]) -> None:
        self.vectorizer = TfidfVectorizer()
        self.doc_ids = doc_ids
        if not docs:
            self.tfidf = None
        else:
            self.tfidf = self.vectorizer.fit_transform(docs)

    def search(self, query: str, top_k: int = 5) -> List[Tuple[Any, float]]:
        if self.tfidf is None or self.tfidf.shape[0] == 0:
            return []
        q_vec = self.vectorizer.transform([query])
        scores = (self.tfidf @ q_vec.T).toarray().ravel()
        top_idx = np.argsort(scores)[::-1][:top_k]
        return [(self.doc_ids[i], float(scores[i])) for i in top_idx if scores[i] > 0]

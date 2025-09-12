from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from fastembed import TextEmbedding  # type: ignore[import]


@dataclass
class EmbeddingConfig:
    model: str = "sentence-transformers/all-MiniLM-L6-v2"


class EmbeddingService:
    def __init__(self, config: EmbeddingConfig | None = None) -> None:
        self.config = config or EmbeddingConfig()
        self._model = TextEmbedding(self.config.model)

    def encode_one(self, text: str) -> List[float]:
        # Convert numpy array to plain list for Qdrant JSON compatibility
        vec = next(self._model.embed([text]))
        return [float(x) for x in vec]

    def encode_many(self, texts: Iterable[str]) -> List[List[float]]:
        return [[float(x) for x in v] for v in self._model.embed(texts)]

    def dim(self) -> int:
        # Obtain embedding size by encoding a tiny string once
        return len(self.encode_one("x"))

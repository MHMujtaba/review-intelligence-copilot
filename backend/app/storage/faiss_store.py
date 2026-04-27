import json
from pathlib import Path

import numpy as np

from app.schemas.contracts import IndexedReview, RetrievedReview

try:
    import faiss
except ImportError:  # pragma: no cover
    faiss = None


class FaissVectorStore:
    def __init__(self, persist_dir: Path) -> None:
        self.persist_dir = persist_dir
        self.index_path = persist_dir / "review_embeddings.index"
        self.vectors_path = persist_dir / "review_embeddings.npy"
        self.metadata_path = persist_dir / "review_metadata.json"
        self.index = None
        self.metadata: list[IndexedReview] = []
        self.vectors = np.empty((0, 0), dtype=np.float32)
        self.load()

    def rebuild(self, vectors: np.ndarray, metadata: list[IndexedReview]) -> None:
        self.metadata = metadata
        self.vectors = self._normalize(vectors.astype(np.float32))
        if faiss is not None and len(self.vectors):
            dimension = self.vectors.shape[1]
            self.index = faiss.IndexFlatIP(dimension)
            self.index.add(self.vectors)
        else:
            self.index = None
        self.save()

    def search(self, query_vector: np.ndarray, top_k: int, asin: str | None = None) -> list[RetrievedReview]:
        if not len(self.metadata):
            return []
        if self.index is None and self.vectors.size == 0:
            return []

        query = self._normalize(query_vector.reshape(1, -1).astype(np.float32))
        search_width = min(max(top_k * 4, top_k), len(self.metadata))
        if faiss is not None and self.index is not None:
            scores, indices = self.index.search(query, search_width)
            pairs = [(int(index), float(score)) for score, index in zip(scores[0], indices[0]) if index >= 0]
        else:
            similarities = np.dot(self.vectors, query[0])
            indices = np.argsort(similarities)[::-1][:search_width]
            pairs = [(int(index), float(similarities[index])) for index in indices]

        results: list[RetrievedReview] = []
        for index, score in pairs:
            review = self.metadata[index]
            if asin and review.asin != asin:
                continue
            results.append(RetrievedReview(**review.model_dump(), semantic_score=score))
            if len(results) >= top_k:
                break
        return results

    def save(self) -> None:
        payload = [item.model_dump(mode="json") for item in self.metadata]
        self.metadata_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        if self.vectors.size:
            np.save(self.vectors_path, self.vectors)
        if faiss is not None and self.index is not None:
            faiss.write_index(self.index, str(self.index_path))

    def load(self) -> None:
        if not self.metadata_path.exists():
            return
        payload = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        self.metadata = [IndexedReview.model_validate(item) for item in payload]
        if self.vectors_path.exists():
            self.vectors = np.load(self.vectors_path)
        if faiss is not None and self.index_path.exists():
            self.index = faiss.read_index(str(self.index_path))
        elif self.vectors.size:
            self.index = None

    @staticmethod
    def _normalize(vectors: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1
        return vectors / norms

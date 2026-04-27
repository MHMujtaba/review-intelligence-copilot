from app.core.config import get_settings
from app.embeddings.service import EmbeddingService
from app.filtering.service import FilteringService
from app.reranking.service import RerankingService
from app.retrieval.query_understanding import classify_query
from app.schemas.contracts import RetrievedReview
from app.storage.faiss_store import FaissVectorStore


class ReviewRetriever:
    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: FaissVectorStore,
        reranker: RerankingService,
        filter_service: FilteringService,
    ) -> None:
        self.settings = get_settings()
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.reranker = reranker
        self.filter_service = filter_service
        self._cache: dict[tuple[str, str | None, int], tuple[str, list[RetrievedReview]]] = {}

    async def retrieve(self, query: str, asin: str | None = None, top_k: int = 8) -> tuple[str, list[RetrievedReview]]:
        bounded_top_k = min(top_k, 50)
        cache_key = (query.strip().lower(), asin, bounded_top_k)
        if cache_key in self._cache:
            return self._cache[cache_key]

        query_type = classify_query(query).label
        query_embedding = await self.embedding_service.embed_query(query)
        candidates = self.vector_store.search(
            query_embedding,
            top_k=min(self.settings.retrieval_candidate_k, 50),
            asin=asin,
        )
        reranked = self.reranker.rerank(candidates, query_type=query_type, top_k=bounded_top_k)
        filtered = self.filter_service.apply(reranked)
        result = (query_type, filtered[:bounded_top_k])

        if len(self._cache) > 128:
            oldest_key = next(iter(self._cache))
            self._cache.pop(oldest_key, None)
        self._cache[cache_key] = result
        return result

    def clear_cache(self) -> None:
        self._cache.clear()

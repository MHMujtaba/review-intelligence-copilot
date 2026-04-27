import json
from pathlib import Path

from app.core.config import get_settings
from app.csv_loader.service import CsvLoaderService
from app.embeddings.service import EmbeddingService
from app.filtering.service import FilteringService
from app.generation.service import GenerationService
from app.ml.classifier import ReviewQualityClassifier
from app.preprocessing.service import PreprocessingService
from app.retrieval.hybrid import ReviewRetriever
from app.reranking.service import RerankingService
from app.schemas.contracts import (
    AskRequest,
    AskResponse,
    EmbedRequest,
    EmbedResponse,
    IndexedReview,
    LoadCsvRequest,
    LoadCsvResponse,
    ProcessedReview,
    ProductInsightsResponse,
    ProductSummaryResponse,
    SearchRequest,
    SearchResponse,
)
from app.storage.faiss_store import FaissVectorStore
from app.utils.text import extract_review_themes


class ApplicationServices:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.csv_loader = CsvLoaderService()
        self.preprocessing = PreprocessingService()
        self.embedding_service = EmbeddingService()
        self.quality_classifier = ReviewQualityClassifier()
        self.vector_store = FaissVectorStore(self.settings.vector_store_dir)
        self.filtering = FilteringService(quality_classifier=self.quality_classifier)
        self.reranker = RerankingService()
        self.retriever = ReviewRetriever(
            embedding_service=self.embedding_service,
            vector_store=self.vector_store,
            reranker=self.reranker,
            filter_service=self.filtering,
        )
        self.generator = GenerationService()
        self.reviews: list[ProcessedReview] = []
        self.last_loaded_csv: str | None = None

    async def initialize(self) -> None:
        self._load_cached_reviews()

    async def load_csv(self, request: LoadCsvRequest) -> LoadCsvResponse:
        raw_records = self.csv_loader.load(request.file_path, chunksize=request.chunksize)
        self.reviews = self.preprocessing.process_records(raw_records)
        self.last_loaded_csv = request.file_path
        self._save_cached_reviews()
        self.retriever.clear_cache()
        return LoadCsvResponse(
            loaded_reviews=len(self.reviews),
            unique_asins=len({review.asin for review in self.reviews}),
            file_path=request.file_path,
        )

    async def embed_reviews(self, request: EmbedRequest) -> EmbedResponse:
        reviews = self._select_reviews(request.asin)
        self.quality_classifier.train(reviews)
        metadata = [self._to_indexed_review(review) for review in reviews]
        if not metadata:
            return EmbedResponse(embedded_reviews=0, indexed_asins=0)

        vectors = await self._embed_in_batches([review.review_text for review in metadata], request.batch_size)
        if request.asin and self.vector_store.metadata:
            retained = [item for item in self.vector_store.metadata if item.asin != request.asin]
            retained_vectors = self._retained_vectors(request.asin)
            import numpy as np

            metadata = retained + metadata
            vectors = np.vstack([retained_vectors, vectors]) if retained_vectors.size else vectors

        self.vector_store.rebuild(vectors, metadata)
        self.retriever.clear_cache()
        return EmbedResponse(
            embedded_reviews=len([review for review in metadata if not request.asin or review.asin == request.asin]),
            indexed_asins=len({review.asin for review in metadata}),
        )

    async def search(self, request: SearchRequest) -> SearchResponse:
        query_type, results = await self.retriever.retrieve(request.query, asin=request.asin, top_k=request.top_k)
        return SearchResponse(query_type=query_type, results=results)
    """
    async def ask(self, request: AskRequest) -> AskResponse:
        query_type, evidence = await self.retriever.retrieve(
            request.query,
            asin=request.asin,
            top_k=request.max_results,
        )
        answer, context = await self.generator.answer(request.query, query_type, evidence)
        return AskResponse(query_type=query_type, answer=answer, context=context, evidence=evidence)

    async def get_summary(self, asin: str) -> ProductSummaryResponse:
        query = "Provide an overall summary of customer reviews, main pros, main cons, and sentiment."
        query_type, evidence = await self.retriever.retrieve(query, asin=asin, top_k=8)
        answer, context = await self.generator.answer(query, query_type, evidence)
        return ProductSummaryResponse(asin=asin, summary=answer, context=context)
    """

    # async def ask(self, request: AskRequest) -> AskResponse:
    #     query_type, evidence = await self.retriever.retrieve(
    #         request.query,
    #         asin=request.asin,
    #         top_k=request.max_results,
    #     )
    #     answer, context = await self.generator.answer(
    #         request.query, query_type, evidence, mode="ask"  # <-- direct Q&A
    #     )
    #     return AskResponse(query_type=query_type, answer=answer, context=context, evidence=evidence)
    async def ask(self, request: AskRequest) -> AskResponse:
        query_type, evidence = await self.retriever.retrieve(
            request.query,
            asin=request.asin,
            top_k=request.max_results,
        )
        answer, context, response_id = await self.generator.answer(
            request.query,
            query_type,
            evidence,
            mode="ask",
            previous_response_id=request.previous_response_id,  # <-- passed in from client
        )
        return AskResponse(
            query_type=query_type,
            answer=answer,
            context=context,
            evidence=evidence,
            previous_response_id=response_id,  # <-- returned to client
        )
    async def get_summary(self, asin: str) -> ProductSummaryResponse:
        query = "Provide an overall summary of customer reviews, main pros, main cons, and sentiment."
        query_type, evidence = await self.retriever.retrieve(query, asin=asin, top_k=8)
        answer, context,_ = await self.generator.answer(
            query, query_type, evidence, mode="summary"  # <-- structured summary
        )
        return ProductSummaryResponse(asin=asin, summary=answer, context=context)

    async def get_insights(self, asin: str) -> ProductInsightsResponse:
        reviews = self._select_reviews(asin)
        positive_reviews = [review for review in reviews if review.overall >= 4.0]
        negative_reviews = [review for review in reviews if review.overall <= 2.0]
        representative = sorted(
            reviews,
            key=lambda item: (item.helpfulness_ratio, item.overall, item.review_length),
            reverse=True,
        )[:4]

        avg_helpfulness = round(
            sum(review.helpfulness_ratio for review in reviews) / max(len(reviews), 1),
            4,
        )
        avg_rating = round(sum(review.overall for review in reviews) / max(len(reviews), 1), 2)
        sentiment_summary = {
            "average_rating": avg_rating,
            "average_sentiment_score": round(
                sum(review.sentiment_score for review in reviews) / max(len(reviews), 1),
                4,
            ),
            "positive_review_count": len(positive_reviews),
            "negative_review_count": len(negative_reviews),
            "review_count": len(reviews),
        }
        helpfulness_summary = {
            "average_helpfulness_ratio": avg_helpfulness,
            "high_helpfulness_reviews": sum(1 for review in reviews if review.helpfulness_ratio >= 0.5),
            "low_helpfulness_reviews": sum(1 for review in reviews if review.helpfulness_ratio < self.settings.min_helpfulness_ratio),
        }
        return ProductInsightsResponse(
            asin=asin,
            sentiment_summary=sentiment_summary,
            helpfulness_summary=helpfulness_summary,
            top_positive_themes=extract_review_themes(positive_reviews, polarity="positive", limit=5),
            top_negative_themes=extract_review_themes(negative_reviews, polarity="negative", limit=5),
            representative_reviews=[
                {
                    "review_id": review.review_id,
                    "summary": review.summary,
                    "overall": review.overall,
                    "helpfulness_ratio": round(review.helpfulness_ratio, 3),
                    "review_text": review.review_text[:220],
                }
                for review in representative
            ],
        )

    def _select_reviews(self, asin: str | None = None) -> list[ProcessedReview]:
        if asin:
            return [review for review in self.reviews if review.asin == asin]
        return list(self.reviews)

    def _to_indexed_review(self, review: ProcessedReview) -> IndexedReview:
        return IndexedReview(
            review_id=review.review_id,
            asin=review.asin,
            overall=review.overall,
            helpfulness_ratio=review.helpfulness_ratio,
            unix_review_time=review.unix_review_time,
            review_datetime=review.review_datetime,
            summary=review.summary,
            review_text=review.review_text,
            reviewer_id=review.reviewer_id,
            reviewer_name=review.reviewer_name,
            review_length=review.review_length,
            sentiment_score=review.sentiment_score,
            metadata={
                "asin": review.asin,
                "overall": review.overall,
                "helpfulness_ratio": review.helpfulness_ratio,
                "unixReviewTime": review.unix_review_time,
            },
        )

    async def _embed_in_batches(self, texts: list[str], batch_size: int):
        batches = []
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            batches.append(await self.embedding_service.embed_texts(batch))
        import numpy as np

        return np.vstack(batches)

    def _retained_vectors(self, asin: str):
        import numpy as np

        if self.vector_store.vectors.size == 0:
            return np.empty((0, 0), dtype=np.float32)
        indices = [index for index, review in enumerate(self.vector_store.metadata) if review.asin != asin]
        if not indices:
            return np.empty((0, self.vector_store.vectors.shape[1]), dtype=np.float32)
        return self.vector_store.vectors[indices]

    def _save_cached_reviews(self) -> None:
        payload = {
            "last_loaded_csv": self.last_loaded_csv,
            "reviews": [review.model_dump(mode="json") for review in self.reviews],
        }
        self.settings.cache_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _load_cached_reviews(self) -> None:
        cache_path = Path(self.settings.cache_file)
        if not cache_path.exists():
            return
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
        self.last_loaded_csv = payload.get("last_loaded_csv")
        self.reviews = [ProcessedReview.model_validate(item) for item in payload.get("reviews", [])]

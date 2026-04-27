from app.schemas.contracts import RetrievedReview


class RerankingService:
    def rerank(self, reviews: list[RetrievedReview], query_type: str, top_k: int = 8) -> list[RetrievedReview]:
        if not reviews:
            return []

        semantic_max = max((review.semantic_score for review in reviews), default=1.0) or 1.0
        reranked: list[RetrievedReview] = []

        for review in reviews:
            semantic_similarity = review.semantic_score / semantic_max
            helpfulness_ratio = min(review.helpfulness_ratio, 1.0)
            rating_signal = self._rating_signal(review.overall, query_type)
            final_score = (
                (0.5 * semantic_similarity)
                + (0.3 * helpfulness_ratio)
                + (0.2 * rating_signal)
            )
            reranked.append(review.model_copy(update={"final_score": round(final_score, 4)}))

        reranked.sort(key=lambda item: item.final_score, reverse=True)
        return reranked[:top_k]

    def _rating_signal(self, overall: float, query_type: str) -> float:
        if query_type == "complaint_query":
            return 1.0 if overall <= 2.0 else max(0.0, (5.0 - overall) / 4.0)
        if query_type == "positive_query":
            return 1.0 if overall >= 4.0 else max(0.0, (overall - 1.0) / 4.0)
        if query_type == "summary_query":
            return 1 - abs(overall - 3.0) / 2.0
        return 0.6

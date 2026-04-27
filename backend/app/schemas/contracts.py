from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class CsvReviewRecord(BaseModel):
    asin: str
    helpful: str | list[int] | tuple[int, int]
    overall: float = Field(ge=1.0, le=5.0)
    reviewText: str
    reviewTime: str | None = None
    unixReviewTime: float
    reviewerID: str
    reviewerName: str | None = None
    summary: str | None = None


class ProcessedReview(BaseModel):
    review_id: str
    asin: str
    reviewer_id: str
    reviewer_name: str
    overall: float
    summary: str
    review_text: str
    review_time: str
    unix_review_time: float
    review_datetime: datetime
    helpful_votes: int
    total_votes: int
    helpfulness_ratio: float
    clean_text: str
    review_length: int
    sentiment_score: float


class IndexedReview(BaseModel):
    review_id: str
    asin: str
    overall: float
    helpfulness_ratio: float
    unix_review_time: float
    review_datetime: datetime
    summary: str
    review_text: str
    reviewer_id: str
    reviewer_name: str
    review_length: int
    sentiment_score: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievedReview(IndexedReview):
    semantic_score: float = 0.0
    final_score: float = 0.0


class LoadCsvRequest(BaseModel):
    file_path: str
    chunksize: int | None = Field(default=None, ge=100)


class LoadCsvResponse(BaseModel):
    loaded_reviews: int
    unique_asins: int
    file_path: str


class EmbedRequest(BaseModel):
    asin: str | None = None
    batch_size: int = Field(default=64, ge=1, le=512)
    rebuild_index: bool = True


class EmbedResponse(BaseModel):
    embedded_reviews: int
    indexed_asins: int


class SearchRequest(BaseModel):
    query: str
    asin: str | None = None
    top_k: int = Field(default=10, ge=1, le=50)


class SearchResponse(BaseModel):
    query_type: str
    results: list[RetrievedReview]


class AskRequest(BaseModel):
    query: str
    asin: str | None = None
    max_results: int = Field(default=8, ge=3, le=12)
    previous_response_id: str | None = None  # <-- client sends this on follow-ups


class AskResponse(BaseModel):
    query_type: str
    answer: str
    context: dict[str, Any]
    evidence: list[RetrievedReview]
    previous_response_id: str | None = None  # <-- client stores and re-sends this

class ProductSummaryResponse(BaseModel):
    asin: str
    summary: str
    context: dict[str, Any]


class ProductInsightsResponse(BaseModel):
    asin: str
    sentiment_summary: dict[str, Any]
    helpfulness_summary: dict[str, Any]
    top_positive_themes: list[str]
    top_negative_themes: list[str]
    representative_reviews: list[dict[str, Any]]


class QueryType(BaseModel):
    label: Literal["complaint_query", "positive_query", "summary_query", "general_query"]
    confidence: float


class ReviewSearchHit(BaseModel):
    helpful_votes: int
    helpfulness_ratio: float
    review_id: str
    asin: str
    overall: float
    unix_review_time: float
    review_datetime: datetime
    summary: str
    review_text: str
    review_length: int
    sentiment_score: float
    semantic_score: float

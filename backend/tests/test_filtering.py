from datetime import UTC, datetime

from app.filtering.service import FilteringService
from app.schemas.contracts import RetrievedReview


def build_review(**updates) -> RetrievedReview:
    payload = {
        "review_id": "review-1",
        "asin": "B001TEST",
        "overall": 2.0,
        "helpfulness_ratio": 0.6,
        "unix_review_time": 1700000000.0,
        "review_datetime": datetime.now(UTC),
        "summary": "battery issue",
        "review_text": "battery life is poor and the charger stopped working after one week",
        "reviewer_id": "user-1",
        "reviewer_name": "A User",
        "review_length": 12,
        "sentiment_score": -0.18,
        "metadata": {},
        "semantic_score": 0.8,
        "final_score": 0.0,
    }
    payload.update(updates)
    return RetrievedReview(**payload)


def test_filtering_removes_duplicates() -> None:
    service = FilteringService()
    reviews = [build_review(review_id="a"), build_review(review_id="b")]
    filtered = service.apply(reviews)
    assert len(filtered) == 1


def test_filtering_removes_short_reviews() -> None:
    service = FilteringService()
    filtered = service.apply([build_review(review_text="bad item", review_length=2)])
    assert filtered == []

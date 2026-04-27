from dataclasses import dataclass

from app.utils.text import extract_review_themes


@dataclass
class ReviewStub:
    review_id: str
    overall: float
    sentiment_score: float
    helpfulness_ratio: float
    summary: str
    review_text: str


def test_extract_review_themes_requires_multi_review_support() -> None:
    reviews = [
        ReviewStub(
            review_id="1",
            overall=5.0,
            sentiment_score=0.2,
            helpfulness_ratio=0.7,
            summary="great battery",
            review_text="battery life is excellent and lasts all day",
        )
    ]

    assert extract_review_themes(reviews, polarity="positive", limit=5) == []


def test_extract_review_themes_finds_supported_negative_theme() -> None:
    reviews = [
        ReviewStub(
            review_id="1",
            overall=1.0,
            sentiment_score=-0.2,
            helpfulness_ratio=0.8,
            summary="battery issue",
            review_text="battery life is poor and battery life drains quickly",
        ),
        ReviewStub(
            review_id="2",
            overall=2.0,
            sentiment_score=-0.15,
            helpfulness_ratio=0.5,
            summary="poor battery",
            review_text="battery life is poor and needs charging too often",
        ),
    ]

    themes = extract_review_themes(reviews, polarity="negative", limit=5)
    assert "battery life" in themes

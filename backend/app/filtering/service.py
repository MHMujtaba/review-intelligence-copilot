from collections import Counter

from app.core.config import get_settings
from app.ml.classifier import ReviewQualityClassifier
from app.schemas.contracts import RetrievedReview
from app.utils.text import dedupe_key, tokenize_words, word_count


class FilteringService:
    def __init__(self, quality_classifier: ReviewQualityClassifier | None = None) -> None:
        self.settings = get_settings()
        self.quality_classifier = quality_classifier or ReviewQualityClassifier()

    def apply(self, reviews: list[RetrievedReview]) -> list[RetrievedReview]:
        seen: set[str] = set()
        accepted_texts: list[str] = []
        filtered: list[RetrievedReview] = []

        for review in reviews:
            if word_count(review.review_text) < self.settings.min_review_words:
                continue
            if review.helpfulness_ratio < self.settings.min_helpfulness_ratio and review.review_length >= 15:
                continue
            if self.quality_classifier.predict_probability(review) >= self.settings.quality_threshold:
                continue
            key = dedupe_key(review.review_text)
            if key in seen:
                continue
            if self._is_near_duplicate(review.review_text, accepted_texts):
                continue

            seen.add(key)
            accepted_texts.append(review.review_text)
            filtered.append(review)

        return filtered

    def _is_near_duplicate(self, text: str, accepted_texts: list[str]) -> bool:
        current_tokens = Counter(tokenize_words(text))
        if not current_tokens:
            return False
        for existing_text in accepted_texts:
            other_tokens = Counter(tokenize_words(existing_text))
            overlap = sum((current_tokens & other_tokens).values())
            union = sum((current_tokens | other_tokens).values()) or 1
            similarity = overlap / union
            if similarity >= self.settings.near_duplicate_similarity:
                return True
        return False

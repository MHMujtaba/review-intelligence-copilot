from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier

from app.core.config import get_settings
from app.schemas.contracts import IndexedReview, ProcessedReview


class ReviewQualityClassifier:
    def __init__(self) -> None:
        settings = get_settings()
        self.model_path = Path(settings.model_dir) / "review_quality_classifier.joblib"
        self.model = None
        self._load()

    def train(self, reviews: list[ProcessedReview]) -> None:
        if len(reviews) < 10:
            return
        features = np.asarray([self._feature_vector(review) for review in reviews], dtype=np.float32)
        labels = np.asarray([self._weak_label(review) for review in reviews], dtype=np.int32)
        if len(set(labels.tolist())) < 2:
            return

        self.model = RandomForestClassifier(
            n_estimators=150,
            max_depth=8,
            min_samples_leaf=2,
            random_state=42,
        )
        self.model.fit(features, labels)
        joblib.dump(self.model, self.model_path)

    def predict_probability(self, review: ProcessedReview | IndexedReview) -> float:
        features = np.asarray([self._feature_vector(review)], dtype=np.float32)
        if self.model is None:
            return float(self._heuristic_probability(review))
        probability = float(self.model.predict_proba(features)[0][1])
        return round(probability, 4)

    def _load(self) -> None:
        if self.model_path.exists():
            self.model = joblib.load(self.model_path)

    def _feature_vector(self, review: ProcessedReview | IndexedReview) -> list[float]:
        return [
            float(review.review_length),
            float(review.sentiment_score),
            float(review.helpfulness_ratio),
            float(review.overall),
        ]

    def _weak_label(self, review: ProcessedReview) -> int:
        repetitive = review.review_length < 7
        extreme = abs(review.sentiment_score) > 0.25 and review.total_votes == 0
        low_helpful = review.helpfulness_ratio < 0.01 and review.review_length < 15
        return int(repetitive or extreme or low_helpful)

    def _heuristic_probability(self, review: ProcessedReview | IndexedReview) -> float:
        score = 0.0
        if review.review_length < 8:
            score += 0.35
        if review.helpfulness_ratio < 0.01:
            score += 0.3
        if abs(review.sentiment_score) > 0.2:
            score += 0.2
        if review.overall in {1.0, 5.0}:
            score += 0.1
        return min(score, 0.95)

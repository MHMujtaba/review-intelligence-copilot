import ast
import hashlib
from datetime import datetime, timezone

import pandas as pd

from app.schemas.contracts import ProcessedReview
from app.utils.text import normalize_text, sentiment_score, word_count


class PreprocessingService:
    def process_records(self, raw_records: list[dict]) -> list[ProcessedReview]:
        dataframe = pd.DataFrame(raw_records)
        dataframe["reviewText"] = dataframe["reviewText"].fillna("").astype(str)
        dataframe["summary"] = dataframe["summary"].fillna("").astype(str)
        dataframe["reviewerName"] = dataframe["reviewerName"].fillna("").astype(str)
        dataframe["reviewTime"] = dataframe["reviewTime"].fillna("").astype(str)
        dataframe["overall"] = pd.to_numeric(dataframe["overall"], errors="coerce").fillna(3.0).clip(1.0, 5.0)
        dataframe["unixReviewTime"] = pd.to_numeric(dataframe["unixReviewTime"], errors="coerce").fillna(0.0)
        dataframe[["helpful_votes", "total_votes"]] = dataframe["helpful"].apply(self._parse_helpful).apply(pd.Series)
        dataframe["review_datetime"] = dataframe["unixReviewTime"].apply(self._to_datetime)
        dataframe["helpfulness_ratio"] = dataframe.apply(
            lambda row: float(row["helpful_votes"]) / (float(row["total_votes"]) + 1.0),
            axis=1,
        )
        dataframe["clean_text"] = dataframe["reviewText"].map(normalize_text)
        dataframe["review_length"] = dataframe["reviewText"].map(word_count)
        dataframe["sentiment_score"] = dataframe["reviewText"].map(sentiment_score)
        dataframe = dataframe.dropna(subset=["asin", "reviewerID", "reviewText"])
        dataframe = dataframe[dataframe["reviewText"].str.strip().astype(bool)]

        processed: list[ProcessedReview] = []
        for row in dataframe.itertuples(index=False):
            review_id = self._build_review_id(
                asin=str(row.asin),
                reviewer_id=str(row.reviewerID),
                unix_review_time=float(row.unixReviewTime),
                review_text=str(row.reviewText),
            )
            processed.append(
                ProcessedReview(
                    review_id=review_id,
                    asin=str(row.asin),
                    reviewer_id=str(row.reviewerID),
                    reviewer_name=str(row.reviewerName),
                    overall=float(row.overall),
                    summary=str(row.summary),
                    review_text=str(row.reviewText),
                    review_time=str(row.reviewTime),
                    unix_review_time=float(row.unixReviewTime),
                    review_datetime=row.review_datetime,
                    helpful_votes=int(row.helpful_votes),
                    total_votes=int(row.total_votes),
                    helpfulness_ratio=float(row.helpfulness_ratio),
                    clean_text=str(row.clean_text),
                    review_length=int(row.review_length),
                    sentiment_score=float(row.sentiment_score),
                )
            )
        return processed

    @staticmethod
    def _parse_helpful(value) -> tuple[int, int]:
        if isinstance(value, (list, tuple)) and len(value) >= 2:
            return int(value[0]), int(value[1])
        try:
            parsed = ast.literal_eval(str(value))
            if isinstance(parsed, (list, tuple)) and len(parsed) >= 2:
                return int(parsed[0]), int(parsed[1])
        except (ValueError, SyntaxError):
            pass
        return 0, 0

    @staticmethod
    def _to_datetime(unix_time: float) -> datetime:
        if unix_time <= 0:
            return datetime.fromtimestamp(0, tz=timezone.utc)
        return datetime.fromtimestamp(unix_time, tz=timezone.utc)

    @staticmethod
    def _build_review_id(asin: str, reviewer_id: str, unix_review_time: float, review_text: str) -> str:
        digest = hashlib.sha256(f"{asin}|{reviewer_id}|{unix_review_time}|{review_text}".encode("utf-8")).hexdigest()
        return digest[:24]

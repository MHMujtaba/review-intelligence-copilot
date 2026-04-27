import hashlib
import re
import string
from collections import Counter
from typing import Any, Iterable, Literal


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "for",
    "from",
    "had",
    "has",
    "have",
    "i",
    "if",
    "in",
    "is",
    "it",
    "its",
    "me",
    "my",
    "of",
    "on",
    "or",
    "so",
    "that",
    "the",
    "this",
    "to",
    "very",
    "was",
    "were",
    "with",
}

POSITIVE_WORDS = {
    "amazing",
    "awesome",
    "best",
    "comfortable",
    "excellent",
    "fast",
    "good",
    "great",
    "helpful",
    "love",
    "perfect",
    "quality",
    "recommend",
    "reliable",
    "smooth",
}

NEGATIVE_WORDS = {
    "awful",
    "bad",
    "broke",
    "broken",
    "cheap",
    "defective",
    "disappointed",
    "issue",
    "poor",
    "return",
    "slow",
    "terrible",
    "waste",
    "weak",
    "worst",
}

GENERIC_THEME_TOKENS = {
    "amazon",
    "arrived",
    "bought",
    "buy",
    "day",
    "days",
    "item",
    "month",
    "months",
    "ordered",
    "order",
    "package",
    "product",
    "purchase",
    "review",
    "seller",
    "shipping",
    "star",
    "stars",
    "thing",
    "time",
    "week",
    "weeks",
}


def tokenize_words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", text.lower())


def normalize_text(text: str) -> str:
    lowered = text.lower()
    stripped = lowered.translate(str.maketrans("", "", string.punctuation))
    tokens = [token for token in stripped.split() if token and token not in STOPWORDS]
    return " ".join(tokens)


def sentiment_score(text: str) -> float:
    tokens = tokenize_words(text)
    if not tokens:
        return 0.0
    positive = sum(1 for token in tokens if token in POSITIVE_WORDS)
    negative = sum(1 for token in tokens if token in NEGATIVE_WORDS)
    return round((positive - negative) / max(len(tokens), 1), 4)


def word_count(text: str) -> int:
    return len(tokenize_words(text))


def chunk_text(text: str, chunk_size: int = 260, overlap: int = 40) -> list[str]:
    words = text.split()
    if not words:
        return []
    chunks: list[str] = []
    step = max(chunk_size - overlap, 1)
    for start in range(0, len(words), step):
        chunk_words = words[start : start + chunk_size]
        if not chunk_words:
            continue
        chunks.append(" ".join(chunk_words))
        if start + chunk_size >= len(words):
            break
    return chunks


def dedupe_key(text: str) -> str:
    normalized = re.sub(r"\s+", " ", normalize_text(text)).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def extract_themes(texts: Iterable[str], limit: int = 5) -> list[str]:
    counter: Counter[str] = Counter()
    for text in texts:
        tokens = tokenize_words(normalize_text(text))
        for index in range(len(tokens) - 1):
            phrase = f"{tokens[index]} {tokens[index + 1]}"
            if len(phrase) > 5:
                counter[phrase] += 1
    return [phrase for phrase, _ in counter.most_common(limit)]


def extract_review_themes(
    reviews: Iterable[Any],
    polarity: Literal["positive", "negative"],
    limit: int = 5,
) -> list[str]:
    review_list = list(reviews)
    if len(review_list) < 2:
        return []

    filtered_reviews = [
        review
        for review in review_list
        if _matches_polarity(review, polarity)
    ]
    if len(filtered_reviews) < 2:
        return []

    phrase_stats: dict[str, dict[str, Any]] = {}
    for review in filtered_reviews:
        phrases: set[str] = set()
        for part in [getattr(review, "summary", ""), getattr(review, "review_text", "")]:
            if not isinstance(part, str) or not part.strip():
                continue
            tokens = tokenize_words(normalize_text(part))
            phrases.update(_generate_theme_candidates(tokens, polarity=polarity))
        if not phrases:
            continue

        helpfulness = min(max(float(getattr(review, "helpfulness_ratio", 0.0)), 0.0), 1.0)
        sentiment = float(getattr(review, "sentiment_score", 0.0))
        sentiment_bonus = max(sentiment, 0.0) if polarity == "positive" else max(-sentiment, 0.0)

        for phrase in phrases:
            stats = phrase_stats.setdefault(phrase, {"review_ids": set(), "score": 0.0})
            review_id = str(getattr(review, "review_id", phrase))
            if review_id in stats["review_ids"]:
                continue
            stats["review_ids"].add(review_id)
            stats["score"] += 1.0 + helpfulness + min(sentiment_bonus * 8, 0.75)

    ranked: list[tuple[str, int, float]] = []
    for phrase, stats in phrase_stats.items():
        support = len(stats["review_ids"])
        if support < 2:
            continue
        ranked.append((phrase, support, support * 2.0 + stats["score"]))

    ranked.sort(
        key=lambda item: (
            -item[1],
            -item[2],
            len(item[0].split()),
            len(item[0]),
        )
    )

    selected: list[str] = []
    for phrase, _, _ in ranked:
        if _overlaps_with_selected(phrase, selected):
            continue
        selected.append(phrase)
        if len(selected) >= limit:
            break
    return selected


def _matches_polarity(review: Any, polarity: Literal["positive", "negative"]) -> bool:
    overall = float(getattr(review, "overall", 0.0))
    sentiment = float(getattr(review, "sentiment_score", 0.0))
    if polarity == "positive":
        return overall >= 4.0 and sentiment >= 0.0
    return overall <= 2.0 and sentiment <= 0.0


def _generate_theme_candidates(
    tokens: list[str],
    polarity: Literal["positive", "negative"],
) -> set[str]:
    candidates: set[str] = set()
    blocked_words = NEGATIVE_WORDS if polarity == "positive" else POSITIVE_WORDS

    for window_size in (2, 3):
        for index in range(len(tokens) - window_size + 1):
            phrase_tokens = tokens[index : index + window_size]
            if not _is_informative_theme_phrase(phrase_tokens):
                continue
            if any(token in blocked_words for token in phrase_tokens):
                continue
            candidates.add(" ".join(phrase_tokens))
    return candidates


def _is_informative_theme_phrase(tokens: list[str]) -> bool:
    if len(tokens) < 2:
        return False
    if len(set(tokens)) != len(tokens):
        return False
    sentiment_tokens = POSITIVE_WORDS.union(NEGATIVE_WORDS)
    if tokens[-1] in sentiment_tokens and tokens[0] not in sentiment_tokens:
        return False
    if all(token in POSITIVE_WORDS.union(NEGATIVE_WORDS) for token in tokens):
        return False

    non_generic_tokens = [
        token
        for token in tokens
        if token not in GENERIC_THEME_TOKENS and len(token) > 2
    ]
    if len(non_generic_tokens) < 2:
        return False
    return True


def _overlaps_with_selected(phrase: str, selected: list[str]) -> bool:
    phrase_tokens = set(phrase.split())
    for existing in selected:
        existing_tokens = set(existing.split())
        if phrase_tokens.issubset(existing_tokens) or existing_tokens.issubset(phrase_tokens):
            return True
    return False

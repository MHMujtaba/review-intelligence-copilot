from app.schemas.contracts import RetrievedReview


def recall_at_k(retrieved: list[RetrievedReview], relevant_ids: set[str], k: int) -> float:
    if not relevant_ids:
        return 0.0
    selected = {review.review_id for review in retrieved[:k]}
    return len(selected.intersection(relevant_ids)) / len(relevant_ids)


def precision_at_k(retrieved: list[RetrievedReview], relevant_ids: set[str], k: int) -> float:
    if k == 0:
        return 0.0
    selected = {review.review_id for review in retrieved[:k]}
    return len(selected.intersection(relevant_ids)) / k


def groundedness(answer: str, context: dict) -> float:
    support_text = " ".join(
        context.get("top_complaints", [])
        + context.get("top_positive_aspects", [])
        + [item.get("snippet", "") for item in context.get("representative_snippets", [])]
    ).lower()
    answer_tokens = set(answer.lower().split())
    if not answer_tokens:
        return 0.0
    supported = sum(1 for token in answer_tokens if token in support_text)
    return round(supported / len(answer_tokens), 4)


def relevance(answer: str, query: str) -> float:
    answer_tokens = set(answer.lower().split())
    query_tokens = set(query.lower().split())
    if not query_tokens:
        return 0.0
    overlap = len(answer_tokens.intersection(query_tokens))
    return round(overlap / len(query_tokens), 4)

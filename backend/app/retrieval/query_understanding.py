from app.schemas.contracts import QueryType


COMPLAINT_TERMS = {"broken", "complaint", "issue", "problem", "return", "worst", "bad", "negative", "hate"}
POSITIVE_TERMS = {"best", "good", "great", "love", "positive", "recommend", "worth", "favorite"}
SUMMARY_TERMS = {"summary", "summarize", "overview", "insights", "patterns", "trend", "overall"}


def classify_query(query: str) -> QueryType:
    lowered = query.lower()
    complaint_hits = sum(term in lowered for term in COMPLAINT_TERMS)
    positive_hits = sum(term in lowered for term in POSITIVE_TERMS)
    summary_hits = sum(term in lowered for term in SUMMARY_TERMS)

    if complaint_hits > 0 and complaint_hits >= positive_hits:
        return QueryType(label="complaint_query", confidence=min(1.0, 0.55 + complaint_hits * 0.1))
    if positive_hits > 0 and positive_hits > complaint_hits:
        return QueryType(label="positive_query", confidence=min(1.0, 0.55 + positive_hits * 0.1))
    if summary_hits > 0:
        return QueryType(label="summary_query", confidence=min(1.0, 0.55 + summary_hits * 0.1))
    return QueryType(label="general_query", confidence=0.5)

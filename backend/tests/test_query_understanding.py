from app.retrieval.query_understanding import classify_query


def test_classify_complaint_query() -> None:
    result = classify_query("What are the biggest issues and returns customers mention?")
    assert result.label == "complaint_query"


def test_classify_positive_query() -> None:
    result = classify_query("Why do customers love this product and recommend it?")
    assert result.label == "positive_query"

from app.preprocessing.service import PreprocessingService


def test_parse_helpful_string() -> None:
    service = PreprocessingService()
    helpful_votes, total_votes = service._parse_helpful("[2, 5]")
    assert helpful_votes == 2
    assert total_votes == 5

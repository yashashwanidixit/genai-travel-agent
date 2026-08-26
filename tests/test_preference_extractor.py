from app.preferences.preference_extractor import extract_preferences


def test_around_price():
    result = extract_preferences(
        "book me a hotel around 4000 per night"
    )

    assert result.target_price == 4000
    assert result.target_rating is None


def test_approximately_price():
    result = extract_preferences(
        "I'd like a hotel approximately 5000 per night"
    )

    assert result.target_price == 5000


def test_around_rating():
    result = extract_preferences(
        "book me a hotel around 4 rated"
    )

    assert result.target_rating == 4
    assert result.target_price is None


def test_approximately_rating():
    result = extract_preferences(
        "I'd prefer approximately 4.5 rated"
    )

    assert result.target_rating == 4.5


def test_price_and_rating_together():
    result = extract_preferences(
        "book me a hotel around 4000 and around 4 rated"
    )

    assert result.target_price == 4000
    assert result.target_rating == 4
    
def test_soft_price_is_not_hard_price():
    result = extract_preferences(
        "book me a hotel around 4000"
    )

    assert result.target_price == 4000    
    
    
def test_soft_rating_is_not_hard_rating():
    result = extract_preferences(
        "book me a hotel around 4 rated"
    )

    assert result.target_rating == 4    
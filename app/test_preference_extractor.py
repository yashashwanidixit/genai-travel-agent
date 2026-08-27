from app.preferences.preference_extractor import extract_preferences




def test_price_is_not_confused_with_distance():
    result = extract_preferences(
        "book me a hotel around 3 km from Bangalore airport"
    )

    assert result.target_price is None
    assert result.target_rating is None


def test_soft_price():
    result = extract_preferences(
        "book me a hotel around 4000 per night"
    )

    assert result.target_price == 4000
    assert result.target_rating is None


def test_soft_rating():
    result = extract_preferences(
        "book me a hotel around 4.5 rated"
    )

    assert result.target_rating == 4.5
    assert result.target_price is None


def test_price_and_rating():
    result = extract_preferences(
        "book me a hotel around 4000 and around 4 rated"
    )

    assert result.target_price == 4000
    assert result.target_rating == 4


def test_distance_does_not_become_price():
    result = extract_preferences(
        "I'd prefer a hotel around 5 km from my meeting"
    )

    assert result.target_price is None
    assert result.target_rating is None
    
    

# ============================================================
# SOFT PRICE MUST NOT BECOME HARD PRICE
# ============================================================

def test_soft_price_does_not_become_hard_price():
    result = extract_preferences(
        "book me a hotel around 4000 per night"
    )

    assert result.target_price == 4000
    assert result.target_rating is None

    # Soft extractor only returns soft preferences.
    # It cannot create hard constraints.
    assert not hasattr(result, "max_hotel_price")


def test_soft_price_with_prefer_does_not_become_hard_price():
    result = extract_preferences(
        "I prefer a hotel around 4000 per night"
    )

    assert result.target_price == 4000
    assert result.target_rating is None
    assert not hasattr(result, "max_hotel_price")


def test_soft_price_about_does_not_become_hard_price():
    result = extract_preferences(
        "I'd like a hotel about 5000 per night"
    )

    assert result.target_price == 5000
    assert result.target_rating is None
    assert not hasattr(result, "max_hotel_price")


# ============================================================
# SOFT RATING MUST NOT BECOME HARD RATING
# ============================================================

def test_soft_rating_does_not_become_hard_rating():
    result = extract_preferences(
        "book me a hotel around 4 rated"
    )

    assert result.target_rating == 4
    assert result.target_price is None
    assert not hasattr(result, "minimum_hotel_rating")


def test_soft_rating_with_prefer_does_not_become_hard_rating():
    result = extract_preferences(
        "I prefer a hotel around 4.5 rated"
    )

    assert result.target_rating == 4.5
    assert result.target_price is None
    assert not hasattr(result, "minimum_hotel_rating")


def test_soft_stars_does_not_become_hard_rating():
    result = extract_preferences(
        "I'd prefer about 4.5 star hotel"
    )
    print(f"price : {result.target_price}") 
    print(f"rating : {result.target_rating}")
    print(f"distance : {result.target_distance}")
  
    
    

    assert result.target_rating == 4.5
    assert result.target_price is None
    assert not hasattr(result, "minimum_hotel_rating")


# ============================================================
# SOFT DISTANCE MUST NOT BECOME HARD DISTANCE
# ============================================================

def test_soft_distance_does_not_become_price():
    result = extract_preferences(
        "I'd prefer a hotel around 5 km from my meeting"
    )

    assert result.target_price is None
    assert result.target_rating is None


def test_soft_distance_does_not_become_rating():
    result = extract_preferences(
        "I'd prefer a hotel around 5 km from my meeting"
    )

    assert result.target_rating is None


# ============================================================
# PRICE + RATING
# ============================================================

def test_soft_price_and_rating_stay_separate():
    result = extract_preferences(
        "book me a hotel around 4000 per night and around 4 rated"
    )

    assert result.target_price == 4000
    assert result.target_rating == 4


def test_soft_price_and_rating_with_prefer():
    result = extract_preferences(
        "I prefer a hotel around 4000 per night and around 4.5 rated"
    )

    assert result.target_price == 4000
    assert result.target_rating == 4.5


# ============================================================
# DISTANCE + PRICE
# ============================================================

def test_distance_and_price_are_not_confused():
    result = extract_preferences(
        "book me a hotel around 3 km from Bangalore airport "
        "and around 4000 per night"
    )

    # 3 must NOT become price.
    assert result.target_price == 4000

    # 3 must NOT become rating.
    assert result.target_rating is None


def test_distance_before_price():
    result = extract_preferences(
        "around 5 km from the airport and around 5000 per night"
    )

    assert result.target_price == 5000
    assert result.target_rating is None


def test_price_before_distance():
    result = extract_preferences(
        "around 5000 per night and around 5 km from the airport"
    )

    assert result.target_price == 5000
    assert result.target_rating is None


# ============================================================
# DISTANCE + RATING
# ============================================================

def test_distance_and_rating_are_not_confused():
    result = extract_preferences(
        "around 5 km from the airport and around 4.5 rated"
    )

    assert result.target_rating == 4.5
    assert result.target_price is None


def test_rating_before_distance():
    result = extract_preferences(
        "around 4.5 rated and around 5 km from the airport"
    )

    assert result.target_rating == 4.5
    assert result.target_price is None


# ============================================================
# ALL THREE DOMAINS
# ============================================================

def test_price_rating_distance_all_together():
    result = extract_preferences(
        "book me a hotel around 4000 per night, "
        "around 4.5 rated, and around 5 km from the airport"
    )

    assert result.target_price == 4000
    assert result.target_rating == 4.5


def test_all_three_different_order():
    result = extract_preferences(
        "around 5 km from the airport, "
        "preferably around 4.5 rated, "
        "and around 4000 per night"
    )

    assert result.target_price == 4000
    assert result.target_rating == 4.5


# ============================================================
# IMPORTANT: HARD LANGUAGE SHOULD NOT BE TREATED AS SOFT
# ============================================================

def test_hard_price_is_not_soft_price():
    result = extract_preferences(
        "book me a hotel below 4000 per night"
    )

    assert result.target_price is None


def test_hard_rating_is_not_soft_rating():
    result = extract_preferences(
        "book me a hotel with at least 4 rated"
    )

    assert result.target_rating is None


def test_hard_distance_is_not_soft_distance():
    result = extract_preferences(
        "book me a hotel within 10 km of the airport"
    )

    assert result.target_price is None
    assert result.target_rating is None    
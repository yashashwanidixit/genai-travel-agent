from app.recommendation.score_calculation import calculate_score
import pytest
from app.recommendation.user_profile import USER_PROFILE_A
from app.recommendation.utility_calculation import HotelUtilities


def test_score():
    utilities = HotelUtilities(
        price_utility=0.8,
        rating_utility=0.9,
        distance_utility=0.7,
    )

    score = calculate_score(
        utilities,
        USER_PROFILE_A,
    )

    assert score.final_score == pytest.approx(0.83)
    
    
    
def test_score_without_distance():
    utilities = HotelUtilities(
        price_utility=0.8,
        rating_utility=0.9,
        distance_utility=None,
    )

    score = calculate_score(
        utilities,
        USER_PROFILE_A,
    )

    assert score.final_score == pytest.approx(0.8625) 
    
    
    
def test_perfect_utilities():
    utilities = HotelUtilities(
        price_utility=1.0,
        rating_utility=1.0,
        distance_utility=1.0,
    )

    score = calculate_score(
        utilities,
        USER_PROFILE_A,
    )

    assert score.final_score == pytest.approx(1.0)   
    
    
def test_zero_utilities():
    utilities = HotelUtilities(
        price_utility=0.0,
        rating_utility=0.0,
        distance_utility=0.0,
    )

    score = calculate_score(
        utilities,
        USER_PROFILE_A,
    )

    assert score.final_score == pytest.approx(0.0)       
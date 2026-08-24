from app.models.hotel import Hotel
from app.models.ride import RideEstimate, RideType
from app.models.user import UserPreferences
from app.recommendation.feature_extraction import FeatureExtractor
from app.recommendation.normalizer import Normalizer
from app.recommendation.scorer import WeightedScorer
from app.recommendation.ranker import TravelRanker


def test_normalizer_scaling():
    values = [10.0, 20.0, 30.0]
    scaled = Normalizer.min_max_scale(values)
    assert scaled == [0.0, 0.5, 1.0]

    inverted = Normalizer.min_max_scale(values, invert=True)
    assert inverted == [1.0, 0.5, 0.0]


def test_scorer_calculation():
    features = {"rating": 1.0, "review_count": 0.5, "star_match": 1.0, "amenity_score": 0.8, "budget_score": 0.9}
    score = WeightedScorer.calculate_score(features, WeightedScorer.DEFAULT_HOTEL_WEIGHTS)
    assert 0.0 <= score <= 1.0


def test_hotel_and_ride_ranker():
    ranker = TravelRanker()
    prefs = UserPreferences(preferred_hotel_stars=5, max_hotel_budget_per_night=15000.0)

    hotels = [
        Hotel(id="h1", name="Budget Inn", city="Bengaluru", address="A", star_rating=3, user_rating=3.8, price_per_night=3000.0),
        Hotel(id="h2", name="Luxury Palace", city="Bengaluru", address="B", star_rating=5, user_rating=4.9, price_per_night=14000.0),
    ]

    ranked = ranker.rank_hotels(hotels, prefs)
    assert len(ranked) == 2
    assert ranked[0].score is not None
    assert ranked[0].score >= ranked[1].score

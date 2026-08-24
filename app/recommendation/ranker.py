from typing import List, Optional
from app.models.hotel import Hotel
from app.models.ride import RideEstimate
from app.models.user import UserPreferences
from app.recommendation.feature_extraction import extract_features
from app.recommendation.normalizer import Normalizer
from app.recommendation.scorer import WeightedScorer


class TravelRanker:
    """Ranks hotels and rides based on user preferences, pricing, and ratings."""

    def __init__(self, feature_extractor: Optional[extract_features] = None, scorer: Optional[WeightedScorer] = None):
        self.feature_extractor = feature_extractor or extract_features()
        self.scorer = scorer or WeightedScorer()

    def rank_hotels(self, hotels: List[Hotel], prefs: UserPreferences) -> List[Hotel]:
        if not hotels:
            return []

        raw_features = [self.feature_extractor.extract_hotel_features(h, prefs) for h in hotels]
        normalized = Normalizer.normalize_feature_matrix(raw_features, invert_keys=["price"])

        scored_hotels = []
        for hotel, feats in zip(hotels, normalized):
            score = self.scorer.calculate_score(feats, self.scorer.DEFAULT_HOTEL_WEIGHTS)
            hotel_copy = hotel.model_copy(update={"score": score})
            scored_hotels.append(hotel_copy)

        scored_hotels.sort(key=lambda h: (h.score or 0.0), reverse=True)
        return scored_hotels

    def rank_rides(self, rides: List[RideEstimate], prefs: UserPreferences) -> List[RideEstimate]:
        if not rides:
            return []

        raw_features = [self.feature_extractor.extract_ride_features(r, prefs) for r in rides]
        normalized = Normalizer.normalize_feature_matrix(raw_features, invert_keys=["fare", "duration", "eta_pickup"])

        scored_rides = []
        for ride, feats in zip(rides, normalized):
            score = self.scorer.calculate_score(feats, self.scorer.DEFAULT_RIDE_WEIGHTS)
            ride_copy = ride.model_copy(update={"score": score})
            scored_rides.append(ride_copy)

        scored_rides.sort(key=lambda r: (r.score or 0.0), reverse=True)
        return scored_rides

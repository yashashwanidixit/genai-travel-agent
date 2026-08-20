from typing import Dict, List, Any
from app.models.hotel import Hotel
from app.models.ride import RideEstimate
from app.models.user import UserPreferences


class FeatureExtractor:
    """Extracts normalized numerical and categorical signals from travel candidates."""

    @staticmethod
    def extract_hotel_features(hotel: Hotel, prefs: UserPreferences) -> Dict[str, float]:
        # Star alignment
        star_diff = abs(hotel.star_rating - prefs.preferred_hotel_stars)
        star_match = max(0.0, 1.0 - (star_diff / 4.0))

        # Amenity overlap
        matching_amenities = sum(1 for a in prefs.preferred_amenities if a in hotel.amenities)
        amenity_score = (
            matching_amenities / len(prefs.preferred_amenities)
            if prefs.preferred_amenities
            else 1.0
        )

        # Budget fit
        budget_ratio = (
            prefs.max_hotel_budget_per_night / hotel.price_per_night
            if hotel.price_per_night > 0
            else 1.0
        )
        budget_score = min(1.0, budget_ratio)

        return {
            "price": hotel.price_per_night,
            "rating": hotel.user_rating,
            "review_count": float(hotel.review_count),
            "star_match": star_match,
            "amenity_score": amenity_score,
            "budget_score": budget_score,
        }

    @staticmethod
    def extract_ride_features(ride: RideEstimate, prefs: UserPreferences) -> Dict[str, float]:
        type_match = 1.0 if ride.ride_type.value.lower() == prefs.preferred_ride_type.lower() else 0.5

        return {
            "fare": ride.estimated_fare,
            "duration": float(ride.duration_minutes),
            "distance": float(ride.distance_km),
            "eta_pickup": float(ride.eta_pickup_minutes),
            "type_match": type_match,
        }

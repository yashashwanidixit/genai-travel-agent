"""R1 — Recommendation Feature Extraction.

Answers ONLY: "what factual properties does this hotel have that a
future recommendation system may need?"

R1 extracts RAW FACTS from a Hotel. It does not:
- convert facts into [0,1] utilities (that is a future R2 stage)
- apply any weighting or scoring (that is a future R3+ stage)
- know anything about UserProfile or user preferences (those belong
  to a different data domain - HotelFeatures describes the hotel,
  UserProfile describes the user, and R1 must not couple the two)

Architecture:

    Hotel
       |
    extract_features()
       |
    HotelFeatures  (raw price, raw rating, distance-or-None)

The extractor never mutates the Hotel it's given - it only reads from
it and returns a brand new HotelFeatures object.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from app.models.hotel import Hotel


class HotelFeatures(BaseModel):
    """Raw factual features extracted from a single Hotel.

    These are facts, not utilities and not scores. A future R2 stage
    is responsible for converting these into normalized [0,1]-style
    utilities; R1 must never do that conversion itself.
    """

    price: float
    rating: float
    distance_km: Optional[float] = None


def extract_features(hotel: Hotel) -> HotelFeatures:
    """Extracts raw, factual features from a single Hotel.

    price  -> hotel.price_per_night, unchanged
    rating -> hotel.user_rating (NOT star_rating - user_rating is the
              rating feature the current recommendation design uses,
              since it reflects real guest experience rather than an
              official star classification)
    distance_km -> always None right now.

    WHY distance is always None: computing a real distance requires a
    reference location (e.g. coordinates for "Whitefield", or the
    user's current location) to measure against. Nothing in the
    current architecture - HotelSearchQuery, TravelIntent, or
    anywhere else - currently carries such a reference coordinate.
    HotelSearchQuery.location is a plain string like "Whitefield", not
    a lat/lng pair. Rather than invent, hardcode, or geocode a
    coordinate (explicitly forbidden), R1 leaves distance_km unset
    until a reliable reference location genuinely exists in the
    architecture. This keeps the feature interface ready for that
    future addition without fabricating data today.

    Does not mutate the given Hotel object.
    """
    return HotelFeatures(
        price=hotel.price_per_night,
        rating=hotel.user_rating,
        distance_km=None,
    )
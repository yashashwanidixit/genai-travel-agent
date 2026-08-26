"""
R1 — Recommendation Feature Extraction.

Answers ONLY:
"what factual properties does this hotel have that a
future recommendation system may need?"

R1 extracts RAW FACTS.

It does not:
- normalize facts into [0,1] utilities
- apply weighting
- calculate recommendation scores
- use UserProfile or user preferences
- calculate distance
- perform routing
- perform hard filtering

Architecture:

    HotelContext
        |
        |-- hotel.price_per_night
        |-- hotel.user_rating
        |-- distance_km
        |
    extract_features()
        |
    HotelFeatures
        (raw price, raw rating, distance)

The extractor never mutates the Hotel or HotelContext.
It only reads from them and returns a new HotelFeatures object.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from app.models.hotel_context import HotelContext


class HotelFeatures(BaseModel):
    """Raw factual features extracted from a HotelContext."""

    price: float
    rating: float
    distance_km: Optional[float] = None


def extract_features(context: HotelContext) -> HotelFeatures:
    """Extract raw factual recommendation features.

    price:
        Comes directly from context.hotel.price_per_night.

    rating:
        Comes directly from context.hotel.user_rating.
        This is intentionally NOT hotel.star_rating.

    distance_km:
        Comes directly from context.distance_km.

        R1 does NOT calculate this distance. The routing layer has
        already calculated it before HotelContext reaches R1.

        If distance_km is None, R1 preserves None.

    No normalization, scoring, weighting, or filtering is performed.
    """

    return HotelFeatures(
        price=context.hotel.price_per_night,
        rating=context.hotel.user_rating,
        distance_km=context.distance_km,
    )
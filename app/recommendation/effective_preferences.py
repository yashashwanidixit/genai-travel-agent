"""
EffectivePreferences — resolves the current request's soft targets
against a UserProfile fallback, with NO alpha blending.

Rule (per current design, §8): for each dimension, if the current
intent/request supplies an explicit soft target, use it. Otherwise,
fall back to the user's stored profile preference. There is no
averaging and no partial blending between the two - it is one or the
other, chosen per-dimension independently.

This intermediate model exists so utility_calculation.py does not
need to understand TravelIntent, UserProfile, or any fallback logic
itself - it only ever consumes a fully-resolved EffectivePreferences
object with three plain floats.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from app.recommendation.user_profile import UserProfile
from app.preferences.preference_extractor import ExtractedPreferences


class EffectivePreferences(BaseModel):
    
    target_rating: float
    target_price: float



def resolve_effective_preferences(
    profile: UserProfile,
    preferences: ExtractedPreferences,
    max_hotel_price: float | None = None,
) -> EffectivePreferences:

    return EffectivePreferences(
        target_price=(
            max_hotel_price
            if max_hotel_price is not None
            else profile.preferred_price
        ),
        

        target_rating=(
            preferences.target_rating
            if preferences.target_rating is not None
            else profile.preferred_rating
        ),

    )
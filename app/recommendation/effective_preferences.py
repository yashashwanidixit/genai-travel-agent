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


class EffectivePreferences(BaseModel):
    target_price: float
    target_rating: float
    target_distance: float


def resolve_effective_preferences(
    profile: UserProfile,
    intent_target_price: Optional[float] = None,
    intent_target_rating: Optional[float] = None,
    intent_target_distance: Optional[float] = None,
) -> EffectivePreferences:
    """Resolves the effective target for each dimension independently.

    intent_target_* values come from the deterministic soft-preference
    extractor (per §5) via TravelIntent - this function does not parse
    or interpret them, it only checks whether each is None.
    """
    return EffectivePreferences(
        target_price=(
            intent_target_price
            if intent_target_price is not None
            else profile.preferred_price
        ),
        target_rating=(
            intent_target_rating
            if intent_target_rating is not None
            else profile.preferred_rating
        ),
        target_distance=(
            intent_target_distance
            if intent_target_distance is not None
            else profile.preferred_distance
        ),
    )
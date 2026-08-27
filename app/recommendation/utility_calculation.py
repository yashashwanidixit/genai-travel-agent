"""
R2 — Utility Calculation.

Converts raw HotelFeatures (from R1) into normalized [0,1] utilities,
measured against the user's EFFECTIVE preference targets (current
request soft preference, falling back to UserProfile).

All three dimensions here are TARGET-MATCHING features, not
"higher/lower is always better" features:

    price:    closest to target_price wins, not cheapest
    rating:   closest to target_rating wins, NOT highest rating
    distance: closest to target_distance wins, NOT nearest

This is a deliberate, explicitly documented design choice per the
current spec - it supersedes an earlier draft of R2 that treated
rating and distance as "higher/closer is always better."

R2 does NOT:
    - apply price_weight / rating_weight / distance_weight (future R3)
    - compute a final_score (future R3)
    - rank hotels
    - perform hard filtering
    - call an LLM, network, or routing service
    - mutate HotelFeatures / EffectivePreferences / UserProfile

Formulas:

    price_utility    = max(0, 1 - |price - target_price| / price_scale)
    rating_utility    = max(0, 1 - |rating - target_rating| / 5.0)
    distance_utility  = None if distance_km is None else
                        max(0, 1 - |distance_km - target_distance| / distance_scale)

price_scale and distance_scale are calibration constants (default
3000 and 10.0 respectively), not universal truths - they control how
quickly utility decays with deviation from the target.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from app.recommendation.effective_preferences import EffectivePreferences
from app.recommendation.feature_extraction import HotelFeatures

DEFAULT_PRICE_SCALE = 3000.0
RATING_RANGE = 5.0  # rating's fixed natural range, used as the rating deviation divisor


class HotelUtilities(BaseModel):
    """Normalized target-matching utilities. Contains ONLY utility
    values - no score, no weighted_score, no weights. Those belong to
    a future R3 stage that has not been implemented here.

    distance_utility is Optional because a hotel with no known
    distance (distance_km is None on HotelFeatures) has no calculable
    utility for that dimension - it is intentionally left unset rather
    than fabricated as 0.0 or 1.0.
    """

    price_utility: float
    rating_utility: float
   


def calculate_price_utility(
    price: float, target_price: float, scale: float = DEFAULT_PRICE_SCALE
) -> float:
    """Closeness of `price` to `target_price`, NOT "cheaper is better".

    - Measures: absolute deviation from the target, scaled down.
    - Range: always in [0,1] due to the max(0, ...) clamp.
    - Exact match (price == target_price): |0|/scale = 0 -> utility = 1.0.
    - As deviation grows, utility falls linearly until it hits 0 at
      deviation >= scale, then stays at 0 (never negative).
    - No division-by-zero risk: `scale` is a fixed calibration
      constant supplied by the caller/default, never derived from
      price or target_price itself.
    """
    deviation = abs(price - target_price)
    raw = 1.0 - deviation / scale
    return max(0.0, min(1.0, raw))


def calculate_rating_utility(rating: float, target_rating: float) -> float:
    """Closeness of `rating` to `target_rating`.

    EXPLICIT DESIGN CHOICE: a rating ABOVE the target is treated as
    deviation, exactly like a rating below it. This is symmetric, not
    "higher is always better." For example, target_rating=4.2 and
    rating=5.0 does NOT yield utility 1.0 - it yields 1 - 0.8/5 = 0.84,
    the same drop as rating=3.4 would produce.

    - Divisor is fixed at 5.0 (rating's natural max range), so the
      maximum possible deviation always maps to utility 0, and the
      clamp keeps every output in [0,1].
    - No division-by-zero risk: the divisor is the fixed constant 5.0,
      never target_rating or rating itself.
    """
    deviation = abs(rating - target_rating)
    raw = 1.0 - deviation / RATING_RANGE
    return max(0.0, min(1.0, raw))





def calculate_utilities(
    features: HotelFeatures,
    preferences: EffectivePreferences,
    price_scale: float = DEFAULT_PRICE_SCALE,
  
) -> HotelUtilities:
    """Top-level R2 entry point: HotelFeatures + EffectivePreferences
    -> HotelUtilities.

    Does not mutate features or preferences. Does not apply weights.
    Does not compute a final score. Does not rank anything.
    """
    return HotelUtilities(
        price_utility=calculate_price_utility(
            features.price, preferences.target_price, scale=price_scale
        ),
        rating_utility=calculate_rating_utility(
            features.rating, preferences.target_rating
        ),
        
    )
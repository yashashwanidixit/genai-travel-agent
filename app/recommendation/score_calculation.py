from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from app.recommendation.user_profile import UserProfile
from app.recommendation.utility_calculation import HotelUtilities


class HotelScore(BaseModel):
    """Weighted recommendation score for one hotel.

    R3 consumes already-calculated utilities and a UserProfile.

    It does NOT:
        - extract preferences
        - calculate utilities
        - perform hard filtering
        - rank hotels
        - call an LLM
        - mutate HotelFeatures
        - mutate UserProfile

    If distance_utility is None, the distance weight is excluded
    and the remaining weights are renormalized.
    """

    final_score: float


def calculate_score(
    utilities: HotelUtilities,
    profile: UserProfile,
) -> HotelScore:
    """Calculate the weighted recommendation score.

    Normal case:

        score =
            price_utility * price_weight
            + rating_utility * rating_weight
            + distance_utility * distance_weight

    If distance_utility is None, only the available dimensions
    contribute and their weights are renormalized.

    The returned score remains in [0, 1].
    """

    available_weight = (
        profile.price_weight
        + profile.rating_weight
    )

    weighted_sum = (
        utilities.price_utility * profile.price_weight
        + utilities.rating_utility * profile.rating_weight
    )

    if utilities.distance_utility is not None:
        available_weight += profile.distance_weight
        weighted_sum += (
            utilities.distance_utility
            * profile.distance_weight
        )

    if available_weight <= 0:
        raise ValueError(
            "At least one recommendation weight must be positive."
        )

    final_score = weighted_sum / available_weight

    return HotelScore(
        final_score=max(0.0, min(1.0, final_score))
    )
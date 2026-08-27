from __future__ import annotations

from pydantic import BaseModel

from app.recommendation.user_profile import UserProfile
from app.recommendation.utility_calculation import HotelUtilities


class HotelScore(BaseModel):
    """Weighted recommendation score for one hotel.

    R3 combines the already-calculated price and rating utilities
    using the corresponding UserProfile weights.

    Distance is NOT part of the score. Distance has already been
    handled upstream during candidate selection.
    """

    final_score: float


def calculate_score(
    utilities: HotelUtilities,
    profile: UserProfile,
) -> HotelScore:
    """Calculate the final recommendation score.

    Formula:

        score =
            price_utility  * price_weight
            + rating_utility * rating_weight

    Only price and rating contribute to the final score.

    Distance is intentionally excluded because distance is used
    upstream to select the candidate hotels.
    """

    available_weight = (
        profile.price_weight
        + profile.rating_weight
    )

    if available_weight <= 0:
        raise ValueError(
            "At least one of price_weight or rating_weight "
            "must be positive."
        )

    weighted_sum = (
        utilities.price_utility * profile.price_weight
        + utilities.rating_utility * profile.rating_weight
    )

    final_score = weighted_sum / available_weight

    return HotelScore(
        final_score=max(0.0, min(1.0, final_score))
    )
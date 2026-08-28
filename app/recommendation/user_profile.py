from __future__ import annotations

from pydantic import BaseModel


class UserProfile(BaseModel):
    name: str

    preferred_price: float
    preferred_rating: float
    preferred_distance: float

    rating_weight: float
    ranking_preference: str


# Temporary development profiles.
#
# These are test/development data only.
# Application logic must NOT import these directly.


USER_PROFILE_A = UserProfile(
    name="A",
    preferred_price=4000.0,
    preferred_rating=4.2,
    preferred_distance=5.0,
    rating_weight=0.5,
    ranking_preference="rating",
)


USER_PROFILE_B = UserProfile(
    name="B",
    preferred_price=6000.0,
    preferred_rating=4.0,
    preferred_distance=3.0,
    rating_weight=0.2,
    ranking_preference="price",
)


USER_PROFILE_C = UserProfile(
    name="C",
    preferred_price=3000.0,
    preferred_rating=4.5,
    preferred_distance=2.0,
    rating_weight=0.8,
    ranking_preference ="distance"
)
"""
UserProfile — hardcoded, fixed-weight user preference profiles.

NOTE: no UserProfile model existed anywhere in this project before
this task. This is a NEW file, created because R2 requires a fallback
preference source when the current request has no soft target. Verify
this against your real repository - if a UserProfile already exists
elsewhere with different field names, replace this file's contents
with that real model rather than keeping this one.

Weights (price_weight, rating_weight, distance_weight) are stored
here for the FUTURE R3 stage only. R2 must never read or apply them -
R2 only reads the preferred_* fields as fallback targets.
"""

from __future__ import annotations

from pydantic import BaseModel


class UserProfile(BaseModel):
    name: str

    preferred_price: float
    preferred_rating: float
    preferred_distance: float

    # Reserved for future R3 (weighted scoring). R2 must not read these.
    
    rating_weight: float
  


# Two hardcoded example profiles, per the current design.
USER_PROFILE_A = UserProfile(
    name="A",
    preferred_price=4000.0,
    preferred_rating=4.2,
    preferred_distance=5.0,
    price_weight = 0.5,

    rating_weight=0.5,

)

USER_PROFILE_B = UserProfile(
    name="B",
    preferred_price=6000.0,
    preferred_rating=4.0,
    preferred_distance=3.0,
    price_weight = 0.8,
    

    rating_weight=0.2,
    
)

USER_PROFILE_C = UserProfile(
    name="C",
    preferred_price=3000.0,
    preferred_rating=4.0,
    preferred_distance=5.0,
    price_weight=0.9,
    rating_weight=0.1,
)
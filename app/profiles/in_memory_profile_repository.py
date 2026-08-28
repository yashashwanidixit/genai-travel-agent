from __future__ import annotations

from app.profiles.profile_repository import ProfileRepository
from app.recommendation.user_profile import (
    UserProfile,
    USER_PROFILE_A,
    USER_PROFILE_B,
    USER_PROFILE_C,
)


class InMemoryProfileRepository(ProfileRepository):
    """Temporary profile repository backed by Python memory.

    Used during development before a real persistent
    profile/user-memory implementation exists.
    """

    def __init__(self) -> None:
        self._profiles: dict[str, UserProfile] = {
            "A": USER_PROFILE_A,
            "B": USER_PROFILE_B,
            "C": USER_PROFILE_C,
        }

    def get_profile(self, user_id: str) -> UserProfile:
        try:
            return self._profiles[user_id]
        except KeyError:
            raise ValueError(
                f"No profile found for user_id='{user_id}'"
            )
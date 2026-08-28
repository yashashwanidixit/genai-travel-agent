from __future__ import annotations

from abc import ABC, abstractmethod

from app.recommendation.user_profile import UserProfile


class ProfileRepository(ABC):
    """Interface for retrieving user profiles."""

    @abstractmethod
    def get_profile(self, user_id: str) -> UserProfile:
        """Return the profile belonging to user_id."""
        raise NotImplementedError
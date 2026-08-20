from typing import Dict, Optional
from app.models.user import UserPreferences


class PreferenceStore:
    """Manages persistent and session-level user preferences."""

    def __init__(self):
        self._user_preferences: Dict[str, UserPreferences] = {}

    def get_preferences(self, user_id: str) -> UserPreferences:
        if user_id not in self._user_preferences:
            self._user_preferences[user_id] = UserPreferences()
        return self._user_preferences[user_id]

    def update_preferences(self, user_id: str, updates: Dict) -> UserPreferences:
        current = self.get_preferences(user_id)
        current_data = current.model_dump()
        current_data.update(updates)
        updated = UserPreferences(**current_data)
        self._user_preferences[user_id] = updated
        return updated

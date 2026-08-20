from typing import Dict, Any, Optional
from app.memory.episodic import EpisodicMemory
from app.memory.semantic import SemanticMemory
from app.memory.preferences import PreferenceStore
from app.models.user import UserPreferences
from app.models.intent import TravelIntent


class MemoryAgent:
    """Agent responsible for maintaining short-term conversation context, long-term user preferences, and semantic world facts."""

    def __init__(
        self,
        episodic: Optional[EpisodicMemory] = None,
        semantic: Optional[SemanticMemory] = None,
        preferences: Optional[PreferenceStore] = None
    ):
        self.episodic = episodic or EpisodicMemory()
        self.semantic = semantic or SemanticMemory()
        self.preferences = preferences or PreferenceStore()

    def record_interaction(self, session_id: str, role: str, content: str, metadata: Optional[Dict[str, str]] = None):
        self.episodic.add_turn(session_id=session_id, role=role, content=content, metadata=metadata)

    def learn_from_intent(self, user_id: str, intent: TravelIntent):
        updates = {}
        if intent.slots.budget:
            updates["max_hotel_budget_per_night"] = intent.slots.budget
        if intent.slots.ride_type:
            updates["preferred_ride_type"] = intent.slots.ride_type
        if intent.slots.amenities:
            current_prefs = self.preferences.get_preferences(user_id)
            combined = list(set(current_prefs.preferred_amenities + intent.slots.amenities))
            updates["preferred_amenities"] = combined

        if updates:
            self.preferences.update_preferences(user_id, updates)

    def get_context(self, user_id: str, session_id: str, query: str) -> Dict[str, Any]:
        prefs = self.preferences.get_preferences(user_id)
        history = self.episodic.get_history(session_id, limit=5)
        facts = self.semantic.search(query, top_k=3)

        return {
            "preferences": prefs,
            "conversation_history": history,
            "relevant_knowledge": facts
        }

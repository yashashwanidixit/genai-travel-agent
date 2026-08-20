from typing import Dict, Any, Optional
from app.memory.episodic import EpisodicMemory
from app.memory.semantic import SemanticMemory
from app.memory.preferences import PreferenceStore
from app.models.user import UserPreferences


class MemoryRetriever:
    """Unified hybrid retrieval interface over episodic, semantic, and preference memory."""

    def __init__(
        self,
        episodic: Optional[EpisodicMemory] = None,
        semantic: Optional[SemanticMemory] = None,
        preferences: Optional[PreferenceStore] = None,
    ):
        self.episodic = episodic or EpisodicMemory()
        self.semantic = semantic or SemanticMemory()
        self.preferences = preferences or PreferenceStore()

    def get_full_context(self, user_id: str, session_id: str, query: str) -> Dict[str, Any]:
        prefs = self.preferences.get_preferences(user_id)
        history = self.episodic.get_history(session_id, limit=5)
        semantic_facts = self.semantic.search(query, top_k=3)

        return {
            "user_id": user_id,
            "session_id": session_id,
            "preferences": prefs.model_dump(),
            "recent_turns": [turn.model_dump() for turn in history],
            "relevant_facts": semantic_facts,
        }

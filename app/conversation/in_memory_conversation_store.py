from __future__ import annotations

from typing import Any


class InMemoryConversationStore:
    """
    Temporary in-memory storage for conversation state.

    Maps a user_id to that user's ConversationManager.

    This is intentionally an in-memory implementation for now.
    A persistent/session-backed implementation can replace this later.
    """

    def __init__(self) -> None:
        self._conversations: dict[str, Any] = {}

    def get(self, user_id: str) -> Any | None:
        """
        Return the existing conversation for this user.

        Returns None if this user has no active conversation.
        """

        return self._conversations.get(user_id)

    def save(self, user_id: str, conversation: Any) -> None:
        """
        Store the conversation for this user.
        """

        self._conversations[user_id] = conversation

    def remove(self, user_id: str) -> None:
        """
        Remove the user's conversation state.
        """

        self._conversations.pop(user_id, None)
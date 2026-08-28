from __future__ import annotations

from typing import Any


class InMemoryConversationStore:
    """
    Stores active ConversationManager instances by user_id.

    Temporary implementation for the current backend/demo.

    Later this can be replaced by a persistent/session-backed
    conversation store without changing ConversationHandler.
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
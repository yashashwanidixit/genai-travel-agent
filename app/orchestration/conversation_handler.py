from __future__ import annotations

from app.agents.intent_agent import IntentAgent
from app.models.conversation_response import ConversationResponse
from app.models.intent import IntentCategory

from app.preferences.preference_extractor import (
    extract_preferences,
)

from app.profiles.in_memory_profile_repository import (
    InMemoryProfileRepository,
)

from app.providers.hotels.base import HotelProvider

from app.orchestration.hotel_recommendation_flow import (
    recommend_hotels,
)


class ConversationHandler:
    """
    Application-level coordinator for one conversation turn.

    The handler connects:

        user message
            ↓
        conversation state
            ↓
        intent parsing
            ↓
        user profile
            ↓
        recommendation pipeline

    It does NOT contain recommendation logic itself.
    """

    def __init__(
        self,
        intent_agent: IntentAgent,
        profile_repository: InMemoryProfileRepository,
        hotel_provider: HotelProvider,
        conversation_store,
        location_resolver,
        routing_service,
    ) -> None:

        self.intent_agent = intent_agent
        self.profile_repository = profile_repository
        self.hotel_provider = hotel_provider
        self.conversation_store = conversation_store

        self.location_resolver = location_resolver
        self.routing_service = routing_service

    def handle_message(
        self,
        user_id: str,
        message: str,
    ) -> ConversationResponse:

        # --------------------------------------------------------
        # 1. Get the user's profile
        # --------------------------------------------------------

        profile = self.profile_repository.get_profile(user_id)

        # --------------------------------------------------------
        # 2. Get this user's existing conversation state
        # --------------------------------------------------------

        conversation = self.conversation_store.get(user_id)

        # --------------------------------------------------------
        # 3. If there is already a pending conversation,
        #    provide the new message as the answer.
        # --------------------------------------------------------

        if conversation is not None and conversation.has_pending():

            intent = conversation.provide_answer(message)

        else:

            # ----------------------------------------------------
            # 4. New conversation
            # ----------------------------------------------------

            intent = self.intent_agent.parse(message)

            conversation = self._create_conversation_manager()

            intent = conversation.start_new_intent(intent)

        # --------------------------------------------------------
        # 5. Save the conversation state
        # --------------------------------------------------------

        self.conversation_store.save(
            user_id,
            conversation,
        )

        # --------------------------------------------------------
        # 6. Is more information required?
        # --------------------------------------------------------

        question = conversation.current_question()

        if question is not None:

            return ConversationResponse(
                status="NEEDS_INPUT",
                question=question,
            )

        # --------------------------------------------------------
        # 7. Conversation is ready
        # --------------------------------------------------------

        if intent.primary_category != IntentCategory.HOTEL_SEARCH:

            return ConversationResponse(
                status="READY",
                message="Request is ready but is not a hotel search.",
            )

        # --------------------------------------------------------
        # 8. Extract soft preferences from this message
        # --------------------------------------------------------

        preferences = extract_preferences(message)

        # --------------------------------------------------------
        # 9. Run the recommendation pipeline
        # --------------------------------------------------------

        hotel_contexts = recommend_hotels(
            intent=intent,
            preferences=preferences,
            profile=profile,
            hotel_provider=self.hotel_provider,
            location_resolver=self.location_resolver,
            routing_service=self.routing_service,
        )

        # --------------------------------------------------------
        # 10. Return structured result
        # --------------------------------------------------------

        return ConversationResponse(
            status="READY",
            hotel_contexts=hotel_contexts,
        )

    def _create_conversation_manager(self):
        """
        Create a new ConversationManager.

        Replace this with your actual ConversationManager
        constructor once we wire its exact dependencies.
        """

        from app.orchestration.conversation_manager import (
            ConversationManager,
        )

        return ConversationManager()
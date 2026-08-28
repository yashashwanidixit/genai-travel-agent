from __future__ import annotations

from app.agents.intent_agent import IntentAgent

from app.models.conversation_response import ConversationResponse
from app.models.intent import IntentCategory, TravelIntent

from app.preferences.preference_extractor import extract_preferences

from app.profiles.in_memory_profile_repository import (
    InMemoryProfileRepository,
)

from app.providers.hotels.base import HotelProvider

from app.orchestration.conversation_manager import ConversationManager

from app.orchestration.hotel_recommendation_flow import (
    recommend_hotels,
)

from app.services.location_resolver import LocationResolver
from app.services.routing.distance_calculator import (
    HaversineDistanceCalculator,
)

from app.conversation.in_memory_conversation_store import (
    InMemoryConversationStore,
)


class ConversationHandler:

    def __init__(
        self,
        intent_agent: IntentAgent,
        profile_repository: InMemoryProfileRepository,
        conversation_store: InMemoryConversationStore,
        hotel_provider: HotelProvider,
        location_resolver: LocationResolver,
        routing_service: HaversineDistanceCalculator,
    ) -> None:

        self.intent_agent = intent_agent
        self.profile_repository = profile_repository
        self.conversation_store = conversation_store
        self.hotel_provider = hotel_provider
        self.location_resolver = location_resolver
        self.routing_service = routing_service

    def handle_message(
        self,
        user_id: str,
        message: str,
    ) -> ConversationResponse:

        # =========================================================
        # 1. Get the user's profile
        # =========================================================

        profile = self.profile_repository.get_profile(user_id)

        # =========================================================
        # 2. Get any existing conversation for this user
        # =========================================================

        conversation = self.conversation_store.get(user_id)

        # =========================================================
        # 3. EXISTING PENDING CONVERSATION
        # =========================================================

        if conversation is not None and conversation.has_pending():

            # The new message is an answer to the
            # clarification question.
            intent = conversation.provide_answer(message)

            # -----------------------------------------------------
            # Still missing information
            # -----------------------------------------------------

            question = conversation.current_question()

            if question is not None:

                # Keep the ConversationManager stored because
                # we still need it for the next user message.
                self.conversation_store.save(
                    user_id,
                    conversation,
                )

                return ConversationResponse(
                    status="NEEDS_INPUT",
                    question=question,
                )

            # -----------------------------------------------------
            # Conversation is now complete
            # -----------------------------------------------------

            self.conversation_store.remove(user_id)

            return self._process_ready_intent(
                intent=intent,
                profile=profile,
                message=message,
            )

        # =========================================================
        # 4. BRAND-NEW REQUEST
        # =========================================================

        preferences = extract_preferences(message)

        raw_intent = self.intent_agent.parse(message)

        conversation = ConversationManager()

        intent = conversation.start_new_intent(raw_intent)

        # =========================================================
        # 5. Check whether clarification is required
        # =========================================================

        question = conversation.current_question()

        if question is not None:

            # Store this ConversationManager so that the user's
            # next message can continue this conversation.
            self.conversation_store.save(
                user_id,
                conversation,
            )

            return ConversationResponse(
                status="NEEDS_INPUT",
                question=question,
            )

        # =========================================================
        # 6. Request is already complete
        # =========================================================

        return self._process_ready_intent(
            intent=intent,
            profile=profile,
            message=message,
            preferences=preferences,
        )

    def _process_ready_intent(
        self,
        intent: TravelIntent,
        profile,
        message: str,
        preferences=None,
    ) -> ConversationResponse:

        # =========================================================
        # 1. Extract preferences if this message was a
        #    clarification answer.
        # =========================================================

        if preferences is None:
            preferences = extract_preferences(message)

        # =========================================================
        # 2. Handle non-hotel requests
        # =========================================================

        if intent.primary_category != IntentCategory.HOTEL_SEARCH:

            return ConversationResponse(
                status="READY",
                message=(
                    "The request is ready, but hotel recommendation "
                    "is not applicable to this request."
                ),
            )

        # =========================================================
        # 3. Run hotel recommendation pipeline
        # =========================================================

        recommendations = recommend_hotels(
            intent=intent,
            preferences=preferences,
            profile=profile,
            hotel_provider=self.hotel_provider,
            location_resolver=self.location_resolver,
            routing_service=self.routing_service,
        )

        # =========================================================
        # 4. Return recommendation response
        # =========================================================

        return ConversationResponse(
            status="READY",
            hotel_contexts=recommendations,
        )
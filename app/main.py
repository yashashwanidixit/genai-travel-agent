from __future__ import annotations

from app.agents.intent_agent import IntentAgent
from app.llm.ollama_provider import OllamaProvider

from app.profiles.in_memory_profile_repository import (
    InMemoryProfileRepository,
)

from app.providers.hotels.mock import MockHotelProvider

from app.services.location_resolver import LocationResolver
from app.services.routing.distance_calculator import (
    HaversineDistanceCalculator,
)

from app.conversation.in_memory_conversation_store import (
    InMemoryConversationStore,
)

from app.orchestration.conversation_handler import (
    ConversationHandler,
)

from app.interfaces.cli_response_printer import (
    print_conversation_response,
)


USER_ID = "A"


def main() -> None:

    print("Travel Agent")
    print("Type 'exit' to quit.\n")

    # ============================================================
    # DEPENDENCIES
    # ============================================================

    llm_provider = OllamaProvider()

    intent_agent = IntentAgent(
        llm_provider
    )

    profile_repository = (
        InMemoryProfileRepository()
    )

    hotel_provider = MockHotelProvider()

    location_resolver = LocationResolver()

    routing_service = (
        HaversineDistanceCalculator()
    )

    conversation_store = (
        InMemoryConversationStore()
    )

    # ============================================================
    # APPLICATION HANDLER
    # ============================================================

    conversation_handler = ConversationHandler(
        intent_agent=intent_agent,
        profile_repository=profile_repository,
        hotel_provider=hotel_provider,
        conversation_store=conversation_store,
        location_resolver=location_resolver,
        routing_service=routing_service,
    )

    # ============================================================
    # CLI LOOP
    # ============================================================

    while True:

        try:
            user_text = input("You:\n").strip()

        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not user_text:
            continue

        if user_text.lower() in {
            "exit",
            "quit",
        }:
            print("Exiting.")
            break

        try:

            response = (
                conversation_handler.handle_message(
                    user_id=USER_ID,
                    message=user_text,
                )
            )

            print_conversation_response(
                response
            )

        except Exception as exc:

            print(
                f"\nError processing request: {exc}\n"
            )


if __name__ == "__main__":
    main()
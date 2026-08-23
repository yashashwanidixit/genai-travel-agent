from __future__ import annotations

from app.agents.intent_agent import IntentAgent, IntentParsingError
from app.llm.ollama_provider import OllamaProvider
from app.models.hotel import Hotel
from app.models.intent import IntentCategory, TravelIntent
from app.orchestration.conversation_manager import ConversationManager
from app.orchestration.hotel_search_flow import maybe_search_hotels


def _print_ollama_config(provider: OllamaProvider) -> None:
    print("\n[Ollama] Connected")
    print(f"[Ollama] Model: {provider.model}")
    print(f"[Ollama] Keep alive: {provider.keep_alive}")
    print(f"[Ollama] CPU threads: {provider.num_thread}\n")


def _print_slots(intent: TravelIntent) -> None:
    populated = {
        key: value
        for key, value in intent.slots.model_dump().items()
        if value is not None
    }
    if not populated:
        print("(none)")
        return
    for key, value in populated.items():
        print(f"{key}: {value}")


def _status_label(intent: TravelIntent) -> str:
    if intent.primary_category == IntentCategory.HOTEL_SEARCH:
        return "READY FOR HOTEL SEARCH"
    if intent.primary_category == IntentCategory.RIDE_SEARCH:
        return "READY FOR RIDE SEARCH"
    return "READY"


def _print_hotels(hotels: list[Hotel]) -> None:
    """Prints Stage 2A results. This is display-only - no filtering,
    no ranking, no scoring happens here or anywhere upstream of it.
    """
    if not hotels:
        print("\nHotels found:\nNone matched this location in the mock dataset.\n")
        return

    print("\nHotels found:\n")
    for index, hotel in enumerate(hotels, start=1):
        print(f"{index}. {hotel.name}")
        print(f"   Rating: {hotel.user_rating}")
        print(f"   Price: ₹{hotel.price_per_night:.0f}/night")
    print()


def _print_ready(intent: TravelIntent, updated: bool) -> None:
    print("\nUpdated intent:" if updated else "\nIntent:")
    print(f"\ncategory:\n{intent.primary_category.value}\n")
    print("Slots:")
    _print_slots(intent)
    print(f"\nMissing:\n{intent.missing_slots}")
    print(f"\nStatus:\n{_status_label(intent)}\n")

    # Stage 2A integration: only runs for a ready hotel_search intent.
    # maybe_search_hotels() itself enforces this gate, but the check
    # is repeated here so we only print the query/results section for
    # hotel searches, not ride searches.
    if intent.primary_category == IntentCategory.HOTEL_SEARCH:
        hotels = maybe_search_hotels(intent)
        if hotels is not None:
            print("Hotel Search Query:")
            location = intent.slots.destination or intent.slots.meeting_location
            print(f"location: {location}")
            print(f"adults: {intent.slots.number_of_adults or 1}")
            print(f"children: {intent.slots.number_of_children or 0}")
            print(f"rooms: {intent.slots.number_of_rooms or 1}")
            _print_hotels(hotels)


def _print_missing(intent: TravelIntent, question: str, updated: bool) -> None:
    print("\nUpdated intent:" if updated else "\nIntent:")
    print(f"\ncategory:\n{intent.primary_category.value}\n")
    print("Slots:")
    _print_slots(intent)
    print("\nMissing required information:")
    for slot in intent.missing_slots:
        print(slot)
    print(f"\nQuestion:\n{question}\n")


def main() -> None:
    print("Travel Agent — Stage 1")
    print("Type 'exit' to quit.\n")

    llm_provider = OllamaProvider()
    agent = IntentAgent(llm_provider)
    conversation = ConversationManager()

    while True:
        try:
            user_text = input("You:\n").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not user_text:
            continue
        if user_text.lower() in {"exit", "quit"}:
            print("Exiting.")
            break

        if conversation.has_pending():
            intent = conversation.provide_answer(user_text)
            question = conversation.current_question()
            if question is not None:
                _print_missing(intent, question, updated=True)
            else:
                _print_ready(intent, updated=True)
            continue

        _print_ollama_config(llm_provider)

        try:
            raw_intent = agent.parse(user_text)
        except IntentParsingError as exc:
            print(f"\nCould not understand that request: {exc}\n")
            continue
        except RuntimeError as exc:
            print("\n[Ollama] ERROR")
            print(f"LLM error: {exc}\n")
            continue

        intent = conversation.start_new_intent(raw_intent)
        question = conversation.current_question()
        
        if question is not None:
            _print_missing(intent, question, updated=False)
        else:
            _print_slots(intent)
            _print_ready(intent, updated=False)


if __name__ == "__main__":
    main()
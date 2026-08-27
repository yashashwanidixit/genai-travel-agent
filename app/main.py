from __future__ import annotations

from app.agents.intent_agent import IntentAgent, IntentParsingError
from app.llm.ollama_provider import OllamaProvider
from app.models.hotel import Hotel
from app.models.intent import IntentCategory, TravelIntent
from app.orchestration.conversation_manager import ConversationManager
from app.orchestration.hotel_search_flow import maybe_search_hotels
from app.validation.intent_validator import validate_destination
from app.services.location_resolver import LocationResolver
from app.services.routing.distance_calculator import (
    HaversineDistanceCalculator,
)
from app.orchestration.hotel_context_flow import build_hotel_contexts
from app.constraints.hotel import filter_hotel_contexts
from app.recommendation.feature_extraction import extract_features
from app.recommendation.utility_calculation import calculate_utilities
from app.preferences.preference_extractor import extract_preferences
from app.recommendation.effective_preferences import (
    resolve_effective_preferences,
)
from app.preferences.preference_extractor import ExtractedPreferences
from app.recommendation.score_calculation import calculate_score
from app.recommendation.user_profile import USER_PROFILE_A
from app.recommendation.effective_preferences import (
    resolve_effective_preferences,
)
from app.recommendation.distance_candidate_selection import select_distance_candidates
from app.orchestration.reference_location_resolver import resolve_distance_threshold



from app.recommendation.user_profile import USER_PROFILE_A



location_resolver = LocationResolver()
routing_service = HaversineDistanceCalculator()


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
        preferences = ExtractedPreferences(
            target_price=intent.target_price,
            target_rating=intent.target_rating,
           
        )

        effective_preferences = resolve_effective_preferences(
            profile=USER_PROFILE_A,
            preferences=preferences,
        )
        
        print(f"effective preferences: {effective_preferences}")
        

        if hotels is not None:
            
            hotel_contexts = build_hotel_contexts(
                intent=intent,
                hotels=hotels,
                location_resolver=location_resolver,
                routing_service=routing_service,
            )
            filtered_contexts = filter_hotel_contexts(
                hotel_contexts=hotel_contexts,
                intent=intent,
            )
            distance_threshold = resolve_distance_threshold(intent)
            final_contexts = select_distance_candidates(filtered_contexts,distance_threshold)
          
            for context in final_contexts:
                features = extract_features(context)

                utilities = calculate_utilities(
                    features,
                    effective_preferences,
                )

                context.price_utility = utilities.price_utility
                context.rating_utility = utilities.rating_utility
                
                score = calculate_score(
                    utilities,
                    USER_PROFILE_A,
                )

                context.final_score = score.final_score
            

            print("Hotel Search Query:")
            location = (
                intent.slots.destination
                or intent.slots.meeting_location
            )

            print(f"location: {location}")
            print(f"adults: {intent.slots.number_of_adults or 1}")
            print(f"children: {intent.slots.number_of_children or 0}")
            print(f"rooms: {intent.slots.number_of_rooms or 1}")

            _print_hotels(hotels)
            

            print("\nHotel Contexts:")
            for context in filtered_contexts:
                hotel = context.hotel

                print(f"{hotel.name}")

                if context.distance_km is not None:
                    print(
                        f"   Distance: "
                        f"{context.distance_km:.2f} km"
                    )
                else:
                    print("   Distance: meeting location not provided defaulting to whole destination.")
                print(
                f"   Price utility: "
                f"{context.price_utility:.4f}"
                if context.price_utility is not None
                else "   Price utility: None"
            )

                print(
                    f"   Rating utility: "
                    f"{context.rating_utility:.4f}"
                    if context.rating_utility is not None
                    else "   Rating utility: None"
                )

                
                print(
                    f"   Final score: "
                    f"{context.final_score:.4f}"
                    if context.final_score is not None
                    else "   Final score: None"
                ) 
        
        


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
            validated_intent = validate_destination(raw_intent)
         
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
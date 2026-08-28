from __future__ import annotations

from app.models.intent import TravelIntent
from app.models.hotel_context import HotelContext
from app.providers.hotels.base import HotelProvider
from app.preferences.preference_extractor import ExtractedPreferences
from app.recommendation.user_profile import UserProfile

from app.orchestration.hotel_search_flow import maybe_search_hotels
from app.orchestration.hotel_context_flow import build_hotel_contexts
from app.constraints.hotel import filter_hotel_contexts
from app.orchestration.reference_location_resolver import (
    resolve_distance_threshold,
)
from app.recommendation.distance_candidate_selection import (
    select_distance_candidates,
)
from app.recommendation.feature_extraction import extract_features
from app.recommendation.utility_calculation import calculate_utilities
from app.recommendation.effective_preferences import (
    resolve_effective_preferences,
)

def recommend_hotels(
    intent: TravelIntent,
    preferences: ExtractedPreferences,
    profile: UserProfile,
    hotel_provider: HotelProvider,
    location_resolver,
    routing_service,
) -> list[HotelContext]:

    hotels = maybe_search_hotels(
        profile,
        intent=intent,
        provider=hotel_provider,
    )

    if hotels is None:
        return []

    effective_preferences = resolve_effective_preferences(
        profile=profile,
        preferences=preferences,
    )

    hotel_contexts = build_hotel_contexts(
        intent=intent,
        hotels=hotels,
        location_resolver=location_resolver,
        routing_service=routing_service,
    )

    filtered_contexts = filter_hotel_contexts(
        hotel_contexts=hotel_contexts,
        intent=intent,
        profile=profile,
    )

    distance_threshold = resolve_distance_threshold(
        intent,
        profile,
    )

    candidate_contexts = select_distance_candidates(
        filtered_contexts,
        distance_threshold,
    )

    for context in candidate_contexts:

        features = extract_features(context)

        utilities = calculate_utilities(
            features,
            effective_preferences,
        )

        context.price_utility = utilities.price_utility
        context.rating_utility = utilities.rating_utility

    return rank_hotel_contexts(
        candidate_contexts,
        profile,
    )
    
def rank_hotel_contexts(
    candidate_contexts: list[HotelContext],
    profile: UserProfile,
) -> list[HotelContext]:

    if profile.ranking_preference == "rating":
        
        return sorted(
            candidate_contexts,
            key=lambda context: context.rating_utility or 0.0,
            reverse=True,
        )

    if profile.ranking_preference == "price":
        return sorted(
            candidate_contexts,
            key=lambda context: context.hotel.price_per_night,
        )

    if profile.ranking_preference == "distance":

        # If distance is unavailable for all hotels,
        # preserve the existing order.
        if all(
            context.distance_km is None
            for context in candidate_contexts
        ):
            return candidate_contexts

        return sorted(
            candidate_contexts,
            key=lambda context: (
                context.distance_km
                if context.distance_km is not None
                else float("inf")
            ),
        )

    raise ValueError(
        f"Unknown ranking preference: "
        f"{profile.ranking_preference}"
    )
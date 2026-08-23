"""Connects the Stage 1 output (a ready TravelIntent) to the Stage 2A
mock hotel retrieval layer.

This module is intentionally separate from main.py so it can be
unit/integration tested without needing a running CLI or user input.
It contains NO business logic of its own - it only wires together two
already-working pieces:

    TravelIntent -> hotel_search_adapter -> HotelSearchQuery
    HotelSearchQuery -> MockHotelProvider -> Hotel[]

Deliberately out of scope here (see project architecture notes):
hard constraint filtering, recommendation/ranking, user memory,
Appium, real API search. This stops at Hotel[].
"""

from __future__ import annotations

from typing import List, Optional

from app.models.hotel import Hotel
from app.models.intent import IntentCategory, TravelIntent
from app.orchestration.hotel_query_adapter import travel_intent_to_hotel_search_query
from app.providers.hotels.base import HotelProvider
from app.providers.hotels.mock import MockHotelProvider

# A single shared default provider instance. Callers (e.g. main.py)
# can still pass their own HotelProvider - the function depends on the
# HotelProvider abstraction, not on MockHotelProvider directly, so
# swapping in a future APIHotelProvider/AppiumHotelProvider requires
# no change here.
_DEFAULT_PROVIDER: HotelProvider = MockHotelProvider()


def maybe_search_hotels(
    intent: TravelIntent, provider: Optional[HotelProvider] = None
) -> Optional[List[Hotel]]:
    """Runs the hotel search ONLY if the intent is a ready hotel_search.

    Returns None (and does nothing) if:
    - the category is not hotel_search (e.g. it's a ride_search - a
      ride request must never trigger hotel retrieval)
    - the intent still has missing_slots (still waiting on the user)

    This is the single gate that enforces "never call the LLM to
    invent hotels, and never search before the user has actually
    provided what's required."
    """
    if intent.primary_category != IntentCategory.HOTEL_SEARCH:
        return None

    if intent.missing_slots:
        return None

    active_provider = provider or _DEFAULT_PROVIDER

    query = travel_intent_to_hotel_search_query(intent)
    return active_provider.search(query)
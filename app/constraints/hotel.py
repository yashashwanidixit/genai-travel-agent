"""ConstraintEngine for hotels (Stage 2B).

Takes hotels already retrieved by a HotelProvider (Stage 2A) and the
TravelIntent that produced the original search, and returns only the
hotels that satisfy the user's EXPLICIT hard constraints.

This is a FILTER, not a recommender:
- It never ranks or scores hotels.
- It never relaxes a constraint the user stated.
- It never picks a "closest" hotel when nothing qualifies - it
  returns an empty list instead.

Two constraints are implemented here on purpose (see project spec):
    minimum_hotel_rating -> Hotel.user_rating (NOT star_rating)
    max_hotel_price      -> Hotel.price_per_night

Both use inclusive boundaries: a hotel exactly at the threshold
passes. Only a hotel below the minimum or above the maximum is
removed.

Deliberately NOT implemented here: star filtering, amenities,
distance, room preference, soft preferences, user memory, ranking,
scoring, or fallback logic. Those belong to later stages.
"""

from __future__ import annotations

from typing import List

from app.models.hotel import Hotel
from app.models.intent import TravelIntent
from app.models.hotel_context import HotelContext


def _passes_rating_constraint(hotel: Hotel, minimum_hotel_rating: float | None) -> bool:
    # None means the user gave no explicit rating floor for this
    # search, so the constraint simply does not apply - every hotel
    # passes this particular check.
    if minimum_hotel_rating is None:
        return True
    # Inclusive boundary: a hotel exactly at the user's stated minimum
    # is what they asked for, not a hotel below it.
    return hotel.user_rating >= minimum_hotel_rating


def _passes_price_constraint(hotel: Hotel, max_hotel_price: float | None) -> bool:
    if max_hotel_price is None:
        return True
    # Inclusive boundary: a hotel priced exactly at the user's stated
    # budget is still within budget.
    return hotel.price_per_night <= max_hotel_price


def filter_hotels(hotels: List[Hotel], intent: TravelIntent) -> List[Hotel]:
    """Returns only the hotels that satisfy ALL active hard constraints
    extracted in the given TravelIntent.

    A hotel must pass every active constraint to be included. If a
    constraint field is None, that constraint is simply not applied -
    it does not mean "reject everything" or "accept everything
    regardless of the other constraint."

    Input hotels are never mutated; a new list is returned. If no
    hotel satisfies the active constraints, [] is returned - this is
    a valid, expected result and must not be treated as an error or
    silently worked around.
    """
    minimum_hotel_rating = intent.slots.minimum_hotel_rating
    max_hotel_price = intent.slots.max_hotel_price

    eligible: List[Hotel] = []
    for hotel in hotels:
        if _passes_rating_constraint(
            hotel, minimum_hotel_rating
        ) and _passes_price_constraint(hotel, max_hotel_price):
            eligible.append(hotel)

    return eligible


def filter_hotel_contexts(
    hotel_contexts: list[HotelContext],
    intent: TravelIntent,
) -> list[HotelContext]:
    """Apply explicit hard constraints to hotel contexts.

    Supported hard constraints:
        - maximum hotel price
        - minimum hotel rating
        - maximum hotel distance

    This function ONLY filters.

    It does not:
        - calculate distance
        - calculate recommendation scores
        - normalize features
        - apply user-profile weights
        - rank hotels
        - mutate HotelContext or Hotel objects
    """

    eligible: list[HotelContext] = []

    max_price = intent.slots.max_hotel_price
    minimum_rating = intent.slots.minimum_hotel_rating
    max_distance = intent.slots.max_hotel_distance_km

    for context in hotel_contexts:

        hotel = context.hotel

        # ---------------------------------------------------------------
        # HARD PRICE CONSTRAINT
        # ---------------------------------------------------------------

        if (
            max_price is not None
            and hotel.price_per_night > max_price
        ):
            continue

        # ---------------------------------------------------------------
        # HARD RATING CONSTRAINT
        # ---------------------------------------------------------------

        if (
            minimum_rating is not None
            and hotel.user_rating < minimum_rating
        ):
            continue

        # ---------------------------------------------------------------
        # HARD DISTANCE CONSTRAINT
        # ---------------------------------------------------------------

        if max_distance is not None:

            # A distance constraint was explicitly requested, but we
            # don't have a distance to evaluate it against.
            #
            # Do NOT treat None as "passes".
            if context.distance_km is None:
                continue

            if context.distance_km > max_distance:
                continue

        eligible.append(context)

    return eligible
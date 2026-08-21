"""MockHotelProvider: a HotelProvider implementation backed by fake,
deterministic hotel data (data/mock_hotels.py).

This exists so the rest of the architecture (constraint engine,
recommendation engine, CLI) can be developed and tested without a
real hotel source. It intentionally implements nothing beyond
retrieval - see the module docstring on HotelProvider for why hard
filtering does NOT belong here.
"""

from __future__ import annotations

from typing import List, Optional

from app.models.hotel import Hotel
from app.models import HotelSearchQuery
from app.providers.hotels.base import HotelProvider
from data.mock_hotels import MOCK_HOTELS


class MockHotelProvider(HotelProvider):
    def __init__(self, hotels: Optional[List[Hotel]] = None):
        # Defaults to the shared mock dataset, but accepts an override
        # so tests can inject a small controlled dataset if needed.
        self._hotels: List[Hotel] = hotels if hotels is not None else MOCK_HOTELS

    def search(self, query: HotelSearchQuery) -> List[Hotel]:
        """Returns hotels whose city or address match the requested
        location, up to query.limit.

        Location matching is intentionally simple (case-insensitive
        substring containment) - no geocoding, no external APIs, no
        fuzzy scoring. If nothing matches, returns [] rather than
        fabricating results or falling back to another location.

        IMPORTANT: this method does NOT filter by min_stars,
        max_budget_per_night, or required_amenities even though
        HotelSearchQuery carries those fields. That filtering is the
        responsibility of a later Constraint Engine (Stage 2B), kept
        separate so this provider - and any future replacement, like
        an AppiumHotelProvider - stays a pure retrieval component.
        """
        location = query.location.strip().lower()

        matches = [
            hotel
            for hotel in self._hotels
            if location in hotel.address.lower() or location in hotel.city.lower()
        ]

        # Dataset order is fixed (see data/mock_hotels.py), so slicing
        # here is deterministic - no sorting or shuffling.
        return matches[: query.limit]
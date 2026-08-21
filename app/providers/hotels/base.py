from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from app.models.hotel import Hotel
from app.models.hotel import HotelSearchQuery


class HotelProvider(ABC):
    """Abstract contract for anything that can retrieve hotel
    candidates for a HotelSearchQuery.

    MockHotelProvider is the only implementation in Stage 2A. A future
    AppiumHotelProvider will implement this same interface, so nothing
    downstream (constraint engine, recommendation engine) needs to
    change when the mock is swapped for a real source.
    """

    @abstractmethod
    def search(self, query: HotelSearchQuery) -> List[Hotel]:
        """Returns candidate hotels for the given query.

        Implementations must NOT apply hard-requirement filtering
        (rating, price, stars, amenities) here - that responsibility
        belongs to a later Constraint Engine (Stage 2B), so provider
        implementations stay simple and swappable.
        """
        raise NotImplementedError
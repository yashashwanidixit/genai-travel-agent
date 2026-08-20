from abc import ABC, abstractmethod
from typing import List, Optional
from app.models.ride import RideEstimate, RideSearchQuery, RideBookingRequest
from app.models.booking import BookingConfirmation


class BaseRideProvider(ABC):
    """Abstract base class for ride hailing providers."""

    @abstractmethod
    async def get_estimates(self, query: RideSearchQuery) -> List[RideEstimate]:
        """Get price and time estimates across available ride types."""
        pass

    @abstractmethod
    async def book_ride(self, booking_request: RideBookingRequest) -> BookingConfirmation:
        """Book a ride for the specified route and type."""
        pass

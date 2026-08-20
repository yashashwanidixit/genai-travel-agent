from abc import ABC, abstractmethod
from typing import List, Optional
from app.models.hotel import Hotel, HotelSearchQuery, HotelBookingRequest
from app.models.booking import BookingConfirmation


class BaseHotelProvider(ABC):
    """Abstract base class for hotel providers."""

    @abstractmethod
    async def search_hotels(self, query: HotelSearchQuery) -> List[Hotel]:
        """Search for hotels matching query parameters."""
        pass

    @abstractmethod
    async def get_hotel_details(self, hotel_id: str) -> Optional[Hotel]:
        """Retrieve detailed information for a specific hotel."""
        pass

    @abstractmethod
    async def book_hotel(self, booking_request: HotelBookingRequest) -> BookingConfirmation:
        """Execute a hotel booking."""
        pass

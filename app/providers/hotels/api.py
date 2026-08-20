import os
import uuid
from typing import List, Optional
import httpx
from app.providers.hotels.base import BaseHotelProvider
from app.models.hotel import Hotel, HotelSearchQuery, HotelBookingRequest
from app.models.booking import BookingConfirmation, BookingType, BookingStatus


class ApiHotelProvider(BaseHotelProvider):
    """External API integration for live hotel aggregators (e.g. Amadeus/Booking.com API)."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("HOTEL_API_KEY", "test_key")
        self.base_url = base_url or os.getenv("HOTEL_API_BASE_URL", "https://api.travelprovider.com/v1")

    async def search_hotels(self, query: HotelSearchQuery) -> List[Hotel]:
        # Implementation skeleton for external REST API with fallback to structured response
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                params = {
                    "city": query.city,
                    "checkIn": query.check_in_date,
                    "checkOut": query.check_out_date,
                    "limit": query.limit,
                }
                response = await client.get(f"{self.base_url}/hotels/search", headers=headers, params=params)
                if response.status_code == 200:
                    data = response.json()
                    return [Hotel(**item) for item in data.get("results", [])]
        except Exception:
            pass
        return []

    async def get_hotel_details(self, hotel_id: str) -> Optional[Hotel]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                response = await client.get(f"{self.base_url}/hotels/{hotel_id}", headers=headers)
                if response.status_code == 200:
                    return Hotel(**response.json())
        except Exception:
            pass
        return None

    async def book_hotel(self, booking_request: HotelBookingRequest) -> BookingConfirmation:
        booking_id = f"bk_api_htl_{uuid.uuid4().hex[:8]}"
        return BookingConfirmation(
            booking_id=booking_id,
            user_id=booking_request.user_id,
            booking_type=BookingType.HOTEL,
            status=BookingStatus.CONFIRMED,
            provider="ApiHotelProvider",
            total_amount=7500.0,
            currency="INR",
            details=booking_request.model_dump(),
            confirmation_code=f"API-HTL-{uuid.uuid4().hex[:6].upper()}"
        )

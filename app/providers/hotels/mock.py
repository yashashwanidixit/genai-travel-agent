import json
import os
import uuid
from typing import List, Optional
from app.providers.hotels.base import BaseHotelProvider
from app.models.hotel import Hotel, HotelSearchQuery, HotelBookingRequest
from app.models.booking import BookingConfirmation, BookingType, BookingStatus


class MockHotelProvider(BaseHotelProvider):
    """Mock hotel provider that loads hotel data from data/mock_hotels.json."""

    def __init__(self, data_file_path: Optional[str] = None):
        if not data_file_path:
            # Default to data/mock_hotels.json relative to project root
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            data_file_path = os.path.join(base_dir, "data", "mock_hotels.json")
        self.data_file_path = data_file_path
        self._hotels = self._load_data()

    def _load_data(self) -> List[Hotel]:
        if os.path.exists(self.data_file_path):
            with open(self.data_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [Hotel(**h) for h in data]
        return []

    async def search_hotels(self, query: HotelSearchQuery) -> List[Hotel]:
        results = []
        for h in self._hotels:
            if query.city.lower() in h.city.lower():
                if query.min_stars and h.star_rating < query.min_stars:
                    continue
                if query.max_budget_per_night and h.price_per_night > query.max_budget_per_night:
                    continue
                if query.required_amenities:
                    if not all(a in h.amenities for a in query.required_amenities):
                        continue
                results.append(h)
        return results[:query.limit]

    async def get_hotel_details(self, hotel_id: str) -> Optional[Hotel]:
        for h in self._hotels:
            if h.id == hotel_id:
                return h
        return None

    async def book_hotel(self, booking_request: HotelBookingRequest) -> BookingConfirmation:
        hotel = await self.get_hotel_details(booking_request.hotel_id)
        price = hotel.price_per_night if hotel else 5000.0
        booking_id = f"bk_htl_{uuid.uuid4().hex[:8]}"

        return BookingConfirmation(
            booking_id=booking_id,
            user_id=booking_request.user_id,
            booking_type=BookingType.HOTEL,
            status=BookingStatus.CONFIRMED,
            provider="MockHotelProvider",
            total_amount=price,
            currency="INR",
            details={
                "hotel_name": hotel.name if hotel else "Hotel",
                "room_id": booking_request.room_id,
                "check_in": booking_request.check_in_date,
                "check_out": booking_request.check_out_date,
                "guests": booking_request.guests,
            },
            confirmation_code=f"HTL-{uuid.uuid4().hex[:6].upper()}"
        )

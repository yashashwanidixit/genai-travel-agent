from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from app.models.hotel import Hotel, HotelSearchQuery, HotelBookingRequest
from app.models.booking import BookingConfirmation
from app.providers.hotels.mock import MockHotelProvider

router = APIRouter()
provider = MockHotelProvider()


@router.get("/search", response_model=List[Hotel])
async def search_hotels(
    city: str = Query(..., description="Destination city name"),
    min_stars: Optional[int] = Query(None, ge=1, le=5),
    max_budget: Optional[float] = Query(None, ge=0),
    amenities: Optional[List[str]] = Query(None),
    limit: int = Query(10, ge=1, le=50)
):
    """Search available hotels by city, rating, budget, and amenities."""
    search_query = HotelSearchQuery(
        city=city,
        min_stars=min_stars,
        max_budget_per_night=max_budget,
        required_amenities=amenities or [],
        limit=limit
    )
    return await provider.search_hotels(search_query)


@router.get("/{hotel_id}", response_model=Hotel)
async def get_hotel(hotel_id: str):
    """Get detailed hotel metadata and room types."""
    hotel = await provider.get_hotel_details(hotel_id)
    if not hotel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hotel not found")
    return hotel


@router.post("/book", response_model=BookingConfirmation, status_code=status.HTTP_201_CREATED)
async def book_hotel(booking_request: HotelBookingRequest):
    """Execute a hotel booking request."""
    return await provider.book_hotel(booking_request)

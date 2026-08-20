from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from app.models.ride import RideEstimate, RideSearchQuery, RideBookingRequest, RideType
from app.models.booking import BookingConfirmation
from app.providers.rides.mock import MockRideProvider

router = APIRouter()
provider = MockRideProvider()


@router.get("/estimates", response_model=List[RideEstimate])
async def get_estimates(
    pickup: str = Query(..., description="Pickup location"),
    dropoff: str = Query(..., description="Dropoff location"),
    preferred_type: Optional[RideType] = Query(None),
    max_budget: Optional[float] = Query(None)
):
    """Retrieve multi-provider ride estimates with ETA and pricing."""
    query = RideSearchQuery(
        pickup_location=pickup,
        dropoff_location=dropoff,
        preferred_type=preferred_type,
        max_budget=max_budget
    )
    return await provider.get_estimates(query)


@router.post("/book", response_model=BookingConfirmation, status_code=status.HTTP_201_CREATED)
async def book_ride(booking_request: RideBookingRequest):
    """Book a ride option."""
    return await provider.book_ride(booking_request)

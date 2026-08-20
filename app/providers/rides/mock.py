import uuid
from typing import List
from app.providers.rides.base import BaseRideProvider
from app.models.ride import RideEstimate, RideSearchQuery, RideBookingRequest, RideType
from app.models.booking import BookingConfirmation, BookingType, BookingStatus


class MockRideProvider(BaseRideProvider):
    """Mock ride provider simulating Uber, Ola, and Namma Yatri pricing."""

    async def get_estimates(self, query: RideSearchQuery) -> List[RideEstimate]:
        # Simulated distance approx 15 km with 35 mins duration
        estimates = [
            RideEstimate(
                provider="Namma Yatri Mock",
                ride_type=RideType.AUTO,
                estimated_fare=220.0,
                duration_minutes=40,
                distance_km=14.5,
                eta_pickup_minutes=3
            ),
            RideEstimate(
                provider="Uber Mock",
                ride_type=RideType.MINI,
                estimated_fare=340.0,
                duration_minutes=35,
                distance_km=14.5,
                eta_pickup_minutes=4
            ),
            RideEstimate(
                provider="Uber Mock",
                ride_type=RideType.SEDAN,
                estimated_fare=460.0,
                duration_minutes=35,
                distance_km=14.5,
                eta_pickup_minutes=5
            ),
            RideEstimate(
                provider="Ola Mock",
                ride_type=RideType.SUV,
                estimated_fare=680.0,
                duration_minutes=35,
                distance_km=14.5,
                eta_pickup_minutes=7
            ),
            RideEstimate(
                provider="Uber Mock",
                ride_type=RideType.PREMIUM,
                estimated_fare=850.0,
                duration_minutes=35,
                distance_km=14.5,
                eta_pickup_minutes=6
            )
        ]

        if query.preferred_type:
            estimates = [e for e in estimates if e.ride_type == query.preferred_type]
        if query.max_budget:
            estimates = [e for e in estimates if e.estimated_fare <= query.max_budget]

        return estimates

    async def book_ride(self, booking_request: RideBookingRequest) -> BookingConfirmation:
        booking_id = f"bk_ride_{uuid.uuid4().hex[:8]}"
        return BookingConfirmation(
            booking_id=booking_id,
            user_id=booking_request.user_id,
            booking_type=BookingType.RIDE,
            status=BookingStatus.CONFIRMED,
            provider=booking_request.provider,
            total_amount=booking_request.fare,
            currency="INR",
            details={
                "ride_type": booking_request.ride_type.value,
                "pickup": booking_request.pickup_location,
                "dropoff": booking_request.dropoff_location,
                "pickup_time": booking_request.pickup_time,
                "driver_name": "Ramesh Kumar",
                "vehicle_number": "KA 01 MJ 4321"
            },
            confirmation_code=f"RIDE-{uuid.uuid4().hex[:6].upper()}"
        )

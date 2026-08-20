from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class RideType(str, Enum):
    AUTO = "Auto"
    MINI = "Mini"
    SEDAN = "Sedan"
    SUV = "SUV"
    PREMIUM = "Premium"


class RideEstimate(BaseModel):
    provider: str
    ride_type: RideType
    estimated_fare: float
    currency: str = "INR"
    duration_minutes: int
    distance_km: float
    eta_pickup_minutes: int = 5
    score: Optional[float] = None


class RideSearchQuery(BaseModel):
    pickup_location: str
    dropoff_location: str
    preferred_type: Optional[RideType] = None
    max_budget: Optional[float] = None


class RideBookingRequest(BaseModel):
    provider: str
    ride_type: RideType
    user_id: str
    pickup_location: str
    dropoff_location: str
    pickup_time: Optional[str] = "Immediate"
    fare: float

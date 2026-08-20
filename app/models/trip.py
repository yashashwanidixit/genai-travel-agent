from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.hotel import Hotel
from app.models.ride import RideEstimate


class ItineraryItem(BaseModel):
    day: int
    time_slot: str
    activity: str
    location: str
    notes: Optional[str] = None
    estimated_cost: float = 0.0


class TripPlan(BaseModel):
    plan_id: str
    user_id: str
    destination: str
    origin: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    selected_hotel: Optional[Hotel] = None
    recommended_hotels: List[Hotel] = Field(default_factory=list)
    selected_ride: Optional[RideEstimate] = None
    ride_estimates: List[RideEstimate] = Field(default_factory=list)
    itinerary: List[ItineraryItem] = Field(default_factory=list)
    total_estimated_cost: float = 0.0
    reasoning_summary: Optional[str] = None


class TripRequest(BaseModel):
    user_id: str
    query: str
    origin: Optional[str] = None
    destination: Optional[str] = None
    dates: Optional[str] = None
    budget: Optional[float] = None

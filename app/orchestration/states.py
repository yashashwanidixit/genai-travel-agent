from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.models.intent import TravelIntent
from app.models.hotel import Hotel
from app.models.ride import RideEstimate
from app.models.trip import TripPlan


class TravelState(str, Enum):
    IDLE = "IDLE"
    EXTRACTING_INTENT = "EXTRACTING_INTENT"
    SEARCHING_HOTELS = "SEARCHING_HOTELS"
    SEARCHING_RIDES = "SEARCHING_RIDES"
    RANKING_OPTIONS = "RANKING_OPTIONS"
    SYNTHESIZING_PLAN = "SYNTHESIZING_PLAN"
    AWAITING_USER_CONFIRMATION = "AWAITING_USER_CONFIRMATION"
    BOOKING_EXECUTION = "BOOKING_EXECUTION"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class StateContext(BaseModel):
    session_id: str
    user_id: str
    current_state: TravelState = TravelState.IDLE
    raw_query: Optional[str] = None
    intent: Optional[TravelIntent] = None
    candidate_hotels: List[Hotel] = Field(default_factory=list)
    candidate_rides: List[RideEstimate] = Field(default_factory=list)
    generated_plan: Optional[TripPlan] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

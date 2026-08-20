from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class BookingType(str, Enum):
    HOTEL = "hotel"
    RIDE = "ride"
    FULL_TRIP = "full_trip"


class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BookingConfirmation(BaseModel):
    booking_id: str
    user_id: str
    booking_type: BookingType
    status: BookingStatus
    provider: str
    total_amount: float
    currency: str = "INR"
    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    confirmation_code: Optional[str] = None

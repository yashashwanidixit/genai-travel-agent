from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel


class IntentCategory(str, Enum):
    HOTEL_SEARCH = "hotel_search"
    RIDE_SEARCH = "ride_search"


class ExtractedSlots(BaseModel):
    # Common
    origin: Optional[str] = None
    destination: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None

    # Hotel context
    meeting_location: Optional[str] = None

    # Hotel dates
    check_in: Optional[str] = None
    check_out: Optional[str] = None

    # Hotel guests / rooms
    number_of_rooms: Optional[int] = None
    number_of_adults: Optional[int] = None
    number_of_children: Optional[int] = None
    children_ages: Optional[list[int]] = None

    # Explicit hotel constraint for THIS search only.
    # NOT the hotel's actual rating, NOT a learned preference/weight.
    # Represents: "minimum acceptable hotel rating explicitly requested
    # by the user for the current search." Must stay null unless the
    # user gives an explicit numeric (or clearly-implied numeric) floor.
    minimum_hotel_rating: Optional[float] = None

    # Ride-specific
    ride_type: Optional[str] = None


class TravelIntent(BaseModel):
    raw_query: str
    primary_category: IntentCategory
    slots: ExtractedSlots
    missing_slots: list[str]
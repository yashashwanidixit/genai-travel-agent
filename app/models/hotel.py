from typing import List, Optional
from pydantic import BaseModel, Field


class RoomType(BaseModel):
    id: str
    name: str
    price: float
    capacity: int = 2
    free_cancellation: bool = True


class Hotel(BaseModel):
    id: str
    name: str
    city: str
    address: str
    star_rating: int = Field(ge=1, le=5)
    user_rating: float = Field(ge=0.0, le=5.0)
 
    price_per_night: float
    currency: str = "INR"
    
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    room_types: List[RoomType] = Field(default_factory=list)



class HotelSearchQuery(BaseModel):
    location: str

    check_in_date: Optional[str] = None
    check_out_date: Optional[str] = None

    number_of_rooms: int = 1
    number_of_adults: int = 1
    number_of_children: int = 0
    children_ages: List[int] = Field(default_factory=list)

    min_stars: Optional[int] = None
    max_budget_per_night: Optional[float] = None
   

    limit: int = 10


class HotelBookingRequest(BaseModel):
    hotel_id: str
    room_id: str
    user_id: str
    check_in_date: str
    check_out_date: str
    guests: int = 1
    special_requests: Optional[str] = None

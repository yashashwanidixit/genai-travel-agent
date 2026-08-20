from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


class UserPreferences(BaseModel):
    preferred_hotel_stars: int = Field(default=4, ge=1, le=5)
    max_hotel_budget_per_night: float = Field(default=10000.0, ge=0)
    preferred_ride_type: str = Field(default="Sedan")
    preferred_amenities: List[str] = Field(default_factory=lambda: ["Free WiFi", "Swimming Pool"])
    dietary_preferences: List[str] = Field(default_factory=list)
    home_city: str = Field(default="Bengaluru")


class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    phone_number: Optional[str] = None


class UserCreate(UserBase):
    password: str
    preferences: Optional[UserPreferences] = None


class User(UserBase):
    id: str
    is_active: bool = True
    preferences: UserPreferences = Field(default_factory=UserPreferences)

    class Config:
        from_attributes = True

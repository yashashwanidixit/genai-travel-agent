import uuid
from typing import Dict
from fastapi import APIRouter, HTTPException, status
from app.models.user import User, UserCreate, UserPreferences
from app.memory.preferences import PreferenceStore

router = APIRouter()
pref_store = PreferenceStore()

# In-memory user store for rapid development
_users_db: Dict[str, User] = {
    "user_123": User(
        id="user_123",
        username="traveler_alex",
        email="alex@example.com",
        full_name="Alex Mercer",
        preferences=UserPreferences(
            preferred_hotel_stars=5,
            max_hotel_budget_per_night=15000.0,
            preferred_ride_type="Sedan",
            preferred_amenities=["Free WiFi", "Swimming Pool", "Spa"]
        )
    )
}


@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(user_in: UserCreate):
    """Register a new user profile."""
    user_id = f"usr_{uuid.uuid4().hex[:8]}"
    user = User(
        id=user_id,
        username=user_in.username,
        email=user_in.email,
        full_name=user_in.full_name,
        phone_number=user_in.phone_number,
        preferences=user_in.preferences or UserPreferences()
    )
    _users_db[user_id] = user
    return user


@router.get("/{user_id}", response_model=User)
async def get_user(user_id: str):
    """Get user profile by ID."""
    user = _users_db.get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.put("/{user_id}/preferences", response_model=UserPreferences)
async def update_preferences(user_id: str, prefs: UserPreferences):
    """Update user travel preferences."""
    user = _users_db.get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.preferences = prefs
    pref_store.update_preferences(user_id, prefs.model_dump())
    return prefs

from fastapi import APIRouter
from app.api.routes.trips import router as trips_router
from app.api.routes.hotels import router as hotels_router
from app.api.routes.rides import router as rides_router
from app.api.routes.users import router as users_router

api_router = APIRouter()

api_router.include_router(trips_router, prefix="/trips", tags=["Trips"])
api_router.include_router(hotels_router, prefix="/hotels", tags=["Hotels"])
api_router.include_router(rides_router, prefix="/rides", tags=["Rides"])
api_router.include_router(users_router, prefix="/users", tags=["Users"])

__all__ = ["api_router"]

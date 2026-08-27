from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from app.models.hotel import Hotel


class HotelContext(BaseModel):
    """A Hotel together with search-specific contextual information.

    Hotel contains properties that belong to the hotel itself, such as:
        - price
        - user rating
        - latitude
        - longitude

    HotelContext contains properties that depend on the current search
    context, such as the hotel's distance from the user's reference
    location.

    This distinction is important because the same hotel can have a
    different distance depending on the reference location.

    Example:

        Hotel A -> Meeting X = 2.0 km
        Hotel A -> Meeting Y = 7.5 km

    Therefore distance should NOT be stored permanently on Hotel.
    """

    hotel: Hotel

    # Distance from the current reference/meeting location.
    #
    # None means that a reference location was not available or that
    # distance has not been calculated yet.
    distance_km: Optional[float] = None
    price_utility: Optional[float] = None
    rating_utility: Optional[float] = None
    
    final_score: Optional[float] = None
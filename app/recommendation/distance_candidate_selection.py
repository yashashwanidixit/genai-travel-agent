from app.models.hotel_context import HotelContext





def select_distance_candidates(
    hotel_contexts: list[HotelContext],
    distance_threshold: float,
    extra_hotels: int = 3,
) -> list[HotelContext]:
    
    
    
    if not any(
        context.distance_km is not None
        for context in hotel_contexts
    ):
        return hotel_contexts

    hotels_with_distance = [
        context
        for context in hotel_contexts
        if context.distance_km is not None
    ]

    hotels_with_distance.sort(
        key=lambda context: context.distance_km
    )

    within_threshold = [
        context
        for context in hotels_with_distance
        if context.distance_km <= distance_threshold
    ]

    outside_threshold = [
        context
        for context in hotels_with_distance
        if context.distance_km > distance_threshold
    ]

    return within_threshold + outside_threshold[:extra_hotels]
from app.models.hotel_context import HotelContext





def select_distance_candidates(
    hotel_contexts: list[HotelContext],
    distance_threshold: float,
    extra_hotels: int = 3,
) -> list[HotelContext]:

    hotels_with_distance = [
        context
        for context in hotel_contexts
        if context.distance_km is not None
    ]

    # No distance information → don't filter
    if not hotels_with_distance:
        return hotel_contexts

    hotels_with_distance.sort(
        key=lambda context: context.distance_km
    )

    within_threshold = [
        context
        for context in hotels_with_distance
        if context.distance_km <= distance_threshold
    ]

    # If at least one hotel satisfies the threshold:
    # keep all qualifying + 3 nearest alternatives.
    if within_threshold:
        outside_threshold = [
            context
            for context in hotels_with_distance
            if context.distance_km > distance_threshold
        ]

        candidates = (
            within_threshold
            + outside_threshold[:extra_hotels]
        )

    # If NOTHING satisfies the threshold:
    # fall back to the nearest hotels.
    else:
        
        candidates = hotels_with_distance
    

    return candidates
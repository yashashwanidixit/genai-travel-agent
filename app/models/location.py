from pydantic import BaseModel, Field


class ResolvedLocation(BaseModel):
    """A location resolved from a user-provided location name.

    This model represents the geographic form of a location after
    resolution. The original semantic extraction remains in
    TravelIntent.reference_location.

    Example:
        TravelIntent.reference_location = "Bangalore Airport"

        ResolvedLocation(
            name="Bangalore Airport",
            latitude=13.1986,
            longitude=77.7066,
        )

    The resolver is responsible for determining these coordinates.
    This model does not perform geocoding or lookup itself.
    """

    name: str = Field(min_length=1)
    latitude: float
    longitude: float
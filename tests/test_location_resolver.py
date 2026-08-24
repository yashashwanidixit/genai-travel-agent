"""
Unit tests for LocationResolver.

The resolver is responsible ONLY for converting an explicitly provided
meeting-location string into a ResolvedLocation.

These tests intentionally do NOT test:
- TravelIntent parsing
- LLM behavior
- hotel retrieval
- distance calculation
- GraphHopper
- recommendation logic

Those belong to other stages of the architecture.

The tests verify that the resolver:
1. Returns None when no meeting location is provided.
2. Resolves known canonical locations.
3. Resolves supported aliases.
4. Handles capitalization differences.
5. Handles extra/repeated whitespace.
6. Does not confuse destination with meeting_location.
7. Raises an explicit error for unknown locations.
8. Does not silently invent coordinates.
9. Returns a ResolvedLocation object.
10. Does not mutate the input string.
"""

import pytest

from app.models.location import ResolvedLocation
from app.services.location_resolver import (
    LocationResolutionError,
    LocationResolver,
)


@pytest.fixture
def resolver() -> LocationResolver:
    """Provide a fresh LocationResolver for each test."""
    return LocationResolver()


# ============================================================================
# 1. NO MEETING LOCATION
# ============================================================================


def test_none_meeting_location_returns_none(resolver: LocationResolver):
    """
    If the user did not specify a meeting location, there is no reference
    point for distance calculation.

    The resolver must return None rather than guessing from another field
    such as destination.
    """

    result = resolver.resolve(None)

    assert result is None


def test_empty_meeting_location_returns_none(resolver: LocationResolver):
    """
    An empty string contains no usable location information.

    The resolver should treat it as equivalent to no meeting location.
    """

    result = resolver.resolve("")

    assert result is None


def test_whitespace_only_meeting_location_returns_none(
    resolver: LocationResolver,
):
    """
    A string containing only whitespace is not a valid location.
    """

    result = resolver.resolve("   ")

    assert result is None


# ============================================================================
# 2. CANONICAL LOCATION LOOKUP
# ============================================================================


def test_known_google_office_is_resolved(resolver: LocationResolver):
    """
    A canonical location present in the static location table should resolve
    to its predefined coordinates.
    """

    result = resolver.resolve("Google Office Whitefield")

    assert isinstance(result, ResolvedLocation)

    assert result.name == "Google Office Whitefield"
    assert result.latitude == 12.9698
    assert result.longitude == 77.7499


def test_known_itpl_is_resolved(resolver: LocationResolver):
    """
    ITPL is another canonical location in the static location table.
    """

    result = resolver.resolve("ITPL")

    assert isinstance(result, ResolvedLocation)

    assert result.name == "ITPL"
    assert result.latitude == 12.9850
    assert result.longitude == 77.7280


def test_known_bangalore_airport_is_resolved(
    resolver: LocationResolver,
):
    """
    Bangalore Airport should resolve to its predefined coordinates.
    """

    result = resolver.resolve("Bangalore Airport")

    assert isinstance(result, ResolvedLocation)

    assert result.name == "Bangalore Airport"
    assert result.latitude == 13.1986
    assert result.longitude == 77.7066


# ============================================================================
# 3. CASE NORMALIZATION
# ============================================================================


def test_location_lookup_is_case_insensitive(
    resolver: LocationResolver,
):
    """
    Location lookup should not depend on capitalization.

    These should all resolve to the same location:
        Google Office Whitefield
        google office whitefield
        GOOGLE OFFICE WHITEFIELD
    """

    result_lower = resolver.resolve("google office whitefield")
    result_upper = resolver.resolve("GOOGLE OFFICE WHITEFIELD")
    result_mixed = resolver.resolve("GoOgLe OfFiCe WhItEfIeLd")

    assert result_lower is not None
    assert result_upper is not None
    assert result_mixed is not None

    assert result_lower.name == result_upper.name
    assert result_lower.name == result_mixed.name

    assert result_lower.latitude == result_upper.latitude
    assert result_lower.latitude == result_mixed.latitude

    assert result_lower.longitude == result_upper.longitude
    assert result_lower.longitude == result_mixed.longitude


# ============================================================================
# 4. WHITESPACE NORMALIZATION
# ============================================================================


def test_leading_and_trailing_whitespace_is_ignored(
    resolver: LocationResolver,
):
    """
    Leading and trailing whitespace should not affect resolution.
    """

    result = resolver.resolve("   ITPL   ")

    assert result is not None
    assert result.name == "ITPL"


def test_repeated_internal_whitespace_is_ignored(
    resolver: LocationResolver,
):
    """
    Repeated spaces inside a location name should be normalized.

    Example:

        "Google   Office   Whitefield"

    should behave like:

        "Google Office Whitefield"
    """

    result = resolver.resolve("Google   Office   Whitefield")

    assert result is not None
    assert result.name == "Google Office Whitefield"


# ============================================================================
# 5. ALIAS RESOLUTION
# ============================================================================


def test_google_office_alias_is_resolved(
    resolver: LocationResolver,
):
    """
    'Google Office' is an alias for the canonical
    'Google Office Whitefield' location.
    """

    result = resolver.resolve("Google Office")

    assert result is not None

    assert result.name == "Google Office Whitefield"
    assert result.latitude == 12.9698
    assert result.longitude == 77.7499


def test_google_office_in_whitefield_alias_is_resolved(
    resolver: LocationResolver,
):
    """
    A natural variation of the Google Office location should resolve
    through the alias table.
    """

    result = resolver.resolve("Google Office in Whitefield")

    assert result is not None

    assert result.name == "Google Office Whitefield"
    assert result.latitude == 12.9698
    assert result.longitude == 77.7499


def test_itp_alias_is_resolved(
    resolver: LocationResolver,
):
    """
    'International Tech Park' is an alias for ITPL.
    """

    result = resolver.resolve("International Tech Park")

    assert result is not None

    assert result.name == "ITPL"
    assert result.latitude == 12.9850
    assert result.longitude == 77.7280


def test_airport_alias_is_resolved(
    resolver: LocationResolver,
):
    """
    Common airport names should resolve to the canonical
    Bangalore Airport entry.
    """

    result = resolver.resolve("Kempegowda Airport")

    assert result is not None

    assert result.name == "Bangalore Airport"
    assert result.latitude == 13.1986
    assert result.longitude == 77.7066


def test_bengaluru_airport_alias_is_resolved(
    resolver: LocationResolver,
):
    """
    Bengaluru Airport should resolve to the same canonical location
    as Bangalore Airport.
    """

    result = resolver.resolve("Bengaluru Airport")

    assert result is not None

    assert result.name == "Bangalore Airport"
    assert result.latitude == 13.1986
    assert result.longitude == 77.7066


# ============================================================================
# 6. UNKNOWN LOCATIONS
# ============================================================================


def test_unknown_location_raises_resolution_error(
    resolver: LocationResolver,
):
    """
    The resolver must NOT invent coordinates for an unknown location.

    An explicit meeting location that cannot currently be resolved should
    result in LocationResolutionError.
    """

    with pytest.raises(LocationResolutionError):
        resolver.resolve("Some Random Office")


def test_unknown_location_error_contains_location(
    resolver: LocationResolver,
):
    """
    The error should tell us which location could not be resolved.
    """

    location = "Acme Technologies Whitefield"

    with pytest.raises(LocationResolutionError) as exc_info:
        resolver.resolve(location)

    assert location in str(exc_info.value)


def test_similar_but_unknown_location_is_not_fuzzy_matched(
    resolver: LocationResolver,
):
    """
    The current resolver deliberately uses deterministic lookup.

    It must not make up a match simply because an unknown location
    resembles a known location.
    """

    with pytest.raises(LocationResolutionError):
        resolver.resolve("Google Office Somewhere Else")


# ============================================================================
# 7. DESTINATION MUST NOT BE USED AS FALLBACK
# ============================================================================


def test_resolver_does_not_fall_back_to_destination(
    resolver: LocationResolver,
):
    """
    The resolver receives ONLY meeting_location.

    If meeting_location is None, it must return None.

    It must NOT:
        None -> Whitefield
        None -> destination
        None -> any default location

    This protects the architectural distinction between:

        destination      = where the hotel should be
        meeting_location  = where the meeting actually is
    """

    meeting_location = None
    destination = "Whitefield"

    # Destination is intentionally not passed to the resolver.
    result = resolver.resolve(meeting_location)

    assert result is None


# ============================================================================
# 8. RESOLVED OBJECT STRUCTURE
# ============================================================================


def test_resolved_location_contains_coordinates(
    resolver: LocationResolver,
):
    """
    A successful resolution must produce a ResolvedLocation containing
    a name, latitude, and longitude.
    """

    result = resolver.resolve("ITPL")

    assert result is not None

    assert result.name
    assert isinstance(result.latitude, float)
    assert isinstance(result.longitude, float)


def test_resolved_coordinates_are_not_none(
    resolver: LocationResolver,
):
    """
    A successfully resolved location must have actual coordinates.

    The resolver should never return a partially resolved object.
    """

    result = resolver.resolve("Bangalore Airport")

    assert result is not None

    assert result.latitude is not None
    assert result.longitude is not None


# ============================================================================
# 9. INPUT IS NOT MUTATED
# ============================================================================


def test_input_string_is_not_mutated(
    resolver: LocationResolver,
):
    """
    Strings are immutable, but this test documents an important property
    of the resolver:

    Resolution should create a normalized lookup value internally and
    should not alter the caller's original input.
    """

    location = "  Google   Office   "

    original = location

    resolver.resolve(location)

    assert location == original


# ============================================================================
# 10. ALIAS AND CANONICAL LOCATION RETURN SAME COORDINATES
# ============================================================================


def test_alias_and_canonical_location_resolve_to_same_coordinates(
    resolver: LocationResolver,
):
    """
    Different textual representations of the same real-world location
    should ultimately produce identical coordinates.
    """

    canonical = resolver.resolve("Google Office Whitefield")
    alias = resolver.resolve("Google Office")

    assert canonical is not None
    assert alias is not None

    assert canonical.latitude == alias.latitude
    assert canonical.longitude == alias.longitude


# ============================================================================
# 11. RESOLVER DOES NOT CALCULATE DISTANCE
# ============================================================================


def test_resolver_only_resolves_location(
    resolver: LocationResolver,
):
    """
    The output of this stage should be a location with coordinates.

    It should NOT contain:
        distance
        travel time
        hotel information
        recommendation score

    Distance calculation belongs to the later RoutingService stage.
    """

    result = resolver.resolve("ITPL")

    assert result is not None

    assert hasattr(result, "name")
    assert hasattr(result, "latitude")
    assert hasattr(result, "longitude")

    assert not hasattr(result, "distance_km")
    assert not hasattr(result, "travel_time_minutes")
    assert not hasattr(result, "score")
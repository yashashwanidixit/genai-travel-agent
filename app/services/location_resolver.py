from __future__ import annotations

from app.models.location import ResolvedLocation


class LocationResolutionError(Exception):
    """Raised when an explicit meeting location cannot be resolved."""

    pass


# ---------------------------------------------------------------------------
# Static location database
# ---------------------------------------------------------------------------
#
# This is intentionally static for the current stage.
#
# The keys are normalized location names/aliases.
# The values are ResolvedLocation objects containing the coordinates.
#
# Later, this dictionary can be replaced by a real geocoding/location
#grasshopper api will be used 
# service without changing the rest of the application architecture.
# ---------------------------------------------------------------------------

_LOCATION_TABLE: dict[str, ResolvedLocation] = {
    "google office whitefield": ResolvedLocation(
        name="Google Office Whitefield",
        latitude=12.9698,
        longitude=77.7499,
    ),
    "itpl": ResolvedLocation(
        name="ITPL",
        latitude=12.9850,
        longitude=77.7280,
    ),
    "bangalore airport": ResolvedLocation(
        name="Bangalore Airport",
        latitude=13.1986,
        longitude=77.7066,
    ),
}


# ---------------------------------------------------------------------------
# Aliases
# ---------------------------------------------------------------------------
#
# Multiple ways of referring to the same location can be mapped to one
# canonical key in _LOCATION_TABLE.
#
# The alias mechanism is deterministic. It does NOT use semantic matching
# or an LLM.
# ---------------------------------------------------------------------------

_LOCATION_ALIASES: dict[str, str] = {
    "google office": "google office whitefield",
    "google ananta office": "google office whitefield",
    "google office in whitefield": "google office whitefield",
    "google whitefield": "google office whitefield",
    "google whitefield office": "google office whitefield",
    "international tech park": "itpl",
    "international tech park bangalore": "itpl",
    "blr airport": "bangalore airport",
    "bengaluru airport": "bangalore airport",
    "kempegowda airport": "bangalore airport",
    "kempegowda international airport": "bangalore airport",
}


class LocationResolver:
    """Resolve an explicit meeting-location name into coordinates.

    Responsibility:
        meeting_location string
            ->
        ResolvedLocation

    This class does NOT:
    - parse user intent
    - determine whether a location is a meeting location
    - resolve the hotel-search destination
    - calculate distances
    - call an LLM
    - call an external geocoding API
    - modify TravelIntent
    - modify Hotel

    The IntentAgent is responsible for determining that a location is
    actually the meeting_location.

    This resolver only answers:
        "Given this explicit meeting-location string, do we know
         its coordinates?"
    """

    def resolve(
        self,
        meeting_location: str | None,
    ) -> ResolvedLocation | None:
        """Resolve a meeting location.

        Args:
            meeting_location:
                The location explicitly extracted by IntentAgent as the
                user's meeting location.

        Returns:
            ResolvedLocation if the location can be resolved.

            None if meeting_location is None.

        Raises:
            LocationResolutionError:
                If a non-empty meeting location was provided but is not
                present in the current static location database.
        """

        # No meeting location means there is no reference point for
        # distance calculation.
        #
        # IMPORTANT:
        # Do NOT fall back to destination here.
        #
        # Example:
        #   "I want a hotel in Whitefield."
        #
        # destination = "Whitefield"
        # meeting_location = None
        #
        # Therefore:
        #   resolve(None) -> None
        #
        # We must NOT interpret Whitefield as the meeting location.
        if meeting_location is None:
            return None

        normalized = self._normalize(meeting_location)

        # An empty string is treated as no usable meeting location.
        if not normalized:
            return None

        # First check the canonical location table.
        if normalized in _LOCATION_TABLE:
            return _LOCATION_TABLE[normalized]

        # Then check aliases.
        canonical_key = _LOCATION_ALIASES.get(normalized)

        if canonical_key is not None:
            return _LOCATION_TABLE[canonical_key]

        # The user explicitly supplied a meeting location, but the current
        # resolver does not know its coordinates.
        #
        # Do NOT guess coordinates.
        # Do NOT use destination.
        # Do NOT silently use a nearby location.
        raise LocationResolutionError(
            f"Could not resolve meeting location: {meeting_location}"
        )

    @staticmethod
    def _normalize(value: str) -> str:
        """Normalize a location string for deterministic lookup.

        Currently this only performs safe textual normalization:
        - removes leading/trailing whitespace
        - converts to lowercase
        - collapses repeated whitespace

        It deliberately does NOT perform fuzzy or semantic matching.
        """

        return " ".join(value.strip().lower().split())
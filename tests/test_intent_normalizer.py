"""
Deterministic unit tests for app/normalization/intent_normalizer.py.

No Ollama/LLM calls here - pure Python logic tested directly against
hand-built TravelIntent/ExtractedSlots objects.
"""

from app.models.intent import ExtractedSlots, IntentCategory, TravelIntent
from app.normalization.intent_normalizer import normalize_intent, normalize_time


def _make_intent(category: IntentCategory, **slot_values) -> TravelIntent:
    return TravelIntent(
        raw_query="test query",
        primary_category=category,
        slots=ExtractedSlots(**slot_values),
        missing_slots=[],
    )


def test_time_8am_to_24h():
    """"8 AM" must normalize to "08:00"."""
    assert normalize_time("8 AM") == "08:00"


def test_time_8pm_to_24h():
    """"8 PM" must normalize to "20:00"."""
    assert normalize_time("8 PM") == "20:00"


def test_time_830pm_to_24h():
    """"8:30 PM" must normalize to "20:30", preserving minutes."""
    assert normalize_time("8:30 PM") == "20:30"


def test_time_noon_and_midnight_edge_cases():
    """12-hour edge cases: 12 PM = noon, 12 AM = midnight."""
    assert normalize_time("12 PM") == "12:00"
    assert normalize_time("12 AM") == "00:00"


def test_time_lowercase_no_space():
    """"8am" (no space, lowercase) must still normalize correctly."""
    assert normalize_time("8am") == "08:00"


def test_time_already_24h_passthrough():
    """A value already in 24-hour format passes through unchanged."""
    assert normalize_time("08:00") == "08:00"


def test_time_unrecognized_format_not_guessed():
    """An unrecognized expression is left unchanged, never guessed."""
    assert normalize_time("early morning") == "early morning"


def test_time_none_stays_none():
    """None must remain None."""
    assert normalize_time(None) is None


def test_normalize_intent_trims_whitespace_locations():
    """Leading/trailing whitespace on location fields must be trimmed."""
    intent = _make_intent(IntentCategory.HOTEL_SEARCH, destination="  Whitefield  ")
    normalized = normalize_intent(intent)
    assert normalized.slots.destination == "Whitefield"


def test_normalize_intent_ride_type_lowercased():
    """Ride type must normalize to a lowercase canonical value."""
    intent = _make_intent(
        IntentCategory.RIDE_SEARCH,
        origin="Bangalore Airport",
        destination="Whitefield",
        ride_type="BIKE",
    )
    normalized = normalize_intent(intent)
    assert normalized.slots.ride_type == "bike"


def test_normalize_intent_does_not_touch_explicit_rating():
    """An explicit numeric rating must pass through unchanged."""
    intent = _make_intent(
        IntentCategory.HOTEL_SEARCH,
        destination="Whitefield",
        minimum_hotel_rating=4.5,
    )
    normalized = normalize_intent(intent)
    assert normalized.slots.minimum_hotel_rating == 4.5


def test_normalize_intent_vague_rating_stays_none():
    """A None rating (e.g. from "highly rated") must remain None."""
    intent = _make_intent(IntentCategory.HOTEL_SEARCH, destination="Whitefield")
    normalized = normalize_intent(intent)
    assert normalized.slots.minimum_hotel_rating is None


def test_normalize_intent_preserves_relative_date():
    """"tomorrow" must be preserved as-is - relative date resolution
    is out of scope for this stage."""
    intent = _make_intent(
        IntentCategory.RIDE_SEARCH,
        origin="Bangalore Airport",
        destination="Whitefield",
        date="tomorrow",
    )
    normalized = normalize_intent(intent)
    assert normalized.slots.date == "tomorrow"


if __name__ == "__main__":
    import sys
    import pytest

    sys.exit(pytest.main([__file__, "-v"]))
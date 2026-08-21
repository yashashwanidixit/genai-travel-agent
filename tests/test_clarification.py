"""
Deterministic unit tests for app/orchestration/clarification.py.

No Ollama/LLM calls here.
"""

import pytest

from app.models.intent import ExtractedSlots, IntentCategory, TravelIntent
from app.orchestration.clarification import (
    get_clarification_question,
    next_clarification_question,
)
from app.orchestration.requirement_checker import check_requirements


def _make_intent(category: IntentCategory, **slot_values) -> TravelIntent:
    return TravelIntent(
        raw_query="test query",
        primary_category=category,
        slots=ExtractedSlots(**slot_values),
        missing_slots=[],
    )


def test_missing_hotel_destination_generates_correct_question():
    """A missing hotel destination produces the exact hotel-location
    clarification question."""
    intent = check_requirements(_make_intent(IntentCategory.HOTEL_SEARCH))
    assert next_clarification_question(intent) == (
        "Where would you like the hotel to be located?"
    )


def test_missing_ride_origin_generates_correct_question():
    """A missing ride origin (with destination present) produces the
    pickup-location question."""
    intent = check_requirements(
        _make_intent(IntentCategory.RIDE_SEARCH, destination="Whitefield")
    )
    assert next_clarification_question(intent) == "Where should I pick you up from?"


def test_missing_ride_destination_generates_correct_question():
    """A missing ride destination (with origin present) produces the
    drop-off question."""
    intent = check_requirements(
        _make_intent(IntentCategory.RIDE_SEARCH, origin="Bangalore Airport")
    )
    assert next_clarification_question(intent) == "Where are you going?"


def test_ride_missing_both_asks_origin_first():
    """When both are missing, only origin's question is asked first."""
    intent = check_requirements(_make_intent(IntentCategory.RIDE_SEARCH))
    assert next_clarification_question(intent) == "Where should I pick you up from?"


def test_no_question_when_nothing_missing():
    """No clarification question is produced when nothing is missing."""
    intent = check_requirements(
        _make_intent(IntentCategory.HOTEL_SEARCH, destination="Whitefield")
    )
    assert next_clarification_question(intent) is None


def test_unknown_slot_raises_instead_of_generic_question():
    """A slot with no defined question raises rather than falling back
    to a vague generic question."""
    with pytest.raises(ValueError):
        get_clarification_question(IntentCategory.HOTEL_SEARCH, "guests")


if __name__ == "__main__":
    import sys
    import pytest as _pytest

    sys.exit(_pytest.main([__file__, "-v"]))
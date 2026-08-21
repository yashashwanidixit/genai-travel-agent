from __future__ import annotations

from typing import Optional

from app.models.intent import IntentCategory, TravelIntent

# Deterministic (category, missing_slot) -> question mapping. No LLM
# involved. Only fields we have an explicit, unambiguous question for
# are supported - there is no generic fallback question, since a
# question that doesn't identify which field is missing isn't useful.
_CLARIFICATION_QUESTIONS: dict[tuple[IntentCategory, str], str] = {
    (IntentCategory.HOTEL_SEARCH, "destination"): (
        "Where would you like the hotel to be located?"
    ),
    (IntentCategory.RIDE_SEARCH, "origin"): (
        "Where should I pick you up from?"
    ),
    (IntentCategory.RIDE_SEARCH, "destination"): (
        "Where are you going?"
    ),
}


def get_clarification_question(
    category: IntentCategory, missing_slot: str
) -> str:
    key = (category, missing_slot)
    if key not in _CLARIFICATION_QUESTIONS:
        raise ValueError(
            f"No clarification question defined for category="
            f"{category.value!r}, slot={missing_slot!r}"
        )
    return _CLARIFICATION_QUESTIONS[key]


def next_clarification_question(intent: TravelIntent) -> Optional[str]:
    """Returns the question for only the FIRST missing required slot.
    Multiple missing fields are never asked about simultaneously -
    the rest wait for subsequent rounds of the conversation.
    """
    if not intent.missing_slots:
        return None
    first_missing = intent.missing_slots[0]
    return get_clarification_question(intent.primary_category, first_missing)
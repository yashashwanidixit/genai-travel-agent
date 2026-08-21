from __future__ import annotations

from app.models.intent import ExtractedSlots, IntentCategory, TravelIntent

# Hard requirements for the CURRENT Stage 1 operation only. These are
# not "all fields that would be nice to have" - only what blocks the
# next step from proceeding at all.
HOTEL_SEARCH_REQUIRED = ["destination"]
RIDE_SEARCH_REQUIRED = ["origin", "destination"]


def _hotel_missing_slots(slots: ExtractedSlots) -> list[str]:
    missing: list[str] = []
    # A searchable location is required. destination OR
    # meeting_location satisfies it (meeting_location can stand in for
    # a destination), matching the intent-agent behavior this replaces.
    if not slots.destination and not slots.meeting_location:
        missing.append("destination")
    return missing


def _ride_missing_slots(slots: ExtractedSlots) -> list[str]:
    missing: list[str] = []
    if not slots.origin:
        missing.append("origin")
    if not slots.destination:
        missing.append("destination")
    return missing


def compute_missing_slots(intent: TravelIntent) -> list[str]:
    """The single source of truth for which hard-required fields are
    missing for the CURRENT operation. The LLM's own missing_slots
    guess (if any) is never trusted - this function is authoritative.
    """
    if intent.primary_category == IntentCategory.HOTEL_SEARCH:
        return _hotel_missing_slots(intent.slots)
    if intent.primary_category == IntentCategory.RIDE_SEARCH:
        return _ride_missing_slots(intent.slots)
    return []


def check_requirements(intent: TravelIntent) -> TravelIntent:
    """Returns a new TravelIntent with missing_slots overwritten based
    on deterministic hard-requirement logic. Optional fields being
    None (ratings, adults, rooms, etc.) never appear here.
    """
    missing = compute_missing_slots(intent)
    return intent.model_copy(update={"missing_slots": missing})


def is_ready(intent: TravelIntent) -> bool:
    return len(intent.missing_slots) == 0
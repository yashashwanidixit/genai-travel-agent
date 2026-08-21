from __future__ import annotations

import re
from typing import Optional

from app.models.intent import TravelIntent

_12H_PATTERN = re.compile(
    r"^\s*(?P<hour>\d{1,2})(?::(?P<minute>\d{2}))?\s*(?P<meridiem>[AaPp][Mm])\s*$"
)
_24H_PATTERN = re.compile(r"^\s*(?P<hour>\d{1,2}):(?P<minute>\d{2})\s*$")


def normalize_time(value: Optional[str]) -> Optional[str]:
    """Normalizes common 12-hour time expressions ("8 AM", "8:30 PM",
    "12 AM") into 24-hour "HH:MM". Values already in 24-hour format
    pass through (zero-padded). Anything unrecognized is returned
    unchanged rather than guessed at — this must never invent a time.
    Relative dates ("tomorrow") are handled by normalize_intent, not
    here, and are always preserved as-is.
     max_hotel_price is deterministically normalized to a float but is
    never inferred or calculated from other fields.
    """
    if value is None:
        return None

    text = value.strip()
    if not text:
        return value

    match = _12H_PATTERN.match(text)
    if match:
        hour = int(match.group("hour"))
        minute = int(match.group("minute") or 0)
        meridiem = match.group("meridiem").lower()

        if not (1 <= hour <= 12) or not (0 <= minute <= 59):
            return value  # malformed - do not guess

        if meridiem == "am":
            hour_24 = 0 if hour == 12 else hour
        else:
            hour_24 = 12 if hour == 12 else hour + 12

        return f"{hour_24:02d}:{minute:02d}"

    match = _24H_PATTERN.match(text)
    if match:
        hour = int(match.group("hour"))
        minute = int(match.group("minute"))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return f"{hour:02d}:{minute:02d}"
        return value

    # Unrecognized format (e.g. "tomorrow morning") - leave unchanged.
    return value


def normalize_string(value: Optional[str]) -> Optional[str]:
    """Trims whitespace only. Does not alter casing, does not perform
    fuzzy correction, does not geocode.
    """
    if value is None:
        return None
    stripped = value.strip()
    return stripped if stripped else None


def normalize_ride_type(value: Optional[str]) -> Optional[str]:
    """Lowercases and trims ride_type to a canonical form
    ("Bike" / "BIKE" -> "bike"). Does not validate against the known
    set (bike/scooty/auto/cab) - that stays out of scope here.
    """
    if value is None:
        return None
    normalized = value.strip().lower()
    return normalized if normalized else None

def normalize_price(value: Optional[float]) -> Optional[float]:
    """Normalizes an explicitly extracted hotel price.

    Converts the value to a float and ensures it is non-negative.
    Does not infer or calculate prices from other fields.
    Does not convert vague expressions such as 'cheap' or 'affordable'
    into a numeric value.

    Returns None when no price was extracted.
    """
    if value is None:
        return None

    try:
        normalized = float(value)
    except (TypeError, ValueError):
        return value

    if normalized < 0:
        return value

    return normalized


def normalize_intent(intent: TravelIntent) -> TravelIntent:
    """Takes a raw LLM-extracted TravelIntent and returns a new
    TravelIntent with deterministic formatting applied. Never invents
    or discards data — only reformats what is already present.

    minimum_hotel_rating, number_of_rooms, number_of_adults,
    number_of_children, and children_ages are passed through
    unchanged: they are already correctly typed by Pydantic, and their
    *value* (e.g. whether a rating is None or 4.5) is a semantic
    decision that belongs to the LLM extraction step, not this
    deterministic layer.
    """
    slots = intent.slots

    normalized_slots = slots.model_copy(
        update={
            "origin": normalize_string(slots.origin),
            "destination": normalize_string(slots.destination),
            "date": normalize_string(slots.date),
            "time": normalize_time(slots.time),
            "meeting_location": normalize_string(slots.meeting_location),
            "check_in": normalize_string(slots.check_in),
            "check_out": normalize_string(slots.check_out),
            "ride_type": normalize_ride_type(slots.ride_type),
            "max_hotel_price": normalize_price(slots.max_hotel_price),
        }
    )

    return intent.model_copy(update={"slots": normalized_slots})
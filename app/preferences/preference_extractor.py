from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class ExtractedPreferences:
    target_price: float | None = None
    target_rating: float | None = None


PRICE_PATTERNS = [
    (
        re.compile(
            r"\b(?:around|about|approximately|roughly)\s*"
            r"(?:rs\.?|₹)?\s*(\d+(?:\.\d+)?)"
            # Do NOT treat "around 4 rated" as a price.
            r"(?!\s*(?:rated|rating|stars?|star)\b)"
            r"\s*(?:per\s+night|/night|a\s+night|nightly)?\b",
            re.IGNORECASE,
        ),
        "target_price",
    ),
    (
        re.compile(
            r"\b(?:prefer|preferably|ideally)\s+"
            r"(?:a\s+hotel\s+)?"
            r"(?:around\s+|about\s+|approximately\s+|roughly\s+)?"
            r"(?:rs\.?|₹)?\s*(\d+(?:\.\d+)?)"
            # Do NOT treat "prefer around 4 rated" as a price.
            r"(?!\s*(?:rated|rating|stars?|star)\b)"
            r"\s*(?:per\s+night|/night|a\s+night|nightly)?\b",
            re.IGNORECASE,
        ),
        "target_price",
    ),
]

RATING_PATTERNS = [
    (
        re.compile(
            r"\b(?:around|about|approximately|roughly)\s+"
            r"(\d+(?:\.\d+)?)\s*"
            r"(?:rated|rating|stars?|star)\b",
            re.IGNORECASE,
        ),
        "target_rating",
    ),
    (
        re.compile(
            r"\b(?:prefer|preferably|ideally)\s+"
            r"(?:a\s+)?"
            r"(\d+(?:\.\d+)?)\s*"
            r"(?:rated|rating|stars?|star)\b",
            re.IGNORECASE,
        ),
        "target_rating",
    ),
]


def extract_preferences(text: str) -> ExtractedPreferences:
    """
    Deterministically extract soft hotel preferences from the user's
    raw message.

    This function does NOT:
    - call the LLM
    - perform hotel search
    - perform hard filtering
    - calculate utility
    - modify TravelIntent
    """

    preferences = ExtractedPreferences()

    for pattern, field in PRICE_PATTERNS:
        match = pattern.search(text)

        if match:
            value = float(match.group(1))

            if field == "target_price":
                preferences.target_price = value

            break

    for pattern, field in RATING_PATTERNS:
        match = pattern.search(text)

        if match:
            value = float(match.group(1))

            if field == "target_rating":
                preferences.target_rating = value

            break

    return preferences
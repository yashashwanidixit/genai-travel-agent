from __future__ import annotations

import re
from dataclasses import dataclass


# ============================================================
# OUTPUT MODEL
# ============================================================

@dataclass
class ExtractedPreferences:
    target_price: float | None = None
    target_rating: float | None = None
    target_distance: float | None = None


# ============================================================
# SOFT-PREFERENCE LANGUAGE
# ============================================================

SOFT_LANGUAGE_MARKERS = {
    "around",
    "about",
    "approximately",
    "roughly",
    "prefer",
    "preferably",
    "ideally",
}


# ============================================================
# DOMAIN MARKERS
# ============================================================

DISTANCE_UNITS = {
    "km",
    "kms",
    "kilometer",
    "kilometers",
    "kilometre",
    "kilometres",
    "mile",
    "miles",
}


RATING_MARKERS = {
    "rated",
    "rating",
    "star",
    "stars",
}


PRICE_MARKERS = {
    "rs",
    "rs.",
    "rupees",
    "₹",
}


PRICE_PHRASES = {
    "per night",
    "a night",
    "nightly",
    "/night",
}


# ============================================================
# TOKENIZATION
# ============================================================

TOKEN_PATTERN = re.compile(
    r"""
    ₹
    |
    \d+(?:\.\d+)?
    |
    /night
    |
    [A-Za-z]+(?:[-'][A-Za-z]+)*
    """,
    re.VERBOSE | re.IGNORECASE,
)


def _tokenize(text: str) -> list[str]:
    """
    Convert the user's query into meaningful tokens.

    Example:

        "book me a hotel around 4000 per night and
         around 4.5 rated and around 5 km"

    becomes approximately:

        [
            "book",
            "me",
            "a",
            "hotel",
            "around",
            "4000",
            "per",
            "night",
            "and",
            "around",
            "4.5",
            "rated",
            "and",
            "around",
            "5",
            "km",
        ]

    We deliberately tokenize instead of using an arbitrary character
    window around each number.
    """

    return TOKEN_PATTERN.findall(text.lower())


# ============================================================
# NUMBER DETECTION
# ============================================================

NUMBER_PATTERN = re.compile(
    r"^\d+(?:\.\d+)?$"
)


def _is_number(token: str) -> bool:
    """Return True when a token represents a number."""

    return bool(NUMBER_PATTERN.fullmatch(token))


# ============================================================
# TOKEN HELPERS
# ============================================================

def _previous_token(
    tokens: list[str],
    index: int,
) -> str | None:
    """Return the token immediately before the current token."""

    if index == 0:
        return None

    return tokens[index - 1]


def _next_token(
    tokens: list[str],
    index: int,
) -> str | None:
    """Return the token immediately after the current token."""

    if index + 1 >= len(tokens):
        return None

    return tokens[index + 1]


def _next_two_tokens(
    tokens: list[str],
    index: int,
) -> tuple[str | None, str | None]:
    """Return the next two tokens after the current token."""

    first = _next_token(tokens, index)

    if index + 2 >= len(tokens):
        return first, None

    return first, tokens[index + 2]


def _has_soft_language_near_number(
    tokens: list[str],
    index: int,
) -> bool:
    """
    Determine whether this number is associated with soft-preference
    language.

    We intentionally inspect nearby TOKENS rather than characters.

    Examples:

        "around 4000"
              ↑
        previous token = around → True

        "preferably 4.5 stars"
                  ↑
        previous token = preferably → True
    """

    previous = _previous_token(tokens, index)

    if previous in SOFT_LANGUAGE_MARKERS:
        return True

    # Handle:

        # "prefer a hotel around 4000"

    # The immediately preceding token is "around", so this is already
    # covered above.

    return False


# ============================================================
# DOMAIN CLASSIFICATION
# ============================================================

def _classify_number(
    tokens: list[str],
    index: int,
) -> str | None:
    """
    Classify one numeric token as:

        "price"
        "rating"
        "distance"
        None

    Classification is based on tokens directly associated with THIS
    number.

    We never inspect an arbitrary section of the entire sentence.

    Examples:

        around 4000 per night
               ↑
               PRICE

        around 4.5 rated
               ↑
               RATING

        around 5 km
               ↑
               DISTANCE
    """

    value = float(tokens[index])

    previous = _previous_token(tokens, index)
    next_token = _next_token(tokens, index)
    next_token_2 = (
        tokens[index + 2]
        if index + 2 < len(tokens)
        else None
    )

    # --------------------------------------------------------
    # 1. DISTANCE
    # --------------------------------------------------------
    #
    # The distance unit must be directly after the number.
    #
    #     5 km
    #     3 kilometers
    #     2 miles
    #
    if next_token in DISTANCE_UNITS:
        return "distance"

    # --------------------------------------------------------
    # 2. RATING
    # --------------------------------------------------------
    #
    # Rating marker must be directly after the number.
    #
    #     4 rated
    #     4.5 stars
    #     4 rating
    #
    if next_token in RATING_MARKERS:
        return "rating"


    # --------------------------------------------------------
    # 3. EXPLICIT PRICE
    # --------------------------------------------------------
    #
    #     ₹4000
    #
    # The tokenizer produces:
    #
    #     ["₹", "4000"]
    #
    if previous == "₹":
        return "price"

    #     Rs 4000
    #     Rs. 4000
    #     rupees 4000
    #
    if previous in PRICE_MARKERS:
        return "price"

    # --------------------------------------------------------
    # 4. PRICE PHRASES
    # --------------------------------------------------------
    #
    #     4000 per night
    #     4000 a night
    #     4000 nightly
    #
    if next_token == "per" and next_token_2 == "night":
        return "price"

    if next_token == "a" and next_token_2 == "night":
        return "price"

    if next_token == "nightly":
        return "price"

    if next_token == "/night":
        return "price"

    # --------------------------------------------------------
    # 5. UNQUALIFIED SOFT PRICE
    # --------------------------------------------------------
    #
    # Example:
    #
    #     "hotel around 4000"
    #
    # There is no "₹", "Rs", or "per night".
    #
    # Because this is a HOTEL domain, an unqualified large number
    # following soft-preference language is interpreted as price.
    #
    # We use a conservative threshold so that:
    #
    #     around 3
    #     around 4
    #     around 5
    #
    # aren't accidentally interpreted as prices.
    #
    if previous in SOFT_LANGUAGE_MARKERS and value >= 100:
        return "price"

    return None


# ============================================================
# MAIN EXTRACTION
# ============================================================

def extract_preferences(text: str) -> ExtractedPreferences:
    """
    Deterministically extract soft hotel preferences.

    Pipeline:

        raw text
            ↓
        tokenize
            ↓
        identify numeric tokens
            ↓
        inspect directly associated tokens
            ↓
        classify as price / rating / distance
            ↓
        return ExtractedPreferences

    This function:

        DOES:
            - extract soft price
            - extract soft rating
            - extract soft distance

        DOES NOT:
            - call the LLM
            - perform hard filtering
            - calculate utilities
            - calculate scores
            - modify TravelIntent
    """

    preferences = ExtractedPreferences()

    tokens = _tokenize(text)

    for index, token in enumerate(tokens):

        if not _is_number(token):
            continue

        # ----------------------------------------------------
        # Hard constraints must not become soft preferences.
        # ----------------------------------------------------
        #
        # We only consider numbers immediately associated with
        # soft language such as:
        #
        #     around
        #     about
        #     approximately
        #     prefer
        #     ideally
        #
        if not _has_soft_language_near_number(tokens, index):
            continue

        domain = _classify_number(tokens, index)

        value = float(token)

        if domain == "price":
            preferences.target_price = value

        elif domain == "rating":
            preferences.target_rating = value

        elif domain == "distance":
            preferences.target_distance = value

    return preferences
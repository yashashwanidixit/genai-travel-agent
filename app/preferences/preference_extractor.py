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
# RATING MARKERS
# ============================================================

RATING_MARKERS = {
    "rated",
    "rating",
    "star",
    "stars",
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


def tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


# ============================================================
# NUMBER DETECTION
# ============================================================

NUMBER_PATTERN = re.compile(r"^\d+(?:\.\d+)?$")


def is_number(token: str) -> bool:
    return bool(NUMBER_PATTERN.fullmatch(token))


# ============================================================
# TOKEN HELPERS
# ============================================================

def _previous_token(
    tokens: list[str],
    index: int,
) -> str | None:
    if index == 0:
        return None

    return tokens[index - 1]


def _next_token(
    tokens: list[str],
    index: int,
) -> str | None:
    if index + 1 >= len(tokens):
        return None

    return tokens[index + 1]


# ============================================================
# RATING EXTRACTION
# ============================================================

def _is_rating_expression(
    tokens: list[str],
    index: int,
) -> bool:
    """
    Determine whether a numeric token represents a hotel rating.

    Uses a small local context window instead of requiring the rating
    marker to be immediately adjacent to the number.

    Examples recognized:

        4.5 stars
        4.5 star
        rated 4.5
        rating 4.5
        rating of 4.5
        4.5 rated
        rated around 4.5
        around 4.5 rated
        rating around 4.5
        4.5 is rated
        hotel rated around 4.5 stars

    Only the two tokens before and after the number are inspected.
    """

    start = max(0, index - 2)
    end = min(len(tokens), index + 3)

    nearby_tokens = tokens[start:end]

    # If a rating-related marker appears within the local window,
    # treat the number as a rating candidate.
    for token in nearby_tokens:
        if token in RATING_MARKERS:
    
            return True

    return False


# ============================================================
# HARD-CONSTRAINT DETECTION
# ============================================================

HARD_RATING_MARKERS = {
    "at",
    "least",
    "minimum",
    "above",
    "higher",
    "lower",
    "more",
    "than",
}


def _is_hard_rating_expression(
    tokens: list[str],
    index: int,
) -> bool:
    """
    Return True if the rating expression is clearly a hard
    minimum constraint.

    Examples:

        rated at least 4
        rating minimum 4
        rating above 4
        rating higher than 4
        4 or higher

    These must NOT become target_rating.
    """

    previous = _previous_token(tokens, index)

    # --------------------------------------------------------
    # "rated at least 4"
    # --------------------------------------------------------

    if (
        index >= 2
        and tokens[index - 1] == "least"
        and tokens[index - 2] == "at"
    ):
        return True

    # --------------------------------------------------------
    # "minimum rating 4"
    # --------------------------------------------------------

    if (
        index >= 2
        and tokens[index - 2] == "minimum"
        and tokens[index - 1] == "rating"
    ):
        return True

    # --------------------------------------------------------
    # "rating above 4"
    # --------------------------------------------------------

    if (
        index >= 2
        and tokens[index - 2] == "rating"
        and tokens[index - 1] in {"above", "higher", "lower"}
    ):
        return True

    # --------------------------------------------------------
    # "rated higher than 4"
    # --------------------------------------------------------

    if (
        index >= 3
        and tokens[index - 3] == "rated"
        and tokens[index - 2] in {"higher", "above"}
        and tokens[index - 1] == "than"
    ):
        return True

    # --------------------------------------------------------
    # "4 or higher"
    # --------------------------------------------------------

    next_token = _next_token(tokens, index)

    if next_token == "or":
        if index + 2 < len(tokens):
            if tokens[index + 2] in {"higher", "above"}:
                return True

    return False


# ============================================================
# SOFT RATING DETECTION
# ============================================================

def is_soft_rating_expression(
    tokens: list[str],
    index: int,
) -> bool:
    """
    Determine whether a numeric rating represents a soft
    preference rather than a hard minimum.

    A rating expression is considered soft when:

        - it is a normal rating expression, AND
        - it is not a hard constraint.

    Examples accepted:

        around 4.5 stars
        about 4.5 stars
        preferably 4.5 stars
        ideally 4.5 stars
        prefer 4.5 stars
        4.5 stars
        rated 4.5
        rating of 4.5
        I want a 4.5 star hotel

    Examples rejected:

        rated at least 4
        minimum rating 4
        rating above 4
        rating higher than 4
        4 or higher
    """

    if not _is_rating_expression(tokens, index):
  
        return False

    if _is_hard_rating_expression(tokens, index):
        return False

    return True


# ============================================================
# MAIN EXTRACTION
# ============================================================

def extract_preferences(text: str) -> ExtractedPreferences:
    """
    Deterministically extract soft hotel preferences.

    Currently extracts:

        - target_rating

    Hard constraints such as minimum_hotel_rating are NOT extracted
    here. They belong to TravelIntent and the LLM intent parser.

    Examples:

        "hotel around 4.5 stars"
            -> target_rating = 4.5

        "hotel ideally rated 4.5"
            -> target_rating = 4.5

        "hotel with a rating of 4.5"
            -> target_rating = 4.5

        "hotel rated at least 4"
            -> target_rating = None
    """

    tokens = tokenize(text)

    preferences = ExtractedPreferences()

    for index, token in enumerate(tokens):

        if not is_number(token):
         
            continue

        value = float(token)
      

        if is_soft_rating_expression(tokens, index):
            preferences.target_rating = value
            

    return preferences
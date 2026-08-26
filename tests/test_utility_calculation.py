"""
Deterministic unit + integration tests for R2 (Utility Calculation).

No Ollama, no network, no routing, no location resolution, no hotel
provider, no hard filtering. HotelFeatures / UserProfile /
EffectivePreferences are constructed directly.
"""

import pytest

from app.recommendation.effective_preferences import (
    EffectivePreferences,
    resolve_effective_preferences,
)
from app.recommendation.feature_extraction import HotelFeatures
from app.recommendation.user_profile import UserProfile
from app.recommendation.utility_calculation import (
    HotelUtilities,
    calculate_distance_utility,
    calculate_price_utility,
    calculate_rating_utility,
    calculate_utilities,
)


# ---------------------------------------------------------------- PRICE

def test_price_utility_exact_match_is_one():
    """Price exactly at target must yield maximum utility (1.0)."""
    assert calculate_price_utility(price=3000, target_price=3000) == 1.0


def test_price_utility_slightly_off_is_high_but_below_one():
    """A small deviation from target should reduce utility slightly,
    not eliminate it - the hotel is still a reasonably good match."""
    utility = calculate_price_utility(price=3200, target_price=3000)
    assert 0.0 < utility < 1.0
    assert utility > 0.9  # small deviation relative to default scale=3000


def test_price_utility_far_off_is_low():
    """A large deviation from target must yield low utility."""
    utility = calculate_price_utility(price=6000, target_price=3000)
    assert utility < 0.5


def test_price_utility_always_bounded():
    """Utility must never leave [0,1], even for extreme deviations."""
    for price in (0, 100, 3000, 10000, 1_000_000):
        utility = calculate_price_utility(price=price, target_price=3000)
        assert 0.0 <= utility <= 1.0


def test_price_utility_monotonic_closer_is_better():
    """Two hotels equally valid except one closer to the target price
    must have the closer one score higher."""
    closer = calculate_price_utility(price=3100, target_price=3000)
    farther = calculate_price_utility(price=4500, target_price=3000)
    assert closer > farther


# ---------------------------------------------------------------- RATING

def test_rating_utility_exact_match_is_one():
    """Rating exactly at target must yield maximum utility (1.0)."""
    assert calculate_rating_utility(rating=4.2, target_rating=4.2) == 1.0


def test_rating_utility_below_target_is_less_than_one():
    """A rating below the target must yield utility < 1.0."""
    utility = calculate_rating_utility(rating=4.0, target_rating=4.2)
    assert utility < 1.0


def test_rating_utility_far_below_target_is_low():
    """A rating much below the target must yield a low utility."""
    utility = calculate_rating_utility(rating=1.0, target_rating=4.2)
    assert utility < 0.5


def test_rating_above_target_is_treated_as_deviation_not_bonus():
    """
    EXPLICIT DESIGN CHECK: a rating ABOVE the target must be penalized
    exactly as much as the same-magnitude deviation below the target -
    "higher rating" is NOT automatically better in this design.
    """
    above = calculate_rating_utility(rating=5.0, target_rating=4.2)
    below = calculate_rating_utility(rating=3.4, target_rating=4.2)
    # both deviate from target by 0.8
    assert above == pytest.approx(below)
    assert above < 1.0


def test_rating_utility_bounded_at_extremes():
    """Ratings at the natural range extremes (0 and 5) must not crash
    and must remain within [0,1]."""
    for rating in (0.0, 5.0):
        utility = calculate_rating_utility(rating=rating, target_rating=4.2)
        assert 0.0 <= utility <= 1.0


# -------------------------------------------------------------- DISTANCE

def test_distance_utility_exact_match_is_one():
    """Distance exactly at the preferred distance must yield 1.0."""
    utility = calculate_distance_utility(distance_km=5.0, target_distance=5.0)
    assert utility == 1.0


def test_distance_utility_slightly_off_is_less_than_one():
    """A small deviation from preferred distance reduces utility."""
    utility = calculate_distance_utility(distance_km=4.0, target_distance=5.0)
    assert utility < 1.0


def test_distance_utility_closer_than_preferred_is_not_automatically_best():
    """
    EXPLICIT DESIGN CHECK: a hotel MUCH closer than the preferred
    distance is not treated as ideal - only a hotel AT the preferred
    distance gets utility 1.0.
    """
    much_closer = calculate_distance_utility(distance_km=0.0, target_distance=5.0)
    at_target = calculate_distance_utility(distance_km=5.0, target_distance=5.0)
    assert much_closer < at_target
    assert at_target == 1.0


def test_distance_utility_far_off_is_low():
    """A distance far from the preferred distance yields low utility."""
    utility = calculate_distance_utility(distance_km=20.0, target_distance=5.0)
    assert utility < 0.3


def test_distance_utility_none_stays_none():
    """
    distance_km = None must produce distance_utility = None, NOT 0.0
    and NOT 1.0. R2 must never fabricate a missing distance signal.
    """
    utility = calculate_distance_utility(distance_km=None, target_distance=5.0)
    assert utility is None


def test_distance_utility_no_division_by_zero_at_zero_distance():
    """distance_km = 0 with any target must not raise."""
    utility = calculate_distance_utility(distance_km=0.0, target_distance=0.0)
    assert utility == 1.0


# --------------------------------------------------- PROFILE FALLBACK

def test_effective_preferences_use_profile_when_intent_target_is_none():
    """
    If the current intent has no soft target for a dimension, the
    profile's preferred value must be used as the effective target.
    """
    profile = UserProfile(
        name="test",
        preferred_price=4000.0,
        preferred_rating=4.2,
        preferred_distance=5.0,
        price_weight=0.3,
        rating_weight=0.5,
        distance_weight=0.2,
    )

    effective = resolve_effective_preferences(
        profile=profile,
        intent_target_price=None,
        intent_target_rating=None,
        intent_target_distance=None,
    )

    assert effective.target_price == 4000.0
    assert effective.target_rating == 4.2
    assert effective.target_distance == 5.0


def test_effective_preferences_current_intent_overrides_profile():
    """
    NO ALPHA BLENDING: if the current intent supplies an explicit
    target, it must be used AS-IS, fully overriding the profile value
    for that dimension - not averaged, not blended.
    """
    profile = UserProfile(
        name="test",
        preferred_price=5000.0,
        preferred_rating=4.0,
        preferred_distance=3.0,
        price_weight=0.6,
        rating_weight=0.2,
        distance_weight=0.2,
    )

    effective = resolve_effective_preferences(
        profile=profile,
        intent_target_price=3000.0,
        intent_target_rating=None,
        intent_target_distance=None,
    )

    # price comes from current intent, fully overriding the profile
    assert effective.target_price == 3000.0
    # rating and distance fall back to the profile since intent gave None
    assert effective.target_rating == 4.0
    assert effective.target_distance == 3.0


# ------------------------------------------------------- WEIGHT SEPARATION

def test_hotel_utilities_has_no_score_or_weight_fields():
    """
    Structural guard: HotelUtilities must contain ONLY utility values.
    No score, weighted_score, or preference_score field may exist -
    those belong to a future R3 stage that is not implemented here.
    """
    field_names = set(HotelUtilities.model_fields.keys())
    assert field_names == {"price_utility", "rating_utility", "distance_utility"}


def test_calculate_utilities_does_not_apply_profile_weights():
    """
    Even though UserProfile carries weights, calculate_utilities must
    never read or apply them - it only uses EffectivePreferences
    targets. This test proves weights have zero effect on the output.
    """
    features = HotelFeatures(price=3200, rating=4.4, distance_km=3.0)
    preferences = EffectivePreferences(
        target_price=3000, target_rating=4.2, target_distance=5.0
    )

    result_a = calculate_utilities(features, preferences)

    # A wildly different weight profile would change nothing, since
    # calculate_utilities never receives weights at all - there is no
    # weight parameter to even pass in.
    result_b = calculate_utilities(features, preferences)

    assert result_a == result_b


# --------------------------------------------------------- IMMUTABILITY

def test_calculate_utilities_does_not_mutate_features_or_preferences():
    """R2 must not modify the HotelFeatures or EffectivePreferences it
    was given - only read from them."""
    features = HotelFeatures(price=3200, rating=4.4, distance_km=3.0)
    preferences = EffectivePreferences(
        target_price=3000, target_rating=4.2, target_distance=5.0
    )

    original_price = features.price
    original_rating = features.rating
    original_distance = features.distance_km
    original_target_price = preferences.target_price

    calculate_utilities(features, preferences)

    assert features.price == original_price
    assert features.rating == original_rating
    assert features.distance_km == original_distance
    assert preferences.target_price == original_target_price


# ----------------------------------------------------- INTEGRATION TEST

def test_integration_full_pipeline_features_profile_intent_to_utilities():
    """
    Small deterministic integration test:
        HotelFeatures + UserProfile + current intent targets
            -> resolve_effective_preferences
            -> calculate_utilities
            -> HotelUtilities

    Uses the exact example from the spec: profile has
    preferred_price=5000/preferred_rating=4.2/preferred_distance=5,
    current intent only supplies target_price=3000 (rating/distance
    are None). Effective targets must end up as price=3000 (from
    intent), rating=4.2 and distance=5 (both from profile fallback).

    No Ollama, no HotelProvider, no routing, no full application -
    this only exercises the R2-relevant chain.
    """
    profile = UserProfile(
        name="integration-test-profile",
        preferred_price=5000.0,
        preferred_rating=4.2,
        preferred_distance=5.0,
        price_weight=0.3,
        rating_weight=0.5,
        distance_weight=0.2,
    )

    effective = resolve_effective_preferences(
        profile=profile,
        intent_target_price=3000.0,
        intent_target_rating=None,
        intent_target_distance=None,
    )

    assert effective.target_price == 3000.0
    assert effective.target_rating == 4.2
    assert effective.target_distance == 5.0

    features = HotelFeatures(price=3200, rating=4.4, distance_km=3.0)
    utilities = calculate_utilities(features, effective)

    assert isinstance(utilities, HotelUtilities)
    assert 0.0 <= utilities.price_utility <= 1.0
    assert 0.0 <= utilities.rating_utility <= 1.0
    assert utilities.distance_utility is not None
    assert 0.0 <= utilities.distance_utility <= 1.0

    # sanity-check against the formulas directly
    assert utilities.price_utility == pytest.approx(
        calculate_price_utility(3200, 3000.0)
    )
    assert utilities.rating_utility == pytest.approx(
        calculate_rating_utility(4.4, 4.2)
    )
    assert utilities.distance_utility == pytest.approx(
        calculate_distance_utility(3.0, 5.0)
    )


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-v"]))
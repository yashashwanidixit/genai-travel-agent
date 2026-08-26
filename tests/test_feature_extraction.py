"""
Deterministic unit tests for R1 (Recommendation Feature Extraction),
updated for the HotelContext -> HotelFeatures interface.

No Ollama, no LLM calls, no network, no routing/GraphHopper/Haversine,
no location resolution, no hard filtering. Hotel and HotelContext
objects are constructed by hand so these tests are fast and fully
isolated from every other stage of the pipeline.
"""

from app.models.hotel import Hotel
from app.models.hotel_context import HotelContext
from app.recommendation.feature_extraction import HotelFeatures, extract_features


def _hotel(**overrides) -> Hotel:
    defaults = dict(
        id="hotel_001",
        name="Whitefield Grand",
        city="Bengaluru",
        address="ITPL Main Road, Whitefield",
        star_rating=4,
        user_rating=4.4,
        price_per_night=3500.0,
        currency="INR",
        latitude=12.9698,
        longitude=77.7500,
    )
    defaults.update(overrides)
    return Hotel(**defaults)


def test_basic_feature_extraction():
    """
    R1's price, rating, and distance must match the source Hotel and
    HotelContext exactly - this is the core contract of the
    HotelContext -> HotelFeatures mapping.
    """
    hotel = _hotel(price_per_night=3500.0, user_rating=4.4)
    context = HotelContext(hotel=hotel, distance_km=2.7)

    features = extract_features(context)

    assert features.price == hotel.price_per_night
    assert features.rating == hotel.user_rating
    assert features.distance_km == context.distance_km


def test_distance_is_preserved_exactly():
    """
    Distance must pass through R1 with no rounding, truncation, or
    normalization - the routing layer already produced this value and
    R1's only job is to copy it forward untouched.
    """
    hotel = _hotel()
    context = HotelContext(hotel=hotel, distance_km=3.75)

    features = extract_features(context)

    assert features.distance_km == 3.75


def test_none_distance_is_preserved():
    """
    When no reference/meeting location was available upstream,
    distance_km is None on HotelContext. R1 must propagate that None
    rather than inventing 0 or any other fallback value.
    """
    hotel = _hotel()
    context = HotelContext(hotel=hotel, distance_km=None)

    features = extract_features(context)

    assert features.distance_km is None


def test_raw_values_remain_raw_not_normalized():
    """
    Explicitly protects the R1/R2 boundary. A hotel priced at 4000,
    rated 4.2, at distance 5.5 km must come out of R1 as exactly
    those values - not converted into [0,1]-style utilities such as
    0.65, 0.88, or 0.73. Utility normalization is R2's job, not R1's.
    """
    hotel = _hotel(price_per_night=4000.0, user_rating=4.2)
    context = HotelContext(hotel=hotel, distance_km=5.5)

    features = extract_features(context)

    assert features.price == 4000.0
    assert features.rating == 4.2
    assert features.distance_km == 5.5

    assert features.price != 0.65
    assert features.rating != 0.88
    assert features.distance_km != 0.73


def test_hotel_is_not_mutated():
    """
    Feature extraction must be a pure, non-mutating read of the Hotel
    embedded in the context.
    """
    hotel = _hotel(price_per_night=3500.0, user_rating=4.4)
    context = HotelContext(hotel=hotel, distance_km=2.7)

    original_price = hotel.price_per_night
    original_rating = hotel.user_rating

    extract_features(context)

    assert hotel.price_per_night == original_price
    assert hotel.user_rating == original_rating


def test_hotel_context_is_not_mutated():
    """
    Feature extraction must not modify the HotelContext object itself,
    including its distance_km field.
    """
    hotel = _hotel()
    context = HotelContext(hotel=hotel, distance_km=2.7)

    original_distance = context.distance_km

    extract_features(context)

    assert context.distance_km == original_distance
    assert context.hotel is hotel


def test_returns_new_hotel_features_instance():
    """
    R1 must return a distinct new HotelFeatures object, not the
    HotelContext itself or a mutated version of it.
    """
    hotel = _hotel()
    context = HotelContext(hotel=hotel, distance_km=2.7)

    features = extract_features(context)

    assert isinstance(features, HotelFeatures)
    assert features is not context


def test_same_hotel_different_contexts_yield_different_distances():
    """
    Distance is search-context dependent: the SAME Hotel can appear in
    two different HotelContext objects (e.g. two different meeting
    locations) with two different distances. R1 must respect whichever
    context it was given, and the underlying Hotel must remain
    unaffected by either call.
    """
    hotel = _hotel()
    context_a = HotelContext(hotel=hotel, distance_km=2.0)
    context_b = HotelContext(hotel=hotel, distance_km=8.0)

    features_a = extract_features(context_a)
    features_b = extract_features(context_b)

    assert features_a.distance_km == 2.0
    assert features_b.distance_km == 8.0
    assert hotel.price_per_night == context_a.hotel.price_per_night
    assert hotel.price_per_night == context_b.hotel.price_per_night


def test_rating_comes_from_user_rating_not_star_rating():
    """
    When a Hotel has both user_rating and star_rating, R1 must use
    user_rating - the field reflecting actual guest experience - not
    the official star classification.
    """
    hotel = _hotel(user_rating=4.4, star_rating=3)
    context = HotelContext(hotel=hotel, distance_km=1.0)

    features = extract_features(context)

    assert features.rating == 4.4
    assert features.rating != hotel.star_rating


def test_no_scoring_or_weighting_fields_exist():
    """
    Structural guard: HotelFeatures must contain only factual fields
    (price, rating, distance_km) - no score, utility, weighted_score,
    or preference_score field should exist on this model, since those
    belong to future R2/R3 stages.
    """
    field_names = set(HotelFeatures.model_fields.keys())
    assert field_names == {"price", "rating", "distance_km"}

    hotel = _hotel()
    context = HotelContext(hotel=hotel, distance_km=1.0)
    features = extract_features(context)

    assert not hasattr(features, "score")
    assert not hasattr(features, "utility")
    assert not hasattr(features, "weighted_score")
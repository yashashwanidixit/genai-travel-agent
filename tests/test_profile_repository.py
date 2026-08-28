import pytest

from app.profiles.in_memory_profile_repository import (
    InMemoryProfileRepository,
)


def test_get_profile_a():
    repository = InMemoryProfileRepository()

    profile = repository.get_profile("A")

    assert profile.name == "A"
    assert profile.preferred_price == 4000.0
    assert profile.preferred_rating == 4.2
    assert profile.preferred_distance == 5.0


def test_get_profile_b():
    repository = InMemoryProfileRepository()

    profile = repository.get_profile("B")

    assert profile.name == "B"
    assert profile.preferred_price == 6000.0
    assert profile.preferred_rating == 4.0
    assert profile.preferred_distance == 3.0


def test_get_profile_c():
    repository = InMemoryProfileRepository()

    profile = repository.get_profile("C")

    assert profile.name == "C"


def test_unknown_user_raises_error():
    repository = InMemoryProfileRepository()

    with pytest.raises(ValueError):
        repository.get_profile("UNKNOWN")
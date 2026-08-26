from app.agents.intent_agent import IntentAgent
from app.models.intent import IntentCategory
from app.llm.provider import LLMProvider


class FakeLLMProvider(LLMProvider):

    def __init__(self, response: str):
        self.response = response

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema=None,
    ) -> str:
        return self.response


def test_soft_preferences_are_merged_into_intent():
    provider = FakeLLMProvider(
        """
        {
            "category": "hotel_search",
            "origin": null,
            "destination": "Whitefield",
            "meeting_location": null,
            "minimum_hotel_rating": null,
            "max_hotel_price": null,
            "max_hotel_distance_km": null
        }
        """
    )

    agent = IntentAgent(provider)

    query = (
        "Book me a hotel in Whitefield around 4000 "
        "and around 4 rated"
    )

    intent = agent.parse(query)

    assert intent.primary_category == IntentCategory.HOTEL_SEARCH

    # Deterministic extractor
    assert intent.slots.target_price == 4000
    assert intent.slots.target_rating == 4

    # Must NOT become hard constraints
    assert intent.slots.max_hotel_price is None
    assert intent.slots.minimum_hotel_rating is None


def test_soft_price_and_hard_rating_remain_separate():
    provider = FakeLLMProvider(
        """
        {
            "category": "hotel_search",
            "origin": "Bangalore Airport",
            "destination": "Whitefield",
            "meeting_location": "Google Ananta office",
            "minimum_hotel_rating": 3,
            "max_hotel_price": null,
            "max_hotel_distance_km": null
        }
        """
    )

    agent = IntentAgent(provider)

    query = (
        "I just landed at Bangalore Airport and have a meeting "
        "at Google Ananta office. Book me a hotel in Whitefield "
        "around 4000 and rated above 3."
    )

    intent = agent.parse(query)

    # SOFT preference
    assert intent.slots.target_price == 4000

    # No soft rating was requested.
    assert intent.slots.target_rating is None

    # HARD constraint
    assert intent.slots.minimum_hotel_rating == 3

    # No hard price constraint.
    assert intent.slots.max_hotel_price is None


def test_soft_price_does_not_become_hard_price():
    provider = FakeLLMProvider(
        """
        {
            "category": "hotel_search",
            "origin": null,
            "destination": "Whitefield",
            "meeting_location": null,
            "minimum_hotel_rating": null,
            "max_hotel_price": null,
            "max_hotel_distance_km": null
        }
        """
    )

    agent = IntentAgent(provider)

    query = "I would prefer a hotel around 5000 per night"

    intent = agent.parse(query)

    assert intent.slots.target_price == 5000

    # Very important boundary check.
    assert intent.slots.max_hotel_price is None


def test_soft_rating_does_not_become_hard_rating():
    provider = FakeLLMProvider(
        """
        {
            "category": "hotel_search",
            "origin": null,
            "destination": "Whitefield",
            "meeting_location": null,
            "minimum_hotel_rating": null,
            "max_hotel_price": null,
            "max_hotel_distance_km": null
        }
        """
    )

    agent = IntentAgent(provider)

    query = "I would prefer a hotel around 4 rated"

    intent = agent.parse(query)

    assert intent.slots.target_rating == 4

    # Very important boundary check.
    assert intent.slots.minimum_hotel_rating is None
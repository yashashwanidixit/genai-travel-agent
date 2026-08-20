from app.agents.intent_agent import IntentAgent
from app.agents.memory_agent import MemoryAgent
from app.agents.reasoning_agent import ReasoningAgent
from app.models.intent import IntentCategory
from app.models.hotel import Hotel
from app.models.ride import RideEstimate, RideType
from app.models.user import UserPreferences


def test_intent_agent_extraction():
    agent = IntentAgent()
    query = "Plan a weekend trip to Bengaluru under 20000 with swimming pool and sedan cab"
    intent = agent.extract_intent(query)

    assert intent.primary_category == IntentCategory.TRIP_PLANNING
    assert intent.slots.destination == "Bengaluru"
    assert intent.slots.budget == 20000.0
    assert "Swimming Pool" in intent.slots.amenities
    assert intent.slots.ride_type == "Sedan"


def test_memory_agent_lifecycle():
    agent = MemoryAgent()
    agent.record_interaction("session_1", "user", "I like luxury stays")
    history = agent.episodic.get_history("session_1")
    assert len(history) == 1
    assert history[0].content == "I like luxury stays"

    # Test learning preferences
    intent = IntentAgent().extract_intent("Book a 5 star hotel under 18000")
    agent.learn_from_intent("usr_1", intent)
    prefs = agent.preferences.get_preferences("usr_1")
    assert prefs.max_hotel_budget_per_night == 18000.0


def test_reasoning_agent_synthesis():
    agent = ReasoningAgent()
    intent = IntentAgent().extract_intent("Trip to Bengaluru")
    hotel = Hotel(
        id="h1", name="Test Hotel", city="Bengaluru", address="Test Rd",
        star_rating=5, user_rating=4.8, price_per_night=10000.0
    )
    ride = RideEstimate(
        provider="Uber Mock", ride_type=RideType.SEDAN, estimated_fare=500.0,
        duration_minutes=30, distance_km=12.0
    )
    prefs = UserPreferences()

    plan = agent.synthesize_trip_plan(
        user_id="u1",
        intent=intent,
        ranked_hotels=[hotel],
        ranked_rides=[ride],
        preferences=prefs
    )

    assert plan.plan_id.startswith("plan_")
    assert plan.selected_hotel.name == "Test Hotel"
    assert plan.selected_ride.ride_type == RideType.SEDAN
    assert len(plan.itinerary) >= 2

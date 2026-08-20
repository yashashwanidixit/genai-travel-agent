import uuid
from typing import Optional
from app.orchestration.states import TravelState, StateContext
from app.orchestration.state_machine import TravelStateMachine
from app.agents.intent_agent import IntentAgent
from app.agents.memory_agent import MemoryAgent
from app.agents.reasoning_agent import ReasoningAgent
from app.recommendation.ranker import TravelRanker
from app.providers.hotels.mock import MockHotelProvider
from app.providers.rides.mock import MockRideProvider
from app.models.hotel import HotelSearchQuery
from app.models.ride import RideSearchQuery, RideType
from app.models.trip import TripPlan, TripRequest


class TravelOrchestrator:
    """Coordinates multi-agent workflows, state transitions, memory and provider pipelines."""

    def __init__(
        self,
        intent_agent: Optional[IntentAgent] = None,
        memory_agent: Optional[MemoryAgent] = None,
        reasoning_agent: Optional[ReasoningAgent] = None,
        ranker: Optional[TravelRanker] = None,
        hotel_provider: Optional[MockHotelProvider] = None,
        ride_provider: Optional[MockRideProvider] = None,
    ):
        self.intent_agent = intent_agent or IntentAgent()
        self.memory_agent = memory_agent or MemoryAgent()
        self.reasoning_agent = reasoning_agent or ReasoningAgent()
        self.ranker = ranker or TravelRanker()
        self.hotel_provider = hotel_provider or MockHotelProvider()
        self.ride_provider = ride_provider or MockRideProvider()

    async def plan_trip(self, request: TripRequest) -> StateContext:
        session_id = f"sess_{uuid.uuid4().hex[:8]}"
        context = StateContext(
            session_id=session_id,
            user_id=request.user_id,
            current_state=TravelState.IDLE,
            raw_query=request.query
        )

        try:
            # 1. State: Extracting Intent
            TravelStateMachine.transition(context, TravelState.EXTRACTING_INTENT)
            self.memory_agent.record_interaction(session_id, "user", request.query)

            intent = self.intent_agent.extract_intent(request.query)
            if request.destination:
                intent.slots.destination = request.destination
            if request.origin:
                intent.slots.origin = request.origin
            if request.budget:
                intent.slots.budget = request.budget

            context.intent = intent
            self.memory_agent.learn_from_intent(request.user_id, intent)
            prefs = self.memory_agent.preferences.get_preferences(request.user_id)

            # 2. State: Searching Hotels
            TravelStateMachine.transition(context, TravelState.SEARCHING_HOTELS)
            hotel_query = HotelSearchQuery(
                city=intent.slots.destination or "Bengaluru",
                min_stars=prefs.preferred_hotel_stars,
                max_budget_per_night=intent.slots.budget or prefs.max_hotel_budget_per_night,
                required_amenities=intent.slots.amenities or prefs.preferred_amenities
            )
            raw_hotels = await self.hotel_provider.search_hotels(hotel_query)
            if not raw_hotels:
                # Fallback search without strict amenities/budget to return options
                raw_hotels = await self.hotel_provider.search_hotels(
                    HotelSearchQuery(city=intent.slots.destination or "Bengaluru")
                )

            # 3. State: Searching Rides
            TravelStateMachine.transition(context, TravelState.SEARCHING_RIDES)
            ride_query = RideSearchQuery(
                pickup_location=intent.slots.origin or prefs.home_city,
                dropoff_location=f"{intent.slots.destination or 'Bengaluru'} Hotel",
                preferred_type=RideType(prefs.preferred_ride_type) if prefs.preferred_ride_type in [e.value for e in RideType] else None
            )
            raw_rides = await self.ride_provider.get_estimates(ride_query)

            # 4. State: Ranking Options
            TravelStateMachine.transition(context, TravelState.RANKING_OPTIONS)
            ranked_hotels = self.ranker.rank_hotels(raw_hotels, prefs)
            ranked_rides = self.ranker.rank_rides(raw_rides, prefs)

            context.candidate_hotels = ranked_hotels
            context.candidate_rides = ranked_rides

            # 5. State: Synthesizing Plan
            TravelStateMachine.transition(context, TravelState.SYNTHESIZING_PLAN)
            plan = self.reasoning_agent.synthesize_trip_plan(
                user_id=request.user_id,
                intent=intent,
                ranked_hotels=ranked_hotels,
                ranked_rides=ranked_rides,
                preferences=prefs
            )
            context.generated_plan = plan

            # 6. Transition to AWAITING_USER_CONFIRMATION
            TravelStateMachine.transition(context, TravelState.AWAITING_USER_CONFIRMATION)
            self.memory_agent.record_interaction(
                session_id,
                "assistant",
                plan.reasoning_summary or "Synthesized trip plan successfully."
            )

        except Exception as e:
            context.current_state = TravelState.FAILED
            context.error_message = str(e)

        return context

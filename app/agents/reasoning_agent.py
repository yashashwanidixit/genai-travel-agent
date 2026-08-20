import uuid
from typing import List, Optional
from app.models.intent import TravelIntent
from app.models.hotel import Hotel
from app.models.ride import RideEstimate
from app.models.trip import TripPlan, ItineraryItem
from app.models.user import UserPreferences


class ReasoningAgent:
    """Agent responsible for multi-step reasoning, trade-off optimization, and itinerary synthesis."""

    def synthesize_trip_plan(
        self,
        user_id: str,
        intent: TravelIntent,
        ranked_hotels: List[Hotel],
        ranked_rides: List[RideEstimate],
        preferences: UserPreferences
    ) -> TripPlan:
        destination = intent.slots.destination or "Bengaluru"
        plan_id = f"plan_{uuid.uuid4().hex[:8]}"

        selected_hotel = ranked_hotels[0] if ranked_hotels else None
        selected_ride = ranked_rides[0] if ranked_rides else None

        hotel_cost = selected_hotel.price_per_night if selected_hotel else 0.0
        ride_cost = (selected_ride.estimated_fare * 2) if selected_ride else 0.0  # Pickup + Return

        # Build daily itinerary template
        itinerary: List[ItineraryItem] = [
            ItineraryItem(
                day=1,
                time_slot="Morning (09:00 AM)",
                activity="Arrival & Hotel Check-in",
                location=selected_hotel.name if selected_hotel else destination,
                notes=f"Travel from origin via {selected_ride.ride_type.value if selected_ride else 'Cab'}",
                estimated_cost=ride_cost / 2
            ),
            ItineraryItem(
                day=1,
                time_slot="Afternoon (01:00 PM)",
                activity="City Exploration & Local Cuisine Lunch",
                location=f"Central {destination}",
                notes="Recommended local dining spot",
                estimated_cost=1200.0
            ),
            ItineraryItem(
                day=1,
                time_slot="Evening (06:00 PM)",
                activity="Sightseeing & Leisure",
                location=f"Iconic Landmarks of {destination}",
                notes="Relaxed walk & photo opportunities",
                estimated_cost=500.0
            ),
            ItineraryItem(
                day=2,
                time_slot="Morning (10:00 AM)",
                activity="Breakfast & Checkout / Return",
                location=selected_hotel.name if selected_hotel else destination,
                notes=f"Return ride scheduled via {selected_ride.provider if selected_ride else 'Ride Provider'}",
                estimated_cost=ride_cost / 2
            )
        ]

        total_cost = hotel_cost + sum(item.estimated_cost for item in itinerary)

        reasoning = (
            f"Synthesized trip to {destination} optimized for a budget of ₹{intent.slots.budget or preferences.max_hotel_budget_per_night:,.0f}. "
            f"Selected {selected_hotel.name if selected_hotel else 'top hotel'} ({selected_hotel.star_rating if selected_hotel else 4}★) "
            f"matching preferred amenities, paired with {selected_ride.ride_type.value if selected_ride else 'comfortable'} ride for convenient transit."
        )

        return TripPlan(
            plan_id=plan_id,
            user_id=user_id,
            destination=destination,
            origin=intent.slots.origin or preferences.home_city,
            start_date=intent.slots.travel_date or intent.slots.check_in_date or "2026-09-01",
            end_date=intent.slots.check_out_date or "2026-09-02",
            selected_hotel=selected_hotel,
            recommended_hotels=ranked_hotels,
            selected_ride=selected_ride,
            ride_estimates=ranked_rides,
            itinerary=itinerary,
            total_estimated_cost=round(total_cost, 2),
            reasoning_summary=reasoning
        )

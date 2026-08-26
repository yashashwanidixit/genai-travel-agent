from __future__ import annotations

import json
from typing import Optional

from pydantic import BaseModel, ValidationError

from app.llm.prompts import INTENT_SYSTEM_PROMPT
from app.llm.provider import LLMProvider
from app.models.intent import ExtractedSlots, IntentCategory, TravelIntent
from app.monitoring.performance_monitor import (
    ColdStartTracker,
    PerformanceMetrics,
    PerformanceTimer,
)


class IntentParsingError(Exception):
    """Raised when the LLM output cannot be turned into a valid
    TravelIntent even after a correction retry."""


class _LLMIntentOutput(BaseModel):
    """Raw shape expected back from the LLM, before it is mapped onto
    TravelIntent. Kept separate from ExtractedSlots so a malformed
    'category' field doesn't get conflated with slot validation errors.
    """

    category: IntentCategory
    origin: Optional[str] = None
    destination: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    meeting_location: Optional[str] = None
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    number_of_rooms: Optional[int] = None
    number_of_adults: Optional[int] = None
    number_of_children: Optional[int] = None
    children_ages: Optional[list[int]] = None
    minimum_hotel_rating: Optional[float] = None
    ride_type: Optional[str] = None
    max_hotel_price: Optional[float] = None
    max_hotel_distance_km: Optional[float] = None
    target_price: Optional[float] = None
    target_rating: Optional[float] = None


class IntentAgent:
    """User query -> LLMProvider -> JSON -> Pydantic -> TravelIntent.

    IMPORTANT (Part 13 separation of responsibilities): this agent's
    job is ONLY semantic extraction. It does NOT decide missing_slots
    anymore - that determination is now owned exclusively by
    app.orchestration.requirement_checker, which runs on the
    normalized intent downstream. This agent always returns an empty
    missing_slots list; treat it as a placeholder, not a signal.
    """

    def __init__(self, llm_provider: LLMProvider, max_retries: int = 1):
        self.llm_provider = llm_provider
        self.max_retries = max_retries
        self._cold_start_tracker = ColdStartTracker()

    def parse(self, raw_query: str) -> TravelIntent:
        intent, _ = self.parse_with_metrics(raw_query)
        return intent

    def parse_with_metrics(
        self, raw_query: str
    ) -> tuple[TravelIntent, PerformanceMetrics]:
        total_timer = PerformanceTimer()
        total_timer.start()

        llm_time_accum = 0.0
        last_error: Optional[str] = None
        possible_cold_start = False
        attempt =1

        try:
            for _ in range(self.max_retries + 1):
                user_prompt = self._build_user_prompt(raw_query, last_error)
               
                print(f"\n[DEBUG] LLM attempt {attempt }")
                if hasattr(
                    self.llm_provider, "generate_structured_with_metadata"
                ):
                    if not possible_cold_start:
                        possible_cold_start = (
                            self._cold_start_tracker.is_possible_cold_start()
                        )
                    call_result = (
                        self.llm_provider.generate_structured_with_metadata(
                            INTENT_SYSTEM_PROMPT, user_prompt
                        )
                    )
                    raw_response = call_result.text
                    
                    print("\n[DEBUG] Raw LLM response:")
                    print(raw_response)
                    
                    llm_time_accum += call_result.llm_time
                else:
                    llm_timer = PerformanceTimer()
                    llm_timer.start()
                    raw_response = self.llm_provider.generate_structured(
                        INTENT_SYSTEM_PROMPT, user_prompt
                    )
                    
                    llm_time_accum += llm_timer.stop()
                 

                try:
                    parsed_json = json.loads(raw_response)
                except json.JSONDecodeError as exc:
                    last_error = f"Your last response was not valid JSON: {exc}"
                    attempt+=1
                    continue

                try:
                    llm_output = _LLMIntentOutput.model_validate(parsed_json)
                except ValidationError as exc:
                    last_error = (
                        "Your last response did not match the required "
                        f"schema: {exc}"
                    )
                    attempt+=1
                    continue
                  

                intent = self._to_travel_intent(raw_query, llm_output)
                total_time = total_timer.stop()
                metrics = PerformanceMetrics(
                    status="SUCCESS",
                    total_time=total_time,
                    llm_time=llm_time_accum,
                    overhead_time=max(total_time - llm_time_accum, 0.0),
                    possible_cold_start=possible_cold_start,
                )
                print(f"time by {attempt} call: {total_time}")
                return intent, metrics

            total_time = total_timer.stop()
            error_message = (
                f"Could not extract a valid intent after "
                f"{self.max_retries + 1} attempt(s). Last error: {last_error}"
            )
            metrics = PerformanceMetrics(
                status="FAILED",
                total_time=total_time,
                llm_time=llm_time_accum,
                overhead_time=max(total_time - llm_time_accum, 0.0),
                error=error_message,
                possible_cold_start=possible_cold_start,
            )
            raise IntentParsingError(error_message)

        except RuntimeError as exc:
            total_time = total_timer.stop()
            metrics = PerformanceMetrics(
                status="FAILED",
                total_time=total_time,
                llm_time=llm_time_accum,
                overhead_time=max(total_time - llm_time_accum, 0.0),
                error=str(exc),
                possible_cold_start=possible_cold_start,
            )
            metrics.print_report()
            raise

    def _build_user_prompt(
        self, raw_query: str, last_error: Optional[str]
    ) -> str:
        if last_error is None:
            return raw_query

        return (
            f"{last_error}\n\n"
            "Correct your response. Return JSON only, matching the "
            "required schema exactly. Do not include any explanation. "
            "Remember: minimum_hotel_rating must stay null unless the "
            "user gave an explicit numeric floor for this search.\n\n"
            f"Original user request: {raw_query}"
        )

    def _to_travel_intent(
        self, raw_query: str, llm_output: _LLMIntentOutput
    ) -> TravelIntent:
        slots = ExtractedSlots(
            origin=llm_output.origin,
            destination=llm_output.destination,
            date=llm_output.date,
            time=llm_output.time,
            meeting_location=llm_output.meeting_location,
            check_in=llm_output.check_in,
            check_out=llm_output.check_out,
            number_of_rooms=llm_output.number_of_rooms,
            number_of_adults=llm_output.number_of_adults,
            number_of_children=llm_output.number_of_children,
            children_ages=llm_output.children_ages,
            minimum_hotel_rating=llm_output.minimum_hotel_rating,
            ride_type=llm_output.ride_type,
            max_hotel_price= llm_output.max_hotel_price, 
            max_hotel_distance_km=llm_output.max_hotel_distance_km,
            target_price=llm_output.target_price,
            target_rating=llm_output.target_rating,
            
        )

        # missing_slots is intentionally left empty here. It is owned
        # by app.orchestration.requirement_checker, which runs on the
        # normalized intent (see conversation_manager.start_new_intent).
        return TravelIntent(
            raw_query=raw_query,
            primary_category=llm_output.category,
            slots=slots,
            missing_slots=[],
        )
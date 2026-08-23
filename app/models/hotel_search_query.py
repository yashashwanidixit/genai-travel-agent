"""HotelSearchQuery: what a HotelProvider needs to perform a search.

This is DELIBERATELY a different object from TravelIntent.
TravelIntent describes what the user said/wants in the language of
Stage 1's intent schema. HotelSearchQuery describes what any provider
implementation (mock, Appium, future API) actually needs as input.
Keeping them separate means provider implementations never depend on
how the LLM happened to phrase its extraction.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class HotelSearchQuery(BaseModel):
    location: str

    check_in_date: Optional[str] = None
    check_out_date: Optional[str] = None

    number_of_rooms: int = 1
    number_of_adults: int = 1
    number_of_children: int = 0
    children_ages: List[int] = Field(default_factory=list)

    # Reserved for the future Constraint Engine (Stage 2B). Stage 2A
    # accepts these fields in the contract but MUST NOT filter on
    # them - see MockHotelProvider for why.
    min_stars: Optional[int] = None
    max_budget_per_night: Optional[float] = None
    #required_amenities: List[str] = Field(default_factory=list)

    # Must be >= 1. Pydantic enforces this directly rather than the
    # provider silently reinterpreting an invalid value.
    limit: int = Field(default=10, ge=1)
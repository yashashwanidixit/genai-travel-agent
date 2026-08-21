"""
Semantic validation tests for Stage 1 intent parsing.

These are NOT unit tests with mocked components. They run real natural
language queries through the actual IntentAgent -> LLMProvider ->
OllamaProvider -> Ollama -> local model pipeline, and check the
resulting TravelIntent against structured field-level expectations.

Requirements to run:
- Ollama running locally (`ollama serve`)
- The model configured via OLLAMA_MODEL (e.g. qwen2.5:3b) pulled and
  available (`ollama pull qwen2.5:3b`)

Run with pytest:
    pytest tests/intent_test.py

Run manually (prints full input/expected/actual detail + summary):
    python tests/intent_test.py

A PASS means the real local model's extraction matched the expected
structured fields exactly (destination, minimum_hotel_rating,
missing_slots, etc. via direct field comparison — not string matching).
A FAIL means the model's actual output diverged from what Stage 1's
intent contract requires; the ACTUAL block printed for every case is
meant to help you see exactly what the model produced so you can judge
whether the prompt, the model choice, or the field itself needs work.

No production code is modified or fixed by this file. If a test
exposes a real bug, it is reported as a FAILURE with an explanation,
not silently patched.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

from app.agents.intent_agent import IntentAgent
from app.llm.ollama_provider import OllamaProvider
from app.models.intent import IntentCategory, TravelIntent


# ------------------------------------------------------------------
# Shared agent instance (real Ollama, real model — not mocked).
# Reused across all test cases so the model stays warm.
# ------------------------------------------------------------------

_shared_agent: Optional[IntentAgent] = None


def get_agent() -> IntentAgent:
    global _shared_agent
    if _shared_agent is None:
        provider = OllamaProvider()
        _shared_agent = IntentAgent(provider)
    return _shared_agent


# ------------------------------------------------------------------
# Normalization helpers (deterministic only — no fuzzy matching).
# ------------------------------------------------------------------

def _norm(value: Optional[str]) -> Optional[str]:
    """Lowercase + strip for location/string comparisons only.
    Does not correct typos, abbreviations, or synonyms — a genuine
    extraction mismatch (e.g. "ITPL" vs "Whitefield") must still fail.
    """
    if value is None:
        return None
    return value.strip().lower()


def _str_eq(actual: Optional[str], expected: str) -> bool:
    return _norm(actual) == _norm(expected)


# ------------------------------------------------------------------
# Test case runner
# ------------------------------------------------------------------

@dataclass
class CaseResult:
    name: str
    title: str
    query: str
    expected_summary: str
    passed: bool
    failures: list[str]
    intent: Optional[TravelIntent]
    exception: Optional[str] = None


def _format_slots(intent: TravelIntent) -> str:
    populated = {
        k: v for k, v in intent.slots.model_dump().items() if v is not None
    }
    if not populated:
        return "  (none)"
    return "\n".join(f"  {k}: {v}" for k, v in populated.items())


def run_case(
    name: str,
    title: str,
    query: str,
    expected_summary: str,
    check_fn: Callable[[TravelIntent], list[str]],
) -> CaseResult:
    """Runs one query through the real IntentAgent and checks it with
    check_fn, which returns a list of human-readable failure reasons
    (empty list = pass).
    """
    agent = get_agent()

    print("-" * 60)
    print(f"{name}: {title}")
    print("-" * 60)
    print("\nINPUT:")
    print(query)
    print("\nEXPECTED:")
    print(expected_summary)

    intent: Optional[TravelIntent] = None
    failures: list[str] = []
    exception_str: Optional[str] = None

    try:
        intent = agent.parse(query)
    except Exception as exc:  # noqa: BLE001 - we want to report any failure
        exception_str = f"{type(exc).__name__}: {exc}"
        failures.append(f"IntentAgent raised an exception: {exception_str}")

    print("\nACTUAL:")
    if intent is not None:
        print(f"Intent: {intent.primary_category.value}")
        print("\nSlots:")
        print(_format_slots(intent))
        print(f"\nMissing:\n  {intent.missing_slots}")
    else:
        print(f"  (no intent produced — {exception_str})")

    if intent is not None:
        failures.extend(check_fn(intent))

    passed = len(failures) == 0

    print(f"\nRESULT:\n{'PASS' if passed else 'FAIL'}")
    if not passed:
        for reason in failures:
            print(f"  - {reason}")
    print("=" * 60 + "\n")

    return CaseResult(
        name=name,
        title=title,
        query=query,
        expected_summary=expected_summary,
        passed=passed,
        failures=failures,
        intent=intent,
        exception=exception_str,
    )


# ------------------------------------------------------------------
# Test case definitions
# ------------------------------------------------------------------

def _case_1() -> CaseResult:
    return run_case(
        "TEST 1",
        "Basic hotel, no rating constraint",
        "I need a hotel in Whitefield for 2 adults.",
        "Intent: hotel_search\nSlots:\n  destination: Whitefield\n  "
        "number_of_adults: 2\nMissing: []",
        lambda intent: [
            *([f"expected category hotel_search, got {intent.primary_category}"]
              if intent.primary_category != IntentCategory.HOTEL_SEARCH else []),
            *([f"expected destination 'Whitefield', got {intent.slots.destination!r}"]
              if not _str_eq(intent.slots.destination, "Whitefield") else []),
            *([f"expected number_of_adults 2, got {intent.slots.number_of_adults!r}"]
              if intent.slots.number_of_adults != 2 else []),
            *([f"expected minimum_hotel_rating None, got {intent.slots.minimum_hotel_rating!r}"]
              if intent.slots.minimum_hotel_rating is not None else []),
            *([f"expected missing_slots [], got {intent.missing_slots!r}"]
              if intent.missing_slots != [] else []),
        ],
    )


def _case_2() -> CaseResult:
    return run_case(
        "TEST 2",
        "Explicit numeric rating floor",
        "I need a hotel in Whitefield rated at least 4.5.",
        "Intent: hotel_search\nSlots:\n  destination: Whitefield\n  "
        "minimum_hotel_rating: 4.5",
        lambda intent: [
            *([f"expected category hotel_search, got {intent.primary_category}"]
              if intent.primary_category != IntentCategory.HOTEL_SEARCH else []),
            *([f"expected destination 'Whitefield', got {intent.slots.destination!r}"]
              if not _str_eq(intent.slots.destination, "Whitefield") else []),
            *([f"expected minimum_hotel_rating 4.5, got {intent.slots.minimum_hotel_rating!r}"]
              if intent.slots.minimum_hotel_rating != 4.5 else []),
        ],
    )


def _case_3() -> CaseResult:
    return run_case(
        "TEST 3",
        '"Below X" phrasing',
        "I don't want anything below a 4 star hotel.",
        "Intent: hotel_search\nSlots:\n  minimum_hotel_rating: 4.0\n"
        "Missing: ['destination']",
        lambda intent: [
            *([f"expected category hotel_search, got {intent.primary_category}"]
              if intent.primary_category != IntentCategory.HOTEL_SEARCH else []),
            *([f"expected minimum_hotel_rating 4.0, got {intent.slots.minimum_hotel_rating!r}"]
              if intent.slots.minimum_hotel_rating != 4.0 else []),
            *([f"expected 'destination' in missing_slots, got {intent.missing_slots!r}"]
              if "destination" not in intent.missing_slots else []),
        ],
    )


def _case_4() -> CaseResult:
    return run_case(
        "TEST 4",
        "Vague quality language (negative test — must not hallucinate a number)",
        "I want a highly rated hotel in Whitefield.",
        "Intent: hotel_search\nSlots:\n  destination: Whitefield\n"
        "minimum_hotel_rating: None\nMissing: []",
        lambda intent: [
            *([f"expected category hotel_search, got {intent.primary_category}"]
              if intent.primary_category != IntentCategory.HOTEL_SEARCH else []),
            *([f"expected destination 'Whitefield', got {intent.slots.destination!r}"]
              if not _str_eq(intent.slots.destination, "Whitefield") else []),
            *([f"expected minimum_hotel_rating None (model must not invent a "
               f"number for 'highly rated'), got {intent.slots.minimum_hotel_rating!r}"]
              if intent.slots.minimum_hotel_rating is not None else []),
            *([f"expected missing_slots [], got {intent.missing_slots!r}"]
              if intent.missing_slots != [] else []),
        ],
    )


def _case_5() -> CaseResult:
    return run_case(
        "TEST 5",
        "General preference, not a current-search constraint",
        "My preference is usually highly rated hotels. I need something in Whitefield.",
        "Intent: hotel_search\nSlots:\n  destination: Whitefield\n"
        "minimum_hotel_rating: None\nMissing: []",
        lambda intent: [
            *([f"expected category hotel_search, got {intent.primary_category}"]
              if intent.primary_category != IntentCategory.HOTEL_SEARCH else []),
            *([f"expected destination 'Whitefield', got {intent.slots.destination!r}"]
              if not _str_eq(intent.slots.destination, "Whitefield") else []),
            *([f"expected minimum_hotel_rating None (general preference must not "
               f"become a current-request constraint), got "
               f"{intent.slots.minimum_hotel_rating!r}"]
              if intent.slots.minimum_hotel_rating is not None else []),
            *([f"expected missing_slots [], got {intent.missing_slots!r}"]
              if intent.missing_slots != [] else []),
        ],
    )


def _case_6() -> CaseResult:
    return run_case(
        "TEST 6",
        "Meeting location + rating",
        "Find me a hotel near my meeting in Whitefield. I want at least 4.5.",
        "Intent: hotel_search\nSlots:\n  destination: Whitefield\n  "
        "meeting_location: Whitefield\n  minimum_hotel_rating: 4.5\nMissing: []",
        lambda intent: [
            *([f"expected category hotel_search, got {intent.primary_category}"]
              if intent.primary_category != IntentCategory.HOTEL_SEARCH else []),
            *([f"expected destination 'Whitefield', got {intent.slots.destination!r}"]
              if not _str_eq(intent.slots.destination, "Whitefield") else []),
            *([f"expected meeting_location 'Whitefield', got {intent.slots.meeting_location!r}"]
              if not _str_eq(intent.slots.meeting_location, "Whitefield") else []),
            *([f"expected minimum_hotel_rating 4.5, got {intent.slots.minimum_hotel_rating!r}"]
              if intent.slots.minimum_hotel_rating != 4.5 else []),
            *([f"expected missing_slots [], got {intent.missing_slots!r}"]
              if intent.missing_slots != [] else []),
        ],
    )


def _case_7() -> CaseResult:
    return run_case(
        "TEST 7",
        "Rooms + adults + child + rating (non-inference check on children_ages)",
        "Book me one room for 2 adults and 1 child in Whitefield, and don't "
        "show me anything below 4 stars.",
        "Intent: hotel_search\nSlots:\n  destination: Whitefield\n  "
        "number_of_rooms: 1\n  number_of_adults: 2\n  number_of_children: 1\n  "
        "minimum_hotel_rating: 4.0\n  children_ages: None",
        lambda intent: [
            *([f"expected category hotel_search, got {intent.primary_category}"]
              if intent.primary_category != IntentCategory.HOTEL_SEARCH else []),
            *([f"expected destination 'Whitefield', got {intent.slots.destination!r}"]
              if not _str_eq(intent.slots.destination, "Whitefield") else []),
            *([f"expected number_of_rooms 1, got {intent.slots.number_of_rooms!r}"]
              if intent.slots.number_of_rooms != 1 else []),
            *([f"expected number_of_adults 2, got {intent.slots.number_of_adults!r}"]
              if intent.slots.number_of_adults != 2 else []),
            *([f"expected number_of_children 1, got {intent.slots.number_of_children!r}"]
              if intent.slots.number_of_children != 1 else []),
            *([f"expected minimum_hotel_rating 4.0, got {intent.slots.minimum_hotel_rating!r}"]
              if intent.slots.minimum_hotel_rating != 4.0 else []),
            *([f"model invented children_ages (must stay None/empty), got "
               f"{intent.slots.children_ages!r}"]
              if intent.slots.children_ages not in (None, []) else []),
        ],
    )


def _case_8() -> CaseResult:
    return run_case(
        "TEST 8",
        "Full ride request",
        "I need a bike from Bangalore airport to Whitefield tomorrow at 8 AM.",
        "Intent: ride_search\nSlots:\n  origin: Bangalore Airport\n  "
        "destination: Whitefield\n  date: tomorrow\n  time: 08:00\n  "
        "ride_type: bike\nMissing: []",
        lambda intent: [
            *([f"expected category ride_search, got {intent.primary_category}"]
              if intent.primary_category != IntentCategory.RIDE_SEARCH else []),
            *([f"expected origin 'Bangalore Airport', got {intent.slots.origin!r}"]
              if not _str_eq(intent.slots.origin, "Bangalore Airport") else []),
            *([f"expected destination 'Whitefield', got {intent.slots.destination!r}"]
              if not _str_eq(intent.slots.destination, "Whitefield") else []),
            *([f"expected ride_type 'bike', got {intent.slots.ride_type!r}"]
              if not _str_eq(intent.slots.ride_type, "bike") else []),
            *([f"expected time '08:00', got {intent.slots.time!r}"]
              if intent.slots.time != "08:00" else []),
            *([f"expected date to be populated (e.g. 'tomorrow'), got "
               f"{intent.slots.date!r}"]
              if not intent.slots.date else []),
            *([f"expected missing_slots [], got {intent.missing_slots!r}"]
              if intent.missing_slots != [] else []),
        ],
    )


def _case_9() -> CaseResult:
    return run_case(
        "TEST 9",
        "Missing hotel destination",
        "I need a hotel.",
        "Intent: hotel_search\nMissing: ['destination']",
        lambda intent: [
            *([f"expected category hotel_search, got {intent.primary_category}"]
              if intent.primary_category != IntentCategory.HOTEL_SEARCH else []),
            *([f"expected 'destination' in missing_slots, got {intent.missing_slots!r}"]
              if "destination" not in intent.missing_slots else []),
        ],
    )


def _case_10() -> CaseResult:
    return run_case(
        "TEST 10",
        "Missing ride origin and destination",
        "I need a ride.",
        "Intent: ride_search\nMissing: contains 'origin' and 'destination'",
        lambda intent: [
            *([f"expected category ride_search, got {intent.primary_category}"]
              if intent.primary_category != IntentCategory.RIDE_SEARCH else []),
            *([f"expected 'origin' in missing_slots, got {intent.missing_slots!r}"]
              if "origin" not in intent.missing_slots else []),
            *([f"expected 'destination' in missing_slots, got {intent.missing_slots!r}"]
              if "destination" not in intent.missing_slots else []),
        ],
    )


_ALL_CASES: list[Callable[[], CaseResult]] = [
    _case_1, _case_2, _case_3, _case_4, _case_5,
    _case_6, _case_7, _case_8, _case_9, _case_10,
]


# ------------------------------------------------------------------
# pytest entry points
# ------------------------------------------------------------------

def test_1_basic_hotel_no_rating_constraint():
    """
    Verifies the basic hotel-search path: explicit destination and
    adult count are extracted, and no optional constraint is invented.

    This confirms Stage 1's core contract — natural language in,
    structured slots out — without any hallucinated extras.

    Future relevance: destination and adult count feed directly into
    the hotel search and eventual booking/UI automation layers.
    """
    result = _case_1()
    assert result.passed, "; ".join(result.failures)


def test_2_explicit_numeric_rating_floor():
    """
    Verifies that an explicitly stated numeric rating floor is
    correctly extracted into minimum_hotel_rating.

    This constraint will later be used to filter hotel search results
    (hotel.rating >= minimum_hotel_rating) before recommendation
    ranking — losing it here means bad hotels wouldn't get filtered.

    Future relevance: consumed directly by the future filtering step
    in the hotel search/recommendation pipeline.
    """
    result = _case_2()
    assert result.passed, "; ".join(result.failures)


def test_3_below_x_phrasing():
    """
    Verifies that "below X" phrasing is understood as a minimum rating
    floor, and that missing-slot detection still fires correctly when
    a valid slot is present but the required destination is not.

    This matters because natural rating language varies widely, and
    missing_slots must stay accurate regardless of what else was said.

    Future relevance: a missing destination can later trigger a
    clarification question before hotel search begins.
    """
    result = _case_3()
    assert result.passed, "; ".join(result.failures)


def test_4_vague_quality_language_no_hallucination():
    """
    Negative test: verifies the model does NOT invent a numeric rating
    for vague language like "highly rated".

    This is critical because a hallucinated minimum_hotel_rating would
    silently over-filter real hotel results later in the pipeline.

    Future relevance: vague preferences are meant to be handled later
    by user memory + the recommendation engine, not the intent parser.
    """
    result = _case_4()
    assert result.passed, "; ".join(result.failures)


def test_5_general_preference_not_current_constraint():
    """
    Verifies the distinction between a long-term stated preference
    ("usually highly rated") and an explicit constraint for this
    specific search.

    This matters because conflating the two would corrupt the current
    search with information that belongs in user memory instead.

    Future relevance: this type of statement is meant to eventually
    be captured by the memory/recommendation system, not Stage 1.
    """
    result = _case_5()
    assert result.passed, "; ".join(result.failures)


def test_6_meeting_location_plus_rating():
    """
    Verifies that multiple related hotel-context fields (destination,
    meeting_location, minimum_hotel_rating) are all extracted from a
    single natural-language request.

    This matters because real user queries often combine several
    pieces of context in one sentence.

    Future relevance: meeting_location will later support hotel
    recommendation and the cross-domain ride-suggestion workflow.
    """
    result = _case_6()
    assert result.passed, "; ".join(result.failures)


def test_7_rooms_adults_child_and_rating_no_age_invention():
    """
    Verifies extraction of occupancy details (rooms, adults, children)
    alongside a rating constraint, while confirming the model does not
    invent a child's age that was never stated.

    Inventing an age would be a serious correctness issue since it
    would be passed downstream as if the user had actually said it.

    Future relevance: these values will be required by the future
    hotel UI/booking automation layer.
    """
    result = _case_7()
    assert result.passed, "; ".join(result.failures)


def test_8_full_ride_request():
    """
    Verifies that the ride domain is handled correctly end-to-end:
    origin, destination, date, time, and ride_type all extracted from
    one natural-language ride request.

    This is the ride-domain counterpart to the hotel tests and
    confirms Stage 1 isn't hotel-biased in its extraction quality.

    Future relevance: the structured result feeds the future ride
    search/provider and ride booking automation layer.
    """
    result = _case_8()
    assert result.passed, "; ".join(result.failures)


def test_9_missing_hotel_destination():
    """
    Verifies that missing_slots correctly flags a hotel search with no
    location information at all.

    This matters because the future orchestrator relies on
    missing_slots to know when to ask a clarifying question instead of
    searching with incomplete data.

    Future relevance: directly drives the future clarification-prompt
    logic before hotel search begins.
    """
    result = _case_9()
    assert result.passed, "; ".join(result.failures)


def test_10_missing_ride_origin_and_destination():
    """
    Verifies that missing_slots correctly flags both required ride
    fields (origin and destination) when neither is stated.

    This matters because the ride workflow cannot start a search
    without both a pickup and a drop-off point.

    Future relevance: drives future clarifying questions like "where
    should I pick you up?" and "where are you going?".
    """
    result = _case_10()
    assert result.passed, "; ".join(result.failures)


# ------------------------------------------------------------------
# Manual run entry point
# ------------------------------------------------------------------

def _run_all_manual() -> int:
    results = [case() for case in _ALL_CASES]

    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed

    print("=" * 60)
    print("INTENT PARSER TEST SUMMARY")
    print("=" * 60)
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total : {len(results)}")
    print()
    print(f"Overall: {'PASS' if failed == 0 else 'FAIL'}")

    if failed:
        print("\nFailed cases:")
        for r in results:
            if not r.passed:
                reason = "; ".join(r.failures) if r.failures else "unknown failure"
                print(f"  - {r.name} ({r.title}): {reason}")

    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(_run_all_manual())
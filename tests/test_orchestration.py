import pytest
from app.orchestration.states import TravelState, StateContext
from app.orchestration.state_machine import TravelStateMachine
from app.orchestration.orchestrator import TravelOrchestrator
from app.models.trip import TripRequest


def test_state_machine_transitions():
    ctx = StateContext(session_id="s1", user_id="u1")
    assert ctx.current_state == TravelState.IDLE

    TravelStateMachine.transition(ctx, TravelState.EXTRACTING_INTENT)
    assert ctx.current_state == TravelState.EXTRACTING_INTENT

    with pytest.raises(ValueError):
        # Disallowed jump from EXTRACTING_INTENT directly to COMPLETED
        TravelStateMachine.transition(ctx, TravelState.COMPLETED)


@pytest.mark.asyncio
async def test_orchestrator_planning_pipeline():
    orchestrator = TravelOrchestrator()
    request = TripRequest(
        user_id="user_123",
        query="Plan a 2-day trip to Bengaluru under 20000"
    )

    context = await orchestrator.plan_trip(request)
    assert context.current_state == TravelState.AWAITING_USER_CONFIRMATION
    assert context.generated_plan is not None
    assert context.generated_plan.destination == "Bengaluru"
    assert len(context.generated_plan.itinerary) > 0

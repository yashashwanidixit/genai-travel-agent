from fastapi import APIRouter, HTTPException, status
from app.models.trip import TripPlan, TripRequest
from app.orchestration.orchestrator import TravelOrchestrator
from app.orchestration.states import StateContext

router = APIRouter()
orchestrator = TravelOrchestrator()


@router.post("/plan", response_model=StateContext, status_code=status.HTTP_200_OK)
async def plan_trip(request: TripRequest):
    """Plan a personalized trip from natural language query or structured constraints."""
    context = await orchestrator.plan_trip(request)
    if context.error_message:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=context.error_message
        )
    return context


@router.get("/sample-plan", response_model=TripPlan)
async def get_sample_plan():
    """Returns a sample trip plan demonstration."""
    sample_request = TripRequest(
        user_id="user_123",
        query="Plan a luxury weekend trip to Bengaluru under 25000 with a 5 star hotel and swimming pool"
    )
    context = await orchestrator.plan_trip(sample_request)
    if not context.generated_plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan could not be generated")
    return context.generated_plan

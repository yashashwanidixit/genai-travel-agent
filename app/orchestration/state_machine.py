from app.orchestration.states import TravelState, StateContext


class TravelStateMachine:
    """Manages legal transitions and guards between travel planning states."""

    ALLOWED_TRANSITIONS = {
        TravelState.IDLE: [TravelState.EXTRACTING_INTENT],
        TravelState.EXTRACTING_INTENT: [TravelState.SEARCHING_HOTELS, TravelState.FAILED],
        TravelState.SEARCHING_HOTELS: [TravelState.SEARCHING_RIDES, TravelState.FAILED],
        TravelState.SEARCHING_RIDES: [TravelState.RANKING_OPTIONS, TravelState.FAILED],
        TravelState.RANKING_OPTIONS: [TravelState.SYNTHESIZING_PLAN, TravelState.FAILED],
        TravelState.SYNTHESIZING_PLAN: [TravelState.AWAITING_USER_CONFIRMATION, TravelState.FAILED],
        TravelState.AWAITING_USER_CONFIRMATION: [TravelState.BOOKING_EXECUTION, TravelState.IDLE, TravelState.FAILED],
        TravelState.BOOKING_EXECUTION: [TravelState.COMPLETED, TravelState.FAILED],
        TravelState.COMPLETED: [TravelState.IDLE],
        TravelState.FAILED: [TravelState.IDLE],
    }

    @classmethod
    def can_transition(cls, from_state: TravelState, to_state: TravelState) -> bool:
        return to_state in cls.ALLOWED_TRANSITIONS.get(from_state, [])

    @classmethod
    def transition(cls, context: StateContext, to_state: TravelState) -> StateContext:
        if not cls.can_transition(context.current_state, to_state):
            raise ValueError(f"Illegal state transition from {context.current_state} to {to_state}")
        context.current_state = to_state
        return context

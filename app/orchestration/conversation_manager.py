from __future__ import annotations

from typing import Optional

from app.models.intent import TravelIntent
from app.normalization.intent_normalizer import normalize_intent
from app.orchestration.clarification import next_clarification_question
from app.orchestration.requirement_checker import check_requirements, is_ready


class ConversationManager:
    """Minimal in-memory pending-intent state for a single CLI session.

    Holds at most ONE incomplete intent while waiting for the user to
    answer a clarification question, and remembers which single slot
    is currently being asked about so the next raw user message is
    merged into that field rather than treated as a brand-new query.

    Deliberately simple: no database, no persistence across process
    restarts, no multi-turn memory beyond the current pending intent.
    A future stage will replace this with real orchestration/memory.
    """

    def __init__(self):
        self._pending: Optional[TravelIntent] = None
        self._awaiting_slot: Optional[str] = None

    def has_pending(self) -> bool:
        return self._pending is not None

    def start_new_intent(self, raw_intent: TravelIntent) -> TravelIntent:
        """Normalizes a freshly LLM-extracted TravelIntent and runs the
        deterministic requirement check. If required fields are
        missing, stores it as pending; otherwise clears any pending
        state (a new, complete request doesn't need one).
        """
        normalized = normalize_intent(raw_intent)
        checked = check_requirements(normalized)
        self._update_pending_state(checked)
        return checked

    def provide_answer(self, answer_text: str) -> TravelIntent:
        """Merges a raw user answer into the single slot that was
        being asked about, re-normalizes, and re-checks requirements.
        """
        if self._pending is None or self._awaiting_slot is None:
            raise RuntimeError(
                "provide_answer() called with no pending clarification."
            )

        updated_slots = self._pending.slots.model_copy(
            update={self._awaiting_slot: answer_text}
        )
        updated_intent = self._pending.model_copy(
            update={"slots": updated_slots}
        )

        normalized = normalize_intent(updated_intent)
        checked = check_requirements(normalized)
        self._update_pending_state(checked)
        return checked

    def current_question(self) -> Optional[str]:
        if self._pending is None:
            return None
        return next_clarification_question(self._pending)

    def clear(self) -> None:
        self._pending = None
        self._awaiting_slot = None

    def _update_pending_state(self, checked_intent: TravelIntent) -> None:
        if is_ready(checked_intent):
            self._pending = None
            self._awaiting_slot = None
        else:
            self._pending = checked_intent
            self._awaiting_slot = checked_intent.missing_slots[0]
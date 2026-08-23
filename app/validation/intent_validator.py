from __future__ import annotations

from app.models.intent import TravelIntent


def validate_destination(intent: TravelIntent) -> TravelIntent:
    """
    Removes an extracted destination when the destination does not
    appear explicitly in the user's current query.

    This is intentionally conservative. It is designed to catch
    obvious LLM hallucinations such as:

        User: "I want a hotel"
        LLM: destination = "Whitefield"

    It does not attempt to perform semantic location understanding.
    """

    destination = intent.slots.destination

    if destination is None:
        return intent

    raw_query = intent.raw_query.lower()
    destination_text = destination.strip().lower()

    if destination_text not in raw_query:
        normalized_slots = intent.slots.model_copy(
            update={"destination": None}
        )

        updated_intent = intent.model_copy(
            update={"slots": normalized_slots}
        )
        return _update_missing_destination(updated_intent)
        

    return _update_missing_destination(intent)




def _update_missing_destination(intent: TravelIntent) -> TravelIntent:
    """Keeps missing_slots consistent with the validated destination."""

    missing = list(intent.missing_slots)

    if (
        intent.primary_category == IntentCategory.HOTEL_SEARCH
        and intent.slots.destination is None
    ):
        if "destination" not in missing:
            missing.append("destination")
    else:
        missing = [slot for slot in missing if slot != "destination"]

    return intent.model_copy(
        update={"missing_slots": missing}
    )
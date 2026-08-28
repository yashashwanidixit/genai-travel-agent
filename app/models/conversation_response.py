from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.models.hotel_context import HotelContext


@dataclass
class ConversationResponse:
    """
    Result returned by the ConversationHandler after processing
    one user message.

    This model is deliberately independent of the CLI or Android UI.

    The frontend decides how to display this response.
    """

    status: str

    question: Optional[str] = None

    hotel_contexts: Optional[list[HotelContext]] = None

    message: Optional[str] = None
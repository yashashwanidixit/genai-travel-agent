from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class EpisodicMessage(BaseModel):
    role: str  # user, assistant, system
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, str] = Field(default_factory=dict)


class EpisodicMemory:
    """Stores sequential conversation and action turns per session / user."""

    def __init__(self):
        self._store: Dict[str, List[EpisodicMessage]] = {}

    def add_turn(self, session_id: str, role: str, content: str, metadata: Optional[Dict[str, str]] = None) -> EpisodicMessage:
        if session_id not in self._store:
            self._store[session_id] = []
        msg = EpisodicMessage(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self._store[session_id].append(msg)
        return msg

    def get_history(self, session_id: str, limit: int = 10) -> List[EpisodicMessage]:
        turns = self._store.get(session_id, [])
        return turns[-limit:]

    def clear(self, session_id: str) -> None:
        if session_id in self._store:
            self._store[session_id] = []

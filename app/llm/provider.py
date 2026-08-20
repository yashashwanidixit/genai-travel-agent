from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract interface for any local/remote LLM backend used by IntentAgent.

    Stage 1 only implements OllamaProvider, but IntentAgent must never
    depend on Ollama directly so the backend can be swapped later
    without changing agent logic.
    """

    @abstractmethod
    def generate_structured(self, system_prompt: str, user_prompt: str) -> str:
        """Send a system + user prompt to the model and return the raw
        text response. The caller is responsible for parsing/validating it.
        """
        raise NotImplementedError
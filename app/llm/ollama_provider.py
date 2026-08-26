from __future__ import annotations

import os

import requests

from app.llm.provider import LLMProvider
from app.monitoring.performance_monitor import PerformanceTimer


class OllamaCallResult:
    """Wraps a single Ollama call's text output plus timing/status info,
    so IntentAgent can report LLM-specific timing without re-implementing
    the HTTP call itself.
    """

    def __init__(
        self,
        text: str,
        llm_time: float,
        connected: bool,
        error: str | None = None,
    ):
        self.text = text
        self.llm_time = llm_time
        self.connected = connected
        self.error = error


class OllamaProvider(LLMProvider):
    """Talks to a local Ollama server running Qwen3 4B.

    Uses Ollama's /api/chat endpoint with format="json" so the model is
    constrained to return valid JSON rather than free text.

    Adds (on top of the original Stage 1 implementation):
    - keep_alive, so the model stays loaded in memory between calls
    - num_thread, configurable CPU thread count
    - per-call timing and connection status, exposed via
      generate_structured_with_metadata()
    """

    def __init__(
        self,
        model: str | None = None,
        host: str | None = None,
        timeout: int = 120,
        keep_alive: str | None = None,
        num_thread: int | None = None,
    ):
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
        self.host = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.timeout = timeout
        self.keep_alive = keep_alive or os.getenv("OLLAMA_KEEP_ALIVE", "30m")
        self.num_thread = num_thread or int(os.getenv("OLLAMA_NUM_THREADS", "12"))

    def generate_structured(self, system_prompt: str, user_prompt: str) -> str:
        """Original interface required by LLMProvider. Kept working
        unchanged for anything that only needs the text back.
        """
        return self.generate_structured_with_metadata(
            system_prompt, user_prompt
        ).text

    def generate_structured_with_metadata(
        self, system_prompt: str, user_prompt: str,
        response_schema : dict| None = None ,
    ) -> OllamaCallResult:
        """Same call as generate_structured, but also returns LLM-only
        timing and connection status for performance reporting.
        """
        url = f"{self.host}/api/chat"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "format": response_schema if response_schema is not None else "json",
            "stream": False,
            "keep_alive": self.keep_alive,
            "options": {
                "temperature": 0,
                "num_thread": self.num_thread,
            },
        }

        timer = PerformanceTimer()
        timer.start()

        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
        except requests.exceptions.ConnectionError as exc:
            llm_time = timer.stop()
            error = (
                f"Could not connect to Ollama at {self.host}. "
                "Is 'ollama serve' running?"
            )
            raise RuntimeError(error) from exc
        except requests.exceptions.Timeout as exc:
            llm_time = timer.stop()
            raise RuntimeError(
                f"Ollama did not respond within {self.timeout}s."
            ) from exc
        except requests.exceptions.HTTPError as exc:
            llm_time = timer.stop()
            raise RuntimeError(f"Ollama returned an error: {exc}") from exc

        llm_time = timer.stop()

        data = response.json()
        content = data.get("message", {}).get("content", "")
        if not content:
            raise RuntimeError(f"Ollama returned an empty response: {data}")

        return OllamaCallResult(
            text=content,
            llm_time=llm_time,
            connected=True,
            error=None,
        )
from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


class PerformanceTimer:
    """Minimal start/stop wall-clock timer.

    Usage:
        timer = PerformanceTimer()
        timer.start()
        ...
        timer.stop()
        timer.elapsed_seconds
    """

    def __init__(self):
        self._start: Optional[float] = None
        self._end: Optional[float] = None

    def start(self) -> None:
        self._start = time.perf_counter()
        self._end = None

    def stop(self) -> float:
        if self._start is None:
            raise RuntimeError("Timer.stop() called before start()")
        self._end = time.perf_counter()
        return self.elapsed_seconds

    @property
    def elapsed_seconds(self) -> float:
        if self._start is None:
            return 0.0
        end = self._end if self._end is not None else time.perf_counter()
        return end - self._start

    def __enter__(self) -> "PerformanceTimer":
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()


@dataclass
class PerformanceMetrics:
    """A single record of one intent-parsing attempt's performance."""

    status: str  # "SUCCESS" or "FAILED"
    total_time: float
    llm_time: float
    overhead_time: float
    timestamp: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None
    possible_cold_start: bool = False

    def print_report(self) -> None:
        print("\n[Performance]")
        print(f"Status           : {self.status}")
        print(f"LLM inference    : {self.llm_time:.2f} s")
        print(f"Total parsing    : {self.total_time:.2f} s")
        print(f"Overhead         : {self.overhead_time:.2f} s")
        if self.possible_cold_start:
            print("Note             : first observed inference — possible cold start")
        if self.error:
            print(f"Error            : {self.error}")


class ColdStartTracker:
    """Tracks whether we've seen an inference yet, purely to label the
    first one as a *possible* cold start. Does not claim certainty and
    does not perform any warm-up requests itself.
    """

    def __init__(self):
        self._seen_first_inference = False

    def is_possible_cold_start(self) -> bool:
        was_first = not self._seen_first_inference
        self._seen_first_inference = True
        return was_first
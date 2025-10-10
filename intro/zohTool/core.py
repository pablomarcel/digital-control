from __future__ import annotations
import math
from typing import List
from .apis import IntervalEvent

class ZOHModel:
    """Parameter container for ZOH behavior."""
    def __init__(self, Ts: float, delay: float = 0.0, droop_tau: float = float('inf'), offset: float = 0.0):
        if Ts <= 0:
            raise ValueError("Ts must be > 0")
        if delay < 0:
            raise ValueError("delay must be >= 0")
        if not (math.isfinite(droop_tau) or math.isinf(droop_tau)):
            raise ValueError("droop_tau must be finite or inf")
        self.Ts = Ts
        self.delay = delay
        self.droop_tau = droop_tau
        self.offset = offset

class ZOHSimulator:
    """Build interval-wise events for ZOH output."""
    def __init__(self, model: ZOHModel):
        self.model = model

    def expand(self, u: List[float]) -> List[IntervalEvent]:
        Ts = self.model.Ts
        delay = self.model.delay
        tau = self.model.droop_tau
        offset = self.model.offset
        events: List[IntervalEvent] = []
        for k, uk in enumerate(u):
            t0 = k * Ts + delay
            t1 = (k + 1) * Ts + delay
            y0 = uk + offset
            if math.isfinite(tau) and tau > 0.0:
                y1 = y0 * math.exp(-(t1 - t0) / tau)
            else:
                y1 = y0
            events.append(IntervalEvent(k=k, t0=t0, t1=t1, u_in=uk, y0=y0, y1=y1))
        return events

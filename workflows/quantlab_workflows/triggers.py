"""Trigger event representations for AI workflows (ADR 0008, Element 1)."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Any

from quantlab_workflows.types import TriggerType


@dataclass(frozen=True)
class TriggerEvent:
    """The trigger initiating an AI workflow.

    Parameters
    ----------
    trigger_type : TriggerType
        The category of the trigger (MANUAL, SCHEDULE, ANOMALY, WEBHOOK).
    source : str
        The origin or subsystem that fired the event (e.g. 'cli', 'cron_daily').
    payload : dict[str, Any]
        Structured payload carrying parameters, symbols, or anomaly details.
    timestamp : dt.datetime | None, optional
        UTC timestamp when the trigger occurred. Defaults to current UTC time.
    """

    trigger_type: TriggerType
    source: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: dt.datetime = field(default_factory=lambda: dt.datetime.now(dt.UTC))

    def to_dict(self) -> dict[str, Any]:
        """Convert the trigger event to a JSON-compatible dictionary."""
        return {
            "trigger_type": str(self.trigger_type),
            "source": self.source,
            "payload": dict(self.payload),
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TriggerEvent:
        """Reconstruct a TriggerEvent from a dictionary."""
        timestamp = dt.datetime.fromisoformat(data["timestamp"])
        return cls(
            trigger_type=TriggerType(data["trigger_type"]),
            source=str(data["source"]),
            payload=dict(data.get("payload", {})),
            timestamp=timestamp,
        )

    @classmethod
    def manual(cls, prompt: str, **kwargs: Any) -> TriggerEvent:
        """Create a manual researcher trigger event."""
        payload = {"prompt": prompt, **kwargs}
        return cls(trigger_type=TriggerType.MANUAL, source="researcher", payload=payload)

    @classmethod
    def anomaly(cls, symbol: str, metric: str, value: float, threshold: float) -> TriggerEvent:
        """Create an anomaly detection trigger event."""
        payload = {
            "symbol": symbol,
            "metric": metric,
            "value": value,
            "threshold": threshold,
        }
        return cls(
            trigger_type=TriggerType.ANOMALY,
            source="volatility_sentinel",
            payload=payload,
        )

    @classmethod
    def schedule(cls, frequency: str, target: str) -> TriggerEvent:
        """Create a scheduled routine trigger event."""
        payload = {"frequency": frequency, "target": target}
        return cls(trigger_type=TriggerType.SCHEDULE, source="cron", payload=payload)

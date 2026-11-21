"""Tests for workflow types, messages, and trigger events (ADR 0008)."""

from __future__ import annotations

from quantlab_workflows.triggers import TriggerEvent
from quantlab_workflows.types import AgentMessage, AgentRole, TriggerType


def test_trigger_event_manual() -> None:
    trigger = TriggerEvent.manual("Investigate volatility regime", symbol="PETR4.SA")
    assert trigger.trigger_type == TriggerType.MANUAL
    assert trigger.source == "researcher"
    assert trigger.payload["prompt"] == "Investigate volatility regime"
    assert trigger.payload["symbol"] == "PETR4.SA"

    as_dict = trigger.to_dict()
    reconstructed = TriggerEvent.from_dict(as_dict)
    assert reconstructed.trigger_type == trigger.trigger_type
    assert reconstructed.source == trigger.source
    assert reconstructed.payload == trigger.payload
    assert reconstructed.timestamp == trigger.timestamp


def test_trigger_event_anomaly() -> None:
    trigger = TriggerEvent.anomaly("VALE3.SA", metric="volatility", value=0.45, threshold=0.30)
    assert trigger.trigger_type == TriggerType.ANOMALY
    assert trigger.source == "volatility_sentinel"
    assert trigger.payload["symbol"] == "VALE3.SA"
    assert trigger.payload["value"] == 0.45
    assert trigger.payload["threshold"] == 0.30


def test_trigger_event_schedule() -> None:
    trigger = TriggerEvent.schedule("daily", "market_close")
    assert trigger.trigger_type == TriggerType.SCHEDULE
    assert trigger.source == "cron"
    assert trigger.payload["frequency"] == "daily"


def test_agent_message_roundtrip() -> None:
    msg = AgentMessage(
        role=AgentRole.QUANTITATIVE,
        agent_name="Risk Bot",
        content="Volatility is high.",
        metadata={"regime": "turbulent"},
    )
    as_dict = msg.to_dict()
    assert as_dict["role"] == "quantitative"
    assert as_dict["agent_name"] == "Risk Bot"

    restored = AgentMessage.from_dict(as_dict)
    assert restored.role == msg.role
    assert restored.agent_name == msg.agent_name
    assert restored.content == msg.content
    assert restored.metadata == msg.metadata

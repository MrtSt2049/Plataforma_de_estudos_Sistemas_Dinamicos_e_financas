"""Tests for WorkflowContext (ADR 0008, Element 2)."""

from __future__ import annotations

import pandas as pd

from quantlab.research import hash_data
from quantlab_workflows.context import WorkflowContext
from quantlab_workflows.triggers import TriggerEvent
from quantlab_workflows.types import AgentMessage, AgentRole


def test_workflow_context_initialization_and_metrics() -> None:
    trigger = TriggerEvent.manual("Test research hypothesis")
    ctx = WorkflowContext(trigger=trigger, symbol="SPY")

    assert ctx.symbol == "SPY"
    assert ctx.data is None
    assert ctx.data_hash is None

    ctx.record_metric("volatility", 0.185)
    assert ctx.metrics["volatility"] == 0.185

    msg = AgentMessage(
        role=AgentRole.HYPOTHESIS,
        agent_name="Hypothesis Agent",
        content="Testing hypothesis.",
    )
    ctx.add_message(msg)
    assert len(ctx.messages) == 1
    assert ctx.messages[0] == msg


def test_workflow_context_set_data_computes_hash() -> None:
    trigger = TriggerEvent.manual("Analyze series")
    ctx = WorkflowContext(trigger=trigger)

    df = pd.DataFrame(
        {"close": [10.0, 11.0, 10.5, 12.0]},
        index=pd.date_range("2024-01-01", periods=4, freq="D", tz="UTC"),
    )
    ctx.set_data(df)

    assert ctx.data is not None
    assert ctx.data_hash is not None
    expected_hash = hash_data(df)
    assert ctx.data_hash == expected_hash


def test_workflow_context_summary_text() -> None:
    trigger = TriggerEvent.manual("Run study")
    ctx = WorkflowContext(trigger=trigger, symbol="PETR4.SA")
    ctx.hypothesis = "Volatility clusters in 2024"
    ctx.record_metric("annualized_volatility", 0.28)

    summary = ctx.summary_text()
    assert "PETR4.SA" in summary
    assert "Volatility clusters in 2024" in summary
    assert "annualized_volatility: 0.28" in summary

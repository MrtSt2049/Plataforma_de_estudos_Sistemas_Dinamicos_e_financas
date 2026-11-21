"""Integration tests for the complete 5-element AI workflow orchestrator (ADR 0008)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from quantlab_workflows.actions import (
    create_logistic_study,
    create_lorenz_study,
    create_market_risk_study,
)
from quantlab_workflows.context import WorkflowContext
from quantlab_workflows.orchestrator import WorkflowOrchestrator
from quantlab_workflows.providers import MockLLMProvider
from quantlab_workflows.records import WorkflowRecord
from quantlab_workflows.triggers import TriggerEvent
from quantlab_workflows.types import WorkflowStatus


def test_orchestrator_market_risk_workflow() -> None:
    # 1. Trigger
    trigger = TriggerEvent.manual("Analyze volatility and tail risk for asset", symbol="PETR4.SA")

    # 2. Context with data
    rng = np.random.default_rng(42)
    prices = 30.0 * np.exp(np.cumsum(rng.normal(0.0002, 0.02, size=150)))
    dates = pd.date_range("2024-01-01", periods=150, freq="B", tz="UTC")
    df = pd.DataFrame({"close": prices}, index=dates)

    context = WorkflowContext(trigger=trigger, symbol="PETR4.SA")
    context.set_data(df)

    provider = MockLLMProvider(
        responses={
            "hypothesis": "Hypothesis: Asset exhibits annualized volatility exceeding 20%.",
            "metrics": "Quantitative analysis confirms elevated volatility and fat tails.",
            "final": (
                "Scientific Report:\n"
                "1. Verdict: Supported. The empirical data confirms the volatility hypothesis.\n"
                "2. Summary: Annualized volatility and VaR are within high turbulence bounds."
            ),
        },
        default_response="Mock analytical deliberation.",
    )

    orchestrator = WorkflowOrchestrator(provider=provider)
    study_fn = create_market_risk_study(df["close"])

    # Run the 5 elements
    record = orchestrator.run(context=context, study_fn=study_fn, study_name="PETR4 Risk Study")

    # Verify execution record
    assert record.status == WorkflowStatus.COMPLETED
    assert "volatility exceeding 20%" in record.hypothesis
    assert "annualized_volatility" in record.metrics
    assert record.metrics["annualized_volatility"] > 0.0
    assert record.data_hash == context.data_hash
    assert record.experiment_run is not None
    assert record.experiment_run.experiment.hypothesis == record.hypothesis
    assert len(record.messages) >= 4  # Hypothesis, Quant, Dynamics, Synthesizer

    # Verify serialization
    as_dict = record.to_dict()
    restored = WorkflowRecord.from_dict(as_dict)
    assert restored.workflow_id == record.workflow_id
    assert restored.status == record.status
    assert restored.hypothesis == record.hypothesis
    assert restored.metrics == record.metrics
    assert restored.data_hash == record.data_hash


def test_orchestrator_lorenz_workflow() -> None:
    trigger = TriggerEvent.anomaly("lorenz", metric="divergence", value=2.5, threshold=1.0)
    context = WorkflowContext(
        trigger=trigger,
        symbol="lorenz",
        model="lorenz",
        parameters={"sigma": 10.0, "rho": 28.0, "beta": 8.0 / 3.0, "dt": 0.01, "n_steps": 100},
        seed=101,
    )

    provider = MockLLMProvider(
        default_response="Lorenz simulation confirms trajectory is governed by strange attractor."
    )
    orchestrator = WorkflowOrchestrator(provider=provider)
    study_fn = create_lorenz_study()

    record = orchestrator.run(context=context, study_fn=study_fn, study_name="Lorenz Chaos Check")

    assert record.status == WorkflowStatus.COMPLETED
    assert record.metrics["is_above_hopf"] == 1.0
    assert "hopf_threshold" in record.metrics
    assert record.experiment_run is not None


def test_orchestrator_logistic_workflow() -> None:
    trigger = TriggerEvent.schedule("weekly", "logistic_bifurcation")
    context = WorkflowContext(
        trigger=trigger,
        symbol="logistic_map",
        model="logistic_map",
        parameters={"r": 3.9, "n_steps": 1_000},
        seed=77,
    )

    orchestrator = WorkflowOrchestrator()
    study_fn = create_logistic_study()

    record = orchestrator.run(context=context, study_fn=study_fn)

    assert record.status == WorkflowStatus.COMPLETED
    assert record.metrics["is_chaotic"] == 1.0
    assert record.metrics["lyapunov_exponent"] > 0.0


def test_orchestrator_handles_failure_gracefully() -> None:
    trigger = TriggerEvent.manual("Failing study")
    context = WorkflowContext(trigger=trigger)

    def failing_study(params: object, seeds: object) -> dict[str, float]:
        raise RuntimeError("Simulated mathematical failure")

    orchestrator = WorkflowOrchestrator()
    record = orchestrator.run(context=context, study_fn=failing_study)

    assert record.status == WorkflowStatus.FAILED
    assert "Simulated mathematical failure" in record.final_synthesis

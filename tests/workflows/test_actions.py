"""Tests for deterministic actions and Research Core integration (ADR 0008, Element 4)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from quantlab.research import ExperimentRun, SeedManager
from quantlab_workflows.actions import (
    ActionExecutor,
    create_logistic_study,
    create_lorenz_study,
    create_market_risk_study,
)
from quantlab_workflows.context import WorkflowContext
from quantlab_workflows.triggers import TriggerEvent


def test_create_market_risk_study() -> None:
    # Generate reproducible synthetic prices
    rng = np.random.default_rng(123)
    steps = 100
    prices = 100.0 * np.exp(np.cumsum(rng.normal(0.0005, 0.015, size=steps)))
    dates = pd.date_range("2024-01-01", periods=steps, freq="B", tz="UTC")
    series = pd.Series(prices, index=dates)

    study_fn = create_market_risk_study(series)
    seeds = SeedManager(42)
    metrics = study_fn({}, seeds)

    assert "annualized_volatility" in metrics
    assert "sharpe_ratio" in metrics
    assert "max_drawdown" in metrics
    assert "var_95" in metrics
    assert "cvar_95" in metrics
    assert metrics["annualized_volatility"] > 0.0
    assert metrics["max_drawdown"] <= 0.0


def test_create_lorenz_study() -> None:
    study_fn = create_lorenz_study()
    seeds = SeedManager(7)
    parameters = {"sigma": 10.0, "rho": 28.0, "beta": 8.0 / 3.0, "dt": 0.01, "n_steps": 100}
    metrics = study_fn(parameters, seeds)

    assert "hopf_threshold" in metrics
    assert "x_mean" in metrics
    assert "is_above_hopf" in metrics
    assert metrics["is_above_hopf"] == 1.0


def test_create_logistic_study() -> None:
    study_fn = create_logistic_study()
    seeds = SeedManager(99)
    parameters = {"r": 3.8, "n_steps": 1_000}
    metrics = study_fn(parameters, seeds)

    assert "lyapunov_exponent" in metrics
    assert "is_chaotic" in metrics
    # r=3.8 is famously chaotic (positive Lyapunov exponent)
    assert metrics["lyapunov_exponent"] > 0.0
    assert metrics["is_chaotic"] == 1.0


def test_action_executor_runs_experiment() -> None:
    executor = ActionExecutor()
    trigger = TriggerEvent.manual("Test run study")
    ctx = WorkflowContext(
        trigger=trigger,
        hypothesis="Lorenz is above Hopf bifurcation",
        model="lorenz",
        parameters={"sigma": 10.0, "rho": 28.0, "beta": 8.0 / 3.0, "dt": 0.01, "n_steps": 100},
        seed=42,
    )

    study_fn = create_lorenz_study()
    run = executor.execute_study(ctx, study_fn, study_name="Lorenz Hopf Test")

    assert isinstance(run, ExperimentRun)
    assert run.experiment.hypothesis == "Lorenz is above Hopf bifurcation"
    assert "hopf_threshold" in ctx.metrics
    assert "is_above_hopf" in ctx.metrics
    assert ctx.metrics["is_above_hopf"] == 1.0

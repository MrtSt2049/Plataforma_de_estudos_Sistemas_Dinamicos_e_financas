"""Execution of scientific actions and reproducible experiments (ADR 0008, Element 4)."""

from __future__ import annotations

from collections.abc import Callable, Mapping

import numpy as np
import pandas as pd

from quantlab.analysis import (
    annualized_volatility,
    historical_cvar,
    historical_var,
    max_drawdown,
    sharpe_ratio,
    simple_returns,
)
from quantlab.dynamics import (
    LorenzParameters,
    logistic_lyapunov_exponent,
    lorenz_hopf_rho,
    simulate_logistic_map,
    simulate_lorenz,
)
from quantlab.research import Experiment, ExperimentRun, JsonValue, SeedManager, run_experiment
from quantlab_workflows.context import WorkflowContext

ExperimentStudyFn = Callable[[Mapping[str, JsonValue], SeedManager], Mapping[str, float]]


def create_market_risk_study(series: pd.Series) -> ExperimentStudyFn:
    """Create an experiment study function for market risk analysis.

    Parameters
    ----------
    series : pd.Series
        Clean price series (e.g. close prices).

    Returns
    -------
    ExperimentStudyFn
        Callable taking (parameters, seeds) and returning metrics dictionary.
    """
    returns = simple_returns(series)

    def study(parameters: Mapping[str, JsonValue], seeds: SeedManager) -> Mapping[str, float]:
        vol = annualized_volatility(returns)
        sharpe = sharpe_ratio(returns)
        mdd = max_drawdown(series).value
        v95 = historical_var(returns, confidence=0.95)
        cv95 = historical_cvar(returns, confidence=0.95)
        mean_ret = float(returns.mean())

        return {
            "mean_return": mean_ret,
            "annualized_volatility": vol,
            "sharpe_ratio": sharpe,
            "max_drawdown": mdd,
            "var_95": v95,
            "cvar_95": cv95,
        }

    return study


def create_lorenz_study() -> ExperimentStudyFn:
    """Create an experiment study function for the continuous Lorenz system.

    Returns
    -------
    ExperimentStudyFn
        Callable simulating Lorenz dynamics and calculating invariants.
    """

    def study(parameters: Mapping[str, JsonValue], seeds: SeedManager) -> Mapping[str, float]:
        sigma = float(parameters.get("sigma", 10.0))  # type: ignore[arg-type]
        rho = float(parameters.get("rho", 28.0))  # type: ignore[arg-type]
        beta = float(parameters.get("beta", 8.0 / 3.0))  # type: ignore[arg-type]
        dt = float(parameters.get("dt", 0.01))  # type: ignore[arg-type]
        n_steps = int(parameters.get("n_steps", 200))  # type: ignore[arg-type]

        params = LorenzParameters(sigma=sigma, rho=rho, beta=beta)
        hopf_threshold = lorenz_hopf_rho(sigma=sigma, beta=beta)
        hopf_val = float(hopf_threshold) if hopf_threshold is not None else -1.0

        # Draw a reproducible initial condition using SeedManager
        rng = seeds.generator("initial_condition")
        x0 = float(rng.normal(1.0, 0.1))
        y0 = float(rng.normal(1.0, 0.1))
        z0 = float(rng.normal(1.0, 0.1))

        trajectory = simulate_lorenz(
            initial_state=(x0, y0, z0),
            n_steps=n_steps,
            dt=dt,
            parameters=params,
        )

        x_coords = trajectory.states[:, 0]
        z_coords = trajectory.states[:, 2]

        return {
            "hopf_threshold": hopf_val,
            "x_mean": float(np.mean(x_coords)),
            "x_std": float(np.std(x_coords)),
            "z_max": float(np.max(z_coords)),
            "is_above_hopf": 1.0 if (hopf_threshold is not None and rho > hopf_threshold) else 0.0,
        }

    return study


def create_logistic_study() -> ExperimentStudyFn:
    """Create an experiment study function for the discrete logistic map.

    Returns
    -------
    ExperimentStudyFn
        Callable simulating the logistic map and calculating Lyapunov exponent.
    """

    def study(parameters: Mapping[str, JsonValue], seeds: SeedManager) -> Mapping[str, float]:
        r = float(parameters.get("r", 3.8))  # type: ignore[arg-type]
        n_steps = int(parameters.get("n_steps", 5_000))  # type: ignore[arg-type]

        rng = seeds.generator("x0")
        x0 = float(rng.uniform(0.1, 0.9))

        orbit = simulate_logistic_map(r=r, x0=x0, n_steps=n_steps)
        lyapunov = logistic_lyapunov_exponent(r=r, x0=x0, n_steps=n_steps)

        return {
            "r": r,
            "lyapunov_exponent": lyapunov,
            "orbit_mean": float(np.mean(orbit)),
            "orbit_std": float(np.std(orbit)),
            "is_chaotic": 1.0 if lyapunov > 0.0 else 0.0,
        }

    return study


class ActionExecutor:
    """Orchestrates the deterministic execution of scientific studies."""

    def execute_study(
        self,
        context: WorkflowContext,
        study_fn: ExperimentStudyFn,
        study_name: str = "Automated AI Workflow Study",
    ) -> ExperimentRun:
        """Execute an experiment function and record the metrics in context.

        Parameters
        ----------
        context : WorkflowContext
            Workflow context supplying parameters, seed, hypothesis, and data hash.
        study_fn : ExperimentStudyFn
            The deterministic function to execute within the Research Core.
        study_name : str, optional
            Human-readable title of the experiment.

        Returns
        -------
        ExperimentRun
            The immutable execution record produced by quantlab.research.run_experiment.
        """
        hypothesis = context.hypothesis or "Empirical stability and risk evaluation."
        experiment = Experiment(
            name=study_name,
            hypothesis=hypothesis,
            model=context.model,
            parameters=context.parameters,
            seed=context.seed,
            data_hash=context.data_hash,
        )

        run = run_experiment(experiment, study_fn)

        # Update context metrics with the computed experiment metrics
        for name, value in run.metrics.items():
            context.record_metric(name, value)

        return run

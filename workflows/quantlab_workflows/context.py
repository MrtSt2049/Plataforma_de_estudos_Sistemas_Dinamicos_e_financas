"""Workflow context holding state, data, metrics and message history (ADR 0008, Element 2)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from quantlab.data import CleaningReport
from quantlab.research import hash_data
from quantlab_workflows.triggers import TriggerEvent
from quantlab_workflows.types import AgentMessage


@dataclass
class WorkflowContext:
    """The complete context of an AI workflow run.

    Parameters
    ----------
    trigger : TriggerEvent
        The triggering event that initiated the workflow.
    symbol : str | None, optional
        Target ticker symbol or system identifier (e.g. 'PETR4.SA', 'lorenz').
    data : pd.DataFrame | None, optional
        Canonical market data series or simulated trajectory.
    data_hash : str | None, optional
        SHA-256 fingerprint computed via quantlab.research.hash_data.
    cleaning_report : CleaningReport | None, optional
        Audit trail of market data cleaning operations.
    hypothesis : str | None, optional
        The formal scientific hypothesis under test.
    model : str, optional
        Identifier of the mathematical model (e.g. 'risk_and_lorenz_stability').
    parameters : dict[str, Any], optional
        Numeric and model parameters passed to the experiment.
    seed : int, optional
        Deterministic random seed in [0, 2^53 - 1]. Defaults to 42.
    metrics : dict[str, float], optional
        Scalar metrics computed by the quantitative or dynamic engine.
    messages : list[AgentMessage], optional
        Audit trail of agent interactions and reasoning.
    """

    trigger: TriggerEvent
    symbol: str | None = None
    data: pd.DataFrame | None = None
    data_hash: str | None = None
    cleaning_report: CleaningReport | None = None
    hypothesis: str | None = None
    model: str = "quantitative_risk_and_dynamics"
    parameters: dict[str, Any] = field(default_factory=dict)
    seed: int = 42
    metrics: dict[str, float] = field(default_factory=dict)
    messages: list[AgentMessage] = field(default_factory=list)

    def add_message(self, message: AgentMessage) -> None:
        """Append an agent reasoning message to the workflow context."""
        self.messages.append(message)

    def record_metric(self, name: str, value: float) -> None:
        """Record a scalar quantitative or dynamical metric."""
        self.metrics[name] = float(value)

    def set_data(
        self,
        data: pd.DataFrame,
        cleaning_report: CleaningReport | None = None,
    ) -> None:
        """Attach market data, automatically computing its SHA-256 fingerprint."""
        self.data = data
        self.cleaning_report = cleaning_report
        self.data_hash = hash_data(data)

    def summary_text(self) -> str:
        """Return a formatted textual summary of the current context for agents."""
        lines = [
            f"Target: {self.symbol or 'N/A'}",
            f"Trigger: {self.trigger.trigger_type.value} from {self.trigger.source}",
            f"Hypothesis: {self.hypothesis or '(Not yet formulated)'}",
            f"Model: {self.model}",
            f"Seed: {self.seed}",
            f"Data Hash: {self.data_hash or 'None'}",
        ]
        if self.metrics:
            lines.append("Computed Metrics:")
            for k, v in self.metrics.items():
                lines.append(f"  - {k}: {v:.6g}")
        return "\n".join(lines)

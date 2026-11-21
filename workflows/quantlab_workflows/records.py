"""Audit records and serialization for completed AI workflows (ADR 0008, Element 5)."""

from __future__ import annotations

import datetime as dt
import uuid
from dataclasses import dataclass, field
from typing import Any

from quantlab.research import ExperimentRun
from quantlab_workflows.triggers import TriggerEvent
from quantlab_workflows.types import AgentMessage, WorkflowStatus


@dataclass(frozen=True)
class WorkflowRecord:
    """The immutable audit record of an AI workflow execution.

    Parameters
    ----------
    workflow_id : str
        Unique identifier (UUID4 string).
    status : WorkflowStatus
        Final status of the workflow (COMPLETED, FAILED, etc.).
    trigger : TriggerEvent
        The initial trigger event that started the workflow.
    hypothesis : str
        The scientific hypothesis tested.
    messages : tuple[AgentMessage, ...]
        Ordered sequence of agent messages emitted during deliberation.
    metrics : dict[str, float]
        Key metrics resulting from the scientific action.
    final_synthesis : str
        The concluding synthesis or verdict produced by the synthesizer agent.
    data_hash : str | None, optional
        SHA-256 fingerprint of the input data, if applicable.
    experiment_run : ExperimentRun | None, optional
        The Research Core execution record, if a study was run.
    created_at : dt.datetime
        When the workflow began, in UTC.
    completed_at : dt.datetime | None, optional
        When the workflow completed, in UTC.
    """

    workflow_id: str
    status: WorkflowStatus
    trigger: TriggerEvent
    hypothesis: str
    messages: tuple[AgentMessage, ...]
    metrics: dict[str, float]
    final_synthesis: str
    data_hash: str | None = None
    experiment_run: ExperimentRun | None = None
    created_at: dt.datetime = field(default_factory=lambda: dt.datetime.now(dt.UTC))
    completed_at: dt.datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert the record into a JSON-compatible dictionary for Supabase or APIs."""
        return {
            "workflow_id": self.workflow_id,
            "status": str(self.status),
            "trigger": self.trigger.to_dict(),
            "hypothesis": self.hypothesis,
            "messages": [m.to_dict() for m in self.messages],
            "metrics": dict(self.metrics),
            "final_synthesis": self.final_synthesis,
            "data_hash": self.data_hash,
            "experiment_run": self.experiment_run.to_dict() if self.experiment_run else None,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkflowRecord:
        """Reconstruct a WorkflowRecord from a dictionary."""
        exp_run = (
            ExperimentRun.from_dict(data["experiment_run"]) if data.get("experiment_run") else None
        )
        completed_at = (
            dt.datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None
        )
        return cls(
            workflow_id=str(data["workflow_id"]),
            status=WorkflowStatus(data["status"]),
            trigger=TriggerEvent.from_dict(data["trigger"]),
            hypothesis=str(data["hypothesis"]),
            messages=tuple(AgentMessage.from_dict(m) for m in data.get("messages", [])),
            metrics={k: float(v) for k, v in data.get("metrics", {}).items()},
            final_synthesis=str(data.get("final_synthesis", "")),
            data_hash=data.get("data_hash"),
            experiment_run=exp_run,
            created_at=dt.datetime.fromisoformat(data["created_at"]),
            completed_at=completed_at,
        )

    @classmethod
    def create(
        cls,
        status: WorkflowStatus,
        trigger: TriggerEvent,
        hypothesis: str,
        messages: list[AgentMessage],
        metrics: dict[str, float],
        final_synthesis: str,
        data_hash: str | None = None,
        experiment_run: ExperimentRun | None = None,
        created_at: dt.datetime | None = None,
    ) -> WorkflowRecord:
        """Create a new WorkflowRecord with an automatic UUID and UTC timestamps."""
        now = dt.datetime.now(dt.UTC)
        return cls(
            workflow_id=str(uuid.uuid4()),
            status=status,
            trigger=trigger,
            hypothesis=hypothesis,
            messages=tuple(messages),
            metrics=dict(metrics),
            final_synthesis=final_synthesis,
            data_hash=data_hash,
            experiment_run=experiment_run,
            created_at=created_at or now,
            completed_at=now,
        )

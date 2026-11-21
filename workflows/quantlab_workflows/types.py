"""Domain types and enumerations for QuantLab AI Workflows (ADR 0008)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class TriggerType(StrEnum):
    """The category of event that initiated the workflow."""

    MANUAL = "manual"
    SCHEDULE = "schedule"
    ANOMALY = "anomaly"
    WEBHOOK = "webhook"


class AgentRole(StrEnum):
    """Role played by an AI agent within the scientific workflow."""

    HYPOTHESIS = "hypothesis"
    QUANTITATIVE = "quantitative"
    DYNAMICS = "dynamics"
    SYNTHESIZER = "synthesizer"


class WorkflowStatus(StrEnum):
    """Execution status of an AI workflow."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class AgentMessage:
    """An immutable structured message produced by an agent in the workflow.

    Parameters
    ----------
    role : AgentRole
        The specialized role of the emitting agent.
    agent_name : str
        Human-readable name of the agent.
    content : str
        The textual reasoning, findings, or synthesized content.
    metadata : dict[str, Any]
        Additional structured data (e.g. proposed parameters, detected regimes).
    """

    role: AgentRole
    agent_name: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert the message to a plain JSON-compatible dictionary."""
        return {
            "role": str(self.role),
            "agent_name": self.agent_name,
            "content": self.content,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentMessage:
        """Reconstruct an AgentMessage from a dictionary."""
        return cls(
            role=AgentRole(data["role"]),
            agent_name=str(data["agent_name"]),
            content=str(data["content"]),
            metadata=dict(data.get("metadata", {})),
        )

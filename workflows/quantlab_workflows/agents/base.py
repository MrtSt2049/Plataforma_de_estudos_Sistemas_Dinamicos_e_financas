"""Base interface for AI agents in QuantLab workflows (ADR 0008, Element 3)."""

from __future__ import annotations

from typing import Protocol

from quantlab_workflows.context import WorkflowContext
from quantlab_workflows.providers import LLMProvider
from quantlab_workflows.types import AgentMessage, AgentRole


class BaseAgent(Protocol):
    """Protocol for specialized AI agents collaborating in a workflow."""

    @property
    def role(self) -> AgentRole:
        """The specific role of this agent."""
        ...

    @property
    def name(self) -> str:
        """The display name of this agent."""
        ...

    def execute(self, context: WorkflowContext, provider: LLMProvider) -> AgentMessage:
        """Process the workflow context and return an agent decision or message.

        Parameters
        ----------
        context : WorkflowContext
            The shared context containing trigger, data, metrics and prior messages.
        provider : LLMProvider
            The language model provider used to perform reasoning.

        Returns
        -------
        AgentMessage
            The structured decision or synthesis produced by the agent.
        """
        ...

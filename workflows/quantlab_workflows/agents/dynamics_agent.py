"""Dynamical Systems Agent for analyzing non-linear regimes and chaos (ADR 0008)."""

from __future__ import annotations

from quantlab_workflows.context import WorkflowContext
from quantlab_workflows.providers import LLMProvider
from quantlab_workflows.types import AgentMessage, AgentRole

_DEFAULT_SYSTEM_PROMPT = (
    "You are the Dynamical Systems Specialist of QuantLab. Your responsibility is to analyze "
    "non-linear dynamics, stability of fixed points and equilibria, bifurcation thresholds, "
    "and chaotic transitions (e.g. Lyapunov exponents, strange attractors). "
    "Assess whether the dynamics exhibit periodicity, limit cycles, or sensitive dependence "
    "on initial conditions."
)


class DynamicsAgent:
    """Agent that analyzes non-linear dynamical systems and stability regimes."""

    def __init__(
        self,
        name: str = "Dynamical Systems Specialist",
        system_prompt: str = _DEFAULT_SYSTEM_PROMPT,
    ) -> None:
        self._name = name
        self._system_prompt = system_prompt

    @property
    def role(self) -> AgentRole:
        """The specific role of this agent."""
        return AgentRole.DYNAMICS

    @property
    def name(self) -> str:
        """The display name of this agent."""
        return self._name

    def execute(self, context: WorkflowContext, provider: LLMProvider) -> AgentMessage:
        """Analyze dynamical model parameters and invariants in context."""
        params_text = (
            "\n".join(f"  - {k}: {v}" for k, v in context.parameters.items())
            or "  (No explicit parameters provided)"
        )

        tracked_terms = ("lyapunov", "hopf", "stability", "rho", "r_param")
        metrics_text = (
            "\n".join(
                f"  - {k}: {v:.6g}"
                for k, v in context.metrics.items()
                if any(term in k.lower() for term in tracked_terms)
            )
            or "  (No dynamic invariants recorded)"
        )

        prompt = (
            f"Context:\n{context.summary_text()}\n\n"
            f"Model Parameters:\n{params_text}\n\n"
            f"Dynamical Metrics:\n{metrics_text}\n\n"
            "Assess the dynamical state: Is the system in a stable, periodic, or chaotic regime? "
            "How do the parameters relate to critical thresholds (e.g. Hopf bifurcation, "
            "period doubling)? Provide a concise dynamical assessment."
        )

        response = provider.generate(prompt=prompt, system_prompt=self._system_prompt)
        cleaned_content = response.strip()

        msg = AgentMessage(
            role=self.role,
            agent_name=self.name,
            content=cleaned_content,
            metadata={"parameters_analyzed": dict(context.parameters)},
        )
        context.add_message(msg)
        return msg

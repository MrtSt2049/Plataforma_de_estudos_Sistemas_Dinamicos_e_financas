"""Quantitative Analysis Agent for evaluating market risk and return structures (ADR 0008)."""

from __future__ import annotations

from quantlab_workflows.context import WorkflowContext
from quantlab_workflows.providers import LLMProvider
from quantlab_workflows.types import AgentMessage, AgentRole

_DEFAULT_SYSTEM_PROMPT = (
    "You are the Quantitative Risk Analyst of QuantLab. Your responsibility is to analyze "
    "statistical properties of asset return series, including annualized volatility, Sharpe Ratio, "
    "historical VaR/CVaR, and Maximum Drawdown. Identify volatility regimes, tail risks, "
    "and provide quantitative risk assessments."
)


class QuantAgent:
    """Agent that assesses quantitative risk, returns, and statistical regimes."""

    def __init__(
        self,
        name: str = "Quantitative Risk Analyst",
        system_prompt: str = _DEFAULT_SYSTEM_PROMPT,
    ) -> None:
        self._name = name
        self._system_prompt = system_prompt

    @property
    def role(self) -> AgentRole:
        """The specific role of this agent."""
        return AgentRole.QUANTITATIVE

    @property
    def name(self) -> str:
        """The display name of this agent."""
        return self._name

    def execute(self, context: WorkflowContext, provider: LLMProvider) -> AgentMessage:
        """Evaluate the quantitative metrics in context and emit analytical findings."""
        metrics_text = (
            "\n".join(f"  - {k}: {v:.6g}" for k, v in context.metrics.items())
            or "  (No precomputed metrics available)"
        )

        prompt = (
            f"Context:\n{context.summary_text()}\n\n"
            f"Available Quantitative Metrics:\n{metrics_text}\n\n"
            "Analyze these metrics. Characterize the risk profile: is the asset in a high or low "
            "volatility regime? How severe are the tail losses (VaR/CVaR) and drawdown? "
            "Provide a concise analytical synthesis."
        )

        response = provider.generate(prompt=prompt, system_prompt=self._system_prompt)
        cleaned_content = response.strip()

        msg = AgentMessage(
            role=self.role,
            agent_name=self.name,
            content=cleaned_content,
            metadata={"evaluated_metrics": dict(context.metrics)},
        )
        context.add_message(msg)
        return msg

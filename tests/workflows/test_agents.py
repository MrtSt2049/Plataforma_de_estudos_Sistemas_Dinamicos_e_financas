"""Tests for specialized AI agents (ADR 0008, Element 3)."""

from __future__ import annotations

from quantlab_workflows.agents.dynamics_agent import DynamicsAgent
from quantlab_workflows.agents.hypothesis_agent import HypothesisAgent
from quantlab_workflows.agents.quant_agent import QuantAgent
from quantlab_workflows.agents.synthesizer_agent import SynthesizerAgent
from quantlab_workflows.context import WorkflowContext
from quantlab_workflows.providers import MockLLMProvider
from quantlab_workflows.triggers import TriggerEvent
from quantlab_workflows.types import AgentRole


def test_hypothesis_agent_formulates_and_updates_context() -> None:
    provider = MockLLMProvider(
        default_response="Hypothesis: The Lorenz system exhibits chaos when rho exceeds 24.74."
    )
    agent = HypothesisAgent()
    assert agent.role == AgentRole.HYPOTHESIS

    trigger = TriggerEvent.manual("Investigate chaos in Lorenz")
    ctx = WorkflowContext(trigger=trigger)

    msg = agent.execute(ctx, provider)
    assert msg.role == AgentRole.HYPOTHESIS
    assert "The Lorenz system exhibits chaos" in ctx.hypothesis  # type: ignore[operator]
    assert len(ctx.messages) == 1


def test_quant_agent_evaluates_metrics() -> None:
    provider = MockLLMProvider(
        default_response="The annualized volatility of 35% indicates a high-risk regime."
    )
    agent = QuantAgent()
    assert agent.role == AgentRole.QUANTITATIVE

    trigger = TriggerEvent.manual("Assess risk")
    ctx = WorkflowContext(trigger=trigger)
    ctx.record_metric("annualized_volatility", 0.35)
    ctx.record_metric("sharpe_ratio", 0.42)

    msg = agent.execute(ctx, provider)
    assert msg.role == AgentRole.QUANTITATIVE
    assert "high-risk regime" in msg.content
    assert msg.metadata["evaluated_metrics"]["annualized_volatility"] == 0.35


def test_dynamics_agent_evaluates_invariants() -> None:
    provider = MockLLMProvider(
        default_response="System is above Hopf bifurcation threshold. Trajectories are chaotic."
    )
    agent = DynamicsAgent()
    assert agent.role == AgentRole.DYNAMICS

    trigger = TriggerEvent.manual("Check Lorenz stability")
    ctx = WorkflowContext(
        trigger=trigger,
        parameters={"sigma": 10.0, "rho": 28.0, "beta": 2.666667},
    )
    ctx.record_metric("hopf_threshold", 24.7368)

    msg = agent.execute(ctx, provider)
    assert msg.role == AgentRole.DYNAMICS
    assert "Hopf bifurcation" in msg.content


def test_synthesizer_agent_verdict() -> None:
    provider = MockLLMProvider(
        default_response=(
            "Scientific Report:\n"
            "1. Verdict: Supported. The empirical data confirms the hypothesis.\n"
            "2. Summary: High turbulence observed."
        )
    )
    agent = SynthesizerAgent()
    assert agent.role == AgentRole.SYNTHESIZER

    trigger = TriggerEvent.manual("Synthesize findings")
    ctx = WorkflowContext(trigger=trigger)
    ctx.hypothesis = "Volatility is elevated"

    msg = agent.execute(ctx, provider)
    assert msg.role == AgentRole.SYNTHESIZER
    assert msg.metadata["verdict"] == "supported"
    assert "Verdict: Supported" in msg.content

"""Tests for LLM providers and test doubles (ADR 0008)."""

from __future__ import annotations

from quantlab_workflows.providers import CallableLLMProvider, MockLLMProvider


def test_mock_llm_provider_default() -> None:
    provider = MockLLMProvider()
    response = provider.generate("Any prompt")
    assert response == "Mock analysis completed successfully."
    assert len(provider.call_history) == 1
    assert provider.call_history[0]["prompt"] == "Any prompt"


def test_mock_llm_provider_matching() -> None:
    provider = MockLLMProvider(
        responses={"hypothesis": "Hypothesis: Orbit is chaotic at r=3.8"},
        default_response="Default answer",
    )
    ans1 = provider.generate("Please generate a hypothesis for this study.")
    assert "Orbit is chaotic" in ans1

    ans2 = provider.generate("Calculate the returns.")
    assert ans2 == "Default answer"


def test_callable_llm_provider() -> None:
    def custom_fn(prompt: str, sys: str | None) -> str:
        return f"Echo: {prompt} | Sys: {sys}"

    provider = CallableLLMProvider(custom_fn)
    ans = provider.generate("Hello", system_prompt="Be concise")
    assert ans == "Echo: Hello | Sys: Be concise"

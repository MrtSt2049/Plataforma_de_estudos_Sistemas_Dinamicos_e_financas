"""Synthesizer Agent for compiling findings into a final scientific report (ADR 0008)."""

from __future__ import annotations

from quantlab_workflows.context import WorkflowContext
from quantlab_workflows.providers import LLMProvider
from quantlab_workflows.types import AgentMessage, AgentRole

_DEFAULT_SYSTEM_PROMPT = (
    "You are the Lead Scientific Reviewer of QuantLab. Your responsibility is to synthesize "
    "the findings of the Hypothesis, Quantitative Risk, and Dynamical Systems agents. "
    "Evaluate whether the empirical results support, reject, or require refinement of the "
    "original hypothesis. Produce a rigorous, structured scientific summary."
)


class SynthesizerAgent:
    """Agent that compiles multi-agent deliberations into a conclusive scientific report."""

    def __init__(
        self,
        name: str = "Lead Scientific Reviewer",
        system_prompt: str = _DEFAULT_SYSTEM_PROMPT,
    ) -> None:
        self._name = name
        self._system_prompt = system_prompt

    @property
    def role(self) -> AgentRole:
        """The specific role of this agent."""
        return AgentRole.SYNTHESIZER

    @property
    def name(self) -> str:
        """The display name of this agent."""
        return self._name

    def execute(self, context: WorkflowContext, provider: LLMProvider) -> AgentMessage:
        """Synthesize previous agent contributions and empirical results."""
        prior_messages_text = (
            "\n\n".join(
                f"[{msg.agent_name} ({msg.role.value})]:\n{msg.content}" for msg in context.messages
            )
            or "(No prior agent deliberations)"
        )

        metrics_text = (
            "\n".join(f"  - {k}: {v:.6g}" for k, v in context.metrics.items()) or "  (None)"
        )

        prompt = (
            f"Scientific Study Context:\n{context.summary_text()}\n\n"
            f"Prior Agent Deliberations:\n{prior_messages_text}\n\n"
            f"Final Empirical Metrics:\n{metrics_text}\n\n"
            "Produce the final scientific report:\n"
            "1. Verdict on the Hypothesis (Supported, Rejected, or Inconclusive)\n"
            "2. Summary of Key Findings\n"
            "3. Quantitative & Dynamic Risk Takeaways\n"
            "4. Recommendations for Follow-up Experiments"
        )

        response = provider.generate(prompt=prompt, system_prompt=self._system_prompt)
        cleaned_content = response.strip()

        # Determine verdict keyword for metadata
        verdict = "inconclusive"
        lowered = cleaned_content.lower()
        if "supported" in lowered and "not supported" not in lowered:
            verdict = "supported"
        elif "rejected" in lowered or "refuted" in lowered:
            verdict = "rejected"

        msg = AgentMessage(
            role=self.role,
            agent_name=self.name,
            content=cleaned_content,
            metadata={"verdict": verdict},
        )
        context.add_message(msg)
        return msg

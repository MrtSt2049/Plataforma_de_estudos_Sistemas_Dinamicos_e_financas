"""Scientific Hypothesis Agent for formulating testable research statements (ADR 0008)."""

from __future__ import annotations

from quantlab_workflows.context import WorkflowContext
from quantlab_workflows.providers import LLMProvider
from quantlab_workflows.types import AgentMessage, AgentRole

_DEFAULT_SYSTEM_PROMPT = (
    "You are the Scientific Hypothesis Agent of QuantLab, a platform for quantitative finance "
    "and computational dynamical systems. Your responsibility is to translate research goals, "
    "market anomalies or user questions into a formal, falsifiable, and mathematically rigorous "
    "hypothesis suitable for empirical testing. Formulate a clear hypothesis statement."
)


class HypothesisAgent:
    """Agent that translates research goals into formal scientific hypotheses."""

    def __init__(
        self,
        name: str = "Hypothesis Formulator",
        system_prompt: str = _DEFAULT_SYSTEM_PROMPT,
    ) -> None:
        self._name = name
        self._system_prompt = system_prompt

    @property
    def role(self) -> AgentRole:
        """The specific role of this agent."""
        return AgentRole.HYPOTHESIS

    @property
    def name(self) -> str:
        """The display name of this agent."""
        return self._name

    def execute(self, context: WorkflowContext, provider: LLMProvider) -> AgentMessage:
        """Analyze the trigger and context to formulate a formal hypothesis."""
        trigger_info = context.trigger.to_dict()
        prompt = (
            f"Context Summary:\n{context.summary_text()}\n\n"
            f"Trigger details: {trigger_info}\n\n"
            "Formulate a formal, falsifiable scientific hypothesis for this study. "
            "State the hypothesis directly and specify what quantitative criteria "
            "would confirm or refute it."
        )

        response = provider.generate(prompt=prompt, system_prompt=self._system_prompt)
        cleaned_content = response.strip()

        # Update context hypothesis if not previously set
        if not context.hypothesis:
            # Use the first concise sentence or the full generated text
            first_line = cleaned_content.split("\n")[0].strip()
            # If the response starts with 'Hypothesis:', strip it for canonical storage
            if first_line.lower().startswith("hypothesis:"):
                first_line = first_line[len("hypothesis:") :].strip()
            context.hypothesis = first_line or cleaned_content

        msg = AgentMessage(
            role=self.role,
            agent_name=self.name,
            content=cleaned_content,
            metadata={"formulated_hypothesis": context.hypothesis},
        )
        context.add_message(msg)
        return msg

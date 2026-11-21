"""Full pipeline orchestrator connecting the 5 elements of AI workflows (ADR 0008)."""

from __future__ import annotations

import datetime as dt
from collections.abc import Sequence

from quantlab.research import ExperimentRun
from quantlab_workflows.actions import ActionExecutor, ExperimentStudyFn
from quantlab_workflows.agents.base import BaseAgent
from quantlab_workflows.agents.dynamics_agent import DynamicsAgent
from quantlab_workflows.agents.hypothesis_agent import HypothesisAgent
from quantlab_workflows.agents.quant_agent import QuantAgent
from quantlab_workflows.agents.synthesizer_agent import SynthesizerAgent
from quantlab_workflows.context import WorkflowContext
from quantlab_workflows.providers import LLMProvider, MockLLMProvider
from quantlab_workflows.records import WorkflowRecord
from quantlab_workflows.types import WorkflowStatus


class WorkflowOrchestrator:
    """Orchestrator for autonomous multi-agent quantitative and dynamical workflows.

    Coordinates Trigger -> Context -> Intelligent Decision -> Action -> Registry.

    Parameters
    ----------
    provider : LLMProvider | None, optional
        The LLM provider for agent reasoning. Defaults to MockLLMProvider.
    hypothesis_agent : HypothesisAgent | None, optional
        Custom agent for hypothesis formulation.
    analyst_agents : Sequence[BaseAgent] | None, optional
        Specialized agents to analyze context (defaults to QuantAgent + DynamicsAgent).
    synthesizer_agent : SynthesizerAgent | None, optional
        Agent that reviews and compiles final conclusions.
    action_executor : ActionExecutor | None, optional
        Executor for deterministic Research Core studies.
    """

    def __init__(
        self,
        provider: LLMProvider | None = None,
        hypothesis_agent: HypothesisAgent | None = None,
        analyst_agents: Sequence[BaseAgent] | None = None,
        synthesizer_agent: SynthesizerAgent | None = None,
        action_executor: ActionExecutor | None = None,
    ) -> None:
        self.provider = provider or MockLLMProvider()
        self.hypothesis_agent = hypothesis_agent or HypothesisAgent()
        self.analyst_agents: list[BaseAgent] = (
            list(analyst_agents) if analyst_agents is not None else [QuantAgent(), DynamicsAgent()]
        )
        self.synthesizer_agent = synthesizer_agent or SynthesizerAgent()
        self.action_executor = action_executor or ActionExecutor()

    def run(
        self,
        context: WorkflowContext,
        study_fn: ExperimentStudyFn | None = None,
        study_name: str = "Automated Scientific Workflow Study",
    ) -> WorkflowRecord:
        """Execute the complete 5-element workflow.

        Parameters
        ----------
        context : WorkflowContext
            Context initialized with trigger and any preliminary data or parameters.
        study_fn : ExperimentStudyFn | None, optional
            Deterministic study function to execute within the Research Core.
        study_name : str, optional
            Title for the experiment run.

        Returns
        -------
        WorkflowRecord
            The comprehensive, reproducible audit record of the workflow run.
        """
        start_time = dt.datetime.now(dt.UTC)
        exp_run: ExperimentRun | None = None

        try:
            # 1. Intelligent Decision: Formulate or refine the scientific hypothesis
            self.hypothesis_agent.execute(context, self.provider)

            # 2. Intelligent Decision: Deliberate with domain analyst agents
            for agent in self.analyst_agents:
                agent.execute(context, self.provider)

            # 3. Action: Run deterministic study in the Research Core if provided
            if study_fn is not None:
                exp_run = self.action_executor.execute_study(
                    context=context,
                    study_fn=study_fn,
                    study_name=study_name,
                )

            # 4. Intelligent Decision: Synthesize final conclusions & evaluate hypothesis
            synthesis_msg = self.synthesizer_agent.execute(context, self.provider)

            # 5. Registry: Record immutable execution artifact
            record = WorkflowRecord.create(
                status=WorkflowStatus.COMPLETED,
                trigger=context.trigger,
                hypothesis=context.hypothesis or "Hypothesis not recorded",
                messages=context.messages,
                metrics=context.metrics,
                final_synthesis=synthesis_msg.content,
                data_hash=context.data_hash,
                experiment_run=exp_run,
                created_at=start_time,
            )
            return record

        except Exception as exc:
            # Record failed execution state faithfully (RULE 010 & RULE 060)
            return WorkflowRecord.create(
                status=WorkflowStatus.FAILED,
                trigger=context.trigger,
                hypothesis=context.hypothesis or "Failed before hypothesis",
                messages=context.messages,
                metrics=context.metrics,
                final_synthesis=f"Workflow failed: {exc}",
                data_hash=context.data_hash,
                experiment_run=None,
                created_at=start_time,
            )

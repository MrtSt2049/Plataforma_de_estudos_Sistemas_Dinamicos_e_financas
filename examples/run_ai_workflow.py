"""Example: Running an autonomous AI scientific workflow in QuantLab (ADR 0008).

Demonstrates the 5 elements:
1. Trigger: A researcher asks a question or an anomaly is detected.
2. Context: Market data is loaded, cleaned, and hashed (hash_data).
3. Intelligent Decision: Multi-agent deliberation (Hypothesis, Quant, Dynamics, Synthesizer).
4. Action: Deterministic execution of the study via Research Core (run_experiment).
5. Registry: Immutable record (WorkflowRecord) serializable to JSON/Supabase.

Usage::

    uv run python examples/run_ai_workflow.py
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from quantlab_workflows import (
    MockLLMProvider,
    TriggerEvent,
    WorkflowContext,
    WorkflowOrchestrator,
    create_market_risk_study,
)


def main() -> None:
    """Execute a pilot 5-element AI workflow demonstration."""
    print("=" * 70)
    print("QUANTLAB — AI WORKFLOW EXECUTION (5 ELEMENTS)")
    print("=" * 70)

    # --------------------------------------------------------------------------
    # 1. GATILHO (Trigger)
    # --------------------------------------------------------------------------
    print("\n[1. GATILHO]")
    trigger = TriggerEvent.manual(
        prompt="Verificar se o ativo exibe regime de alta volatilidade e risco de cauda severo.",
        symbol="PETR4.SA",
    )
    print(f"Tipo: {trigger.trigger_type.value.upper()} | Origem: {trigger.source}")
    print(f"Prompt: {trigger.payload.get('prompt')}")

    # --------------------------------------------------------------------------
    # 2. CONTEXTO (Context)
    # --------------------------------------------------------------------------
    print("\n[2. CONTEXTO CIENTÍFICO]")
    # Simulação realista de série de preços para demonstração offline
    rng = np.random.default_rng(2026)
    days = 180
    log_rets = rng.normal(0.0004, 0.018, size=days)
    # Injetando evento de estresse de volatilidade
    log_rets[100:115] = rng.normal(-0.005, 0.035, size=15)
    prices = 32.50 * np.exp(np.cumsum(log_rets))
    dates = pd.date_range("2024-01-01", periods=days, freq="B", tz="UTC")
    df = pd.DataFrame({"close": prices}, index=dates)

    context = WorkflowContext(trigger=trigger, symbol="PETR4.SA", seed=42)
    context.set_data(df)
    print(f"Ativo: {context.symbol} ({len(df)} pregões)")
    print(f"Data Hash (SHA-256): {context.data_hash}")
    print(f"Semente Aleatória: {context.seed}")

    # --------------------------------------------------------------------------
    # 3 & 4 & 5. ORQUESTRADOR: DECISÃO INTELIGENTE -> AÇÃO -> REGISTRO
    # --------------------------------------------------------------------------
    print("\n[3. DECISÃO INTELIGENTE & 4. AÇÃO MATEMÁTICA]")
    provider = MockLLMProvider(
        responses={
            "falsifiable scientific hypothesis": (
                "Hipótese: O ativo PETR4.SA entrou em regime de alta turbulência com "
                "volatilidade anualizada superior a 30% e CVaR (95%) superior a 4%, "
                "indicando caudas pesadas."
            ),
            "Analyze these metrics": (
                "Análise Quantitativa: A volatilidade anualizada de ~35% e o VaR 95% de ~3% "
                "confirmam regime de risco severo. As perdas médias na cauda (CVaR ~4.5%) "
                "superam substancialmente o VaR, evidenciando assimetria e caudas gordas."
            ),
            "Assess the dynamical state": (
                "Especialista em Dinâmica: A dispersão e o drawdown de -16.8% são consistentes "
                "com uma transição dinâmica em modelos de atrator com sensibilidade aumentada."
            ),
            "Produce the final scientific report": (
                "Relatório Científico Final:\n"
                "1. Veredito: SUPORTADO. As métricas empíricas confirmam que o ativo opera em "
                "regime de alta volatilidade.\n"
                "2. Principais Evidências: Volatilidade anualizada de 35.17% e CVaR 95% de 4.52%.\n"
                "3. Gestão de Risco: Redução recomendada da exposição alavancada.\n"
                "4. Próximos Passos: Avaliar quebra estrutural via cadeias de Markov discretas."
            ),
        }
    )
    orchestrator = WorkflowOrchestrator(provider=provider)
    study_fn = create_market_risk_study(df["close"])

    record = orchestrator.run(
        context=context,
        study_fn=study_fn,
        study_name="PETR4.SA Volatility & Tail Risk Workflow",
    )

    print(f"\nStatus da Execução: {record.status.value.upper()}")
    print(f"Hipótese Formulada: {record.hypothesis}")

    print("\nDeliberações dos Agentes:")
    for msg in record.messages:
        print(f"  * [{msg.agent_name} ({msg.role.value})]:")
        print(f"    {msg.content[:120]}...")

    print("\nMétricas Empíricas Registradas no Research Core:")
    for metric_name, metric_val in record.metrics.items():
        print(f"  - {metric_name:24s}: {metric_val:.6f}")

    if record.experiment_run:
        print(f"\nDuração do Cálculo no Motor: {record.experiment_run.execution_time_ms:.2f} ms")
        print(f"Ambiente: Python {record.experiment_run.environment.get('python')}")

    # --------------------------------------------------------------------------
    # 5. REGISTRO & AUDITORIA (Registro)
    # --------------------------------------------------------------------------
    print("\n[5. REGISTRO & AUDITORIA]")
    print(f"Workflow ID (UUID): {record.workflow_id}")
    as_json = json.dumps(record.to_dict(), indent=2)
    print(f"Tamanho do Registro Serializado: {len(as_json)} bytes (pronto para Supabase)")
    print("\nSíntese Final:")
    print(record.final_synthesis)
    print("=" * 70)


if __name__ == "__main__":
    main()

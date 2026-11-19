---
trigger: manual
---

8. REGRAS DE BANCO E DADOS

RULE 038 — Integridade

Dados devem ser validados antes da persistência.

RULE 039 — Modelagem

Evite redundância desnecessária.

Utilize normalização quando apropriado e considere estruturas analíticas específicas quando houver justificativa.

RULE 040 — Dados financeiros

Armazene metadados relevantes:

Ativo.

Fonte.

Data.

Frequência.

Moeda.

Unidade.

Ajustes aplicados.

Metodologia de cálculo.

Não misture preços ajustados e não ajustados sem identificação explícita.

RULE 041 — Precisão financeira

Não utilize ponto flutuante binário indiscriminadamente para valores monetários que exijam precisão decimal.

Avalie Decimal e tipos NUMERIC do PostgreSQL para valores monetários.

Para cálculos estatísticos e vetorizados, utilize tipos numéricos científicos adequados.

RULE 042 — Grandes volumes

Utilize Parquet e DuckDB quando apropriado para processamento analítico.

Evite carregar conjuntos de dados desnecessariamente na memória.
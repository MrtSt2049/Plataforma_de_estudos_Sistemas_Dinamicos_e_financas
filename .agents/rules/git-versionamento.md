---
trigger: manual
---

10. REGRAS DE GIT E VERSIONAMENTO

RULE 048 — Commits

Utilize Conventional Commits.

Exemplos:

feat: add historical returns analysis

fix: correct volatility annualization

refactor: isolate risk calculations

test: add logistic map validation

docs: document supabase authentication

RULE 049 — Branches

Utilize branches para funcionalidades e correções.

Exemplos:

main

develop

feature/market-data

feature/risk-analysis

fix/jwt-validation

Adapte o fluxo ao tamanho da equipe.

RULE 050 — Versionamento

Utilize Semantic Versioning quando houver versões publicadas:

MAJOR.MINOR.PATCH.

Não introduza mudanças incompatíveis sem documentação.

RULE 051 — Proteção do repositório

Não versione:

.env.

Tokens.

Chaves.

Banco de dados local.

Arquivos temporários.

Cache.

Ambientes virtuais.

Dados privados.
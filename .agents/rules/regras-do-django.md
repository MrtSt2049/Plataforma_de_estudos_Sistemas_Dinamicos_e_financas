---
trigger: manual
---

RULE 019 — Django como camada de aplicação

O Django é responsável por:

APIs.

Regras de negócio.

Validação.

Permissões.

Persistência.

Orquestração.

Integração com o motor científico.

Não coloque cálculos científicos complexos diretamente nas views.

RULE 020 — Estrutura das aplicações

Cada aplicação Django deve possuir responsabilidades delimitadas.

Organize adequadamente:

models.py

serializers.py

views.py

services.py

permissions.py

urls.py

tests/

Não crie camadas artificiais quando a funcionalidade for simples.

RULE 021 — API REST

Utilize padrões REST consistentes.

Métodos HTTP apropriados.

Códigos de status corretos.

Validação de entrada.

Respostas padronizadas.

Paginação quando necessária.

Filtros explícitos.

Versionamento quando necessário.

Documente a API utilizando OpenAPI e drf-spectacular.

RULE 022 — Serviços

Regras de negócio complexas devem ser organizadas em serviços.

Views devem coordenar requisições, não concentrar toda a lógica.

RULE 023 — Operações demoradas

Simulações e cálculos que possam exceder o tempo de resposta HTTP devem evoluir para execução assíncrona.

A utilização de Celery e Redis deve ser introduzida quando existir necessidade concreta.


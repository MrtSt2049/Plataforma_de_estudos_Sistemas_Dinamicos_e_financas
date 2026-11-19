---
trigger: manual
---

7. REGRAS DE FRONTEND

RULE 031 — React e TypeScript

Utilize TypeScript em todo o frontend.

Evite any.

Defina interfaces e tipos para os dados recebidos das APIs.

RULE 032 — Componentização

Componentes devem possuir responsabilidades claras.

Evite componentes excessivamente grandes.

Separe:

Layout.

Componentes visuais.

Páginas.

Hooks.

Serviços.

Tipos.

Configurações.

Estado global.

RULE 033 — Separação de dados e apresentação

Componentes visuais não devem concentrar lógica de acesso a APIs.

Utilize serviços e hooks apropriados.

RULE 034 — Estados obrigatórios

Toda operação assíncrona relevante deve considerar:

Loading.

Success.

Empty.

Error.

Não deixe o usuário sem feedback durante operações.

RULE 035 — Design System

Utilize tokens e componentes reutilizáveis.

Respeite a identidade visual oficial do QuantLab.

Não crie padrões visuais independentes para cada página.

RULE 036 — Responsividade

Desenvolva prioritariamente para desktop, sem negligenciar tablets e dispositivos móveis.

RULE 037 — Visualização científica

Gráficos devem possuir:

Eixos identificados.

Unidades.

Legendas.

Escalas apropriadas.

Tooltips.

Tratamento de dados ausentes.

Interpretação visual coerente.

Não utilize gráficos apenas como decoração.
---
trigger: always_on
---

QUANTLAB — DEVELOPMENT RULES

Engineering Standards & Development Guidelines

Projeto: QuantLab — Quantitative Finance & Computational Dynamics
Versão: 1.0
Natureza: Regras obrigatórias de desenvolvimento
Stack: Python, Django, Django REST Framework, React, TypeScript e Supabase.

1. PRINCÍPIOS FUNDAMENTAIS

Todo desenvolvimento no QuantLab deve seguir os seguintes princípios:

Mathematical Correctness — correção matemática antes de otimização ou estética.

Clean Architecture — separação clara entre responsabilidades.

Modularity — módulos independentes e reutilizáveis.

Type Safety — tipagem explícita sempre que possível.

Reproducibility — resultados científicos reproduzíveis.

Testability — funcionalidades verificáveis por testes.

Security First — segurança desde a concepção.

Maintainability — código fácil de compreender, modificar e expandir.

Performance Awareness — eficiência computacional sem sacrificar clareza.

Documentation — decisões técnicas e matemáticas documentadas.

Nenhuma funcionalidade deve ser considerada concluída apenas porque funciona em uma demonstração visual.

2. REGRAS DE ARQUITETURA

RULE 001 — Separação de responsabilidades

Cada camada deve possuir uma responsabilidade específica.

Frontend: interface e experiência do usuário.

Backend: regras de negócio, APIs e orquestração.

Scientific Engine: algoritmos e modelos matemáticos.

Supabase: autenticação, persistência e armazenamento.

Data Layer: coleta, transformação e organização dos dados.

Não misture essas responsabilidades.

RULE 002 — Independência do motor científico

O diretório engine/quantlab não pode depender de:

Django.

Django REST Framework.

Supabase.

React.

APIs HTTP.

Componentes de interface.

O motor deve funcionar independentemente da aplicação web.

RULE 003 — Não duplicar lógica

Uma regra de negócio ou algoritmo deve possuir uma implementação central.

Não implemente o mesmo cálculo em diferentes módulos sem uma justificativa.

RULE 004 — Acoplamento controlado

Módulos devem se comunicar por interfaces explícitas.

Evite dependências circulares.

RULE 005 — Arquitetura evolutiva

Não implemente abstrações antecipadas sem necessidade concreta.

Prefira soluções simples que possam evoluir sem comprometer a arquitetura.

RULE 006 — Decisões arquiteturais documentadas

Decisões que alterem tecnologias, estrutura de módulos, persistência, autenticação ou interfaces públicas devem ser registradas em documentos ADR (Architecture Decision Records).
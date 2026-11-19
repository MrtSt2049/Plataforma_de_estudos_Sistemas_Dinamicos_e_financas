# ADR 0004 — Integração numérica de sistemas contínuos

- **Status:** aceita
- **Data:** 2026-11-19

## Contexto

Até aqui o módulo `quantlab.dynamics` só tinha sistemas discretos (o mapa logístico), em que a simulação é uma recorrência exata. O sistema de Lorenz é contínuo, $\dot{\mathbf x} = F(\mathbf x)$, e não tem solução em forma fechada: a trajetória precisa ser aproximada por um integrador numérico. O [ADR 0001](0001-empacotamento-do-motor-e-ambiente.md) deixou as dependências de execução restritas a NumPy e pandas e disse que o SciPy entraria quando um módulo precisasse dele.

## Problema

1. Implementar um integrador próprio ou usar o SciPy?
2. Qual método usar como padrão, e com quais tolerâncias?
3. Como devolver a trajetória de forma que o resultado seja reproduzível e auditável (RULE 017)?

## Alternativas

| Alternativa | A favor | Contra |
|---|---|---|
| **RK4 de passo fixo, próprio** | Simples, sem dependência nova. | Sem controle de erro: a precisão depende de escolher bem o passo, e nada avisa quando ele é grande demais. Mais um algoritmo numérico para manter e testar. |
| **Runge-Kutta adaptativo próprio** (Dormand-Prince) | Controle de erro sem dependência nova. | Reimplementa um código maduro e muito testado. O risco de erro sutil é alto e não traz ganho. |
| **`scipy.integrate.solve_ivp`** | Métodos adaptativos com controle de erro local (RK45, DOP853) e implícitos para sistemas rígidos (Radau). Saída densa para amostrar em qualquer grade. Biblioteca de referência, já prevista na stack do README. | Dependência de execução grande (~35 MB). Os stubs de tipo ficam num pacote separado (`scipy-stubs`). |

Para o método padrão foram comparados o RK45 (ordem 5), o DOP853 (ordem 8) e o Radau (implícito, ordem 5). Medição no Lorenz canônico a partir de $(1, 1, 1)$ até $t = 5$, com `rtol = 1e-10` e `atol = 1e-12`, contra uma referência DOP853 com `rtol = 1e-13`:

| Método | Avaliações de $F$ | Maior erro absoluto | Tempo |
|---|---|---|---|
| DOP853 | 2 885 | $1{,}2 \times 10^{-8}$ | 0,03 s |
| RK45 | 6 194 | $2{,}4 \times 10^{-8}$ | 0,07 s |
| Radau (com jacobiana analítica) | 27 697 | $6{,}8 \times 10^{-10}$ | 0,96 s |

## Decisão

- **SciPy entra como dependência de execução** (`scipy>=1.14`), e `scipy-stubs` entra no grupo `dev`, para o mypy estrito verificar as chamadas.
- Um integrador genérico, `quantlab.dynamics.integration.integrate_autonomous`, concentra o uso do `solve_ivp` (RULE 003). Cada sistema contínuo fornece só o campo vetorial e a jacobiana.
- **Método padrão: DOP853**, com `rtol = 1e-10` e `atol = 1e-12`. O Lorenz não é rígido para parâmetros moderados, e o método de ordem alta é o mais barato nessas tolerâncias. RK45 e Radau ficam disponíveis. O Radau recebe a jacobiana analítica.
- **A grade de amostragem é separada do passo de integração.** O usuário escolhe `dt` e `n_steps`. O solver escolhe os próprios passos, e os pontos da grade vêm do interpolador denso do método. Reduzir `dt` não aumenta a precisão, só registra mais pontos.
- **Tolerâncias abaixo de 100 épsilons de máquina são rejeitadas** (`DomainError`). O SciPy, nesse caso, aumenta o valor em silêncio, e o resultado registraria uma tolerância que não foi usada.
- **O resultado é um `Trajectory` imutável**: tempos, estados (arrays somente leitura), método, tolerâncias e número de avaliações do campo. Isso basta para registrar como a trajetória foi produzida.
- Falha do solver, como explosão em tempo finito ou passo menor que a resolução do ponto flutuante, vira `ComputationError`, nunca um resultado parcial.

## Justificativa

O controle adaptativo de erro é o que torna o resultado defensável: o passo fixo não dá nenhuma garantia local, e o integrador próprio só repetiria, com mais risco, o que o SciPy já faz. O DOP853 foi o mais barato entre os três métodos medidos com a mesma tolerância. Guardar as configurações do solver dentro do resultado evita que uma trajetória circule separada de como ela foi calculada.

## Consequências

- Quem instala o motor passa a baixar o SciPy. O núcleo continua sem dependências de rede ou de interface (RULE 002), e o teste de arquitetura continua valendo.
- A reprodutibilidade é exata na mesma plataforma e com as mesmas versões travadas no `uv.lock`. Entre versões diferentes do SciPy ou plataformas, os resultados podem diferir no nível do arredondamento. Em regime caótico, essa diferença cresce exponencialmente com o tempo (ver [sistema de Lorenz](../math/sistema-lorenz.md)).
- Passar a jacobiana para um método explícito faz o SciPy emitir aviso, e o `pytest` trata aviso como erro. Por isso o integrador só a repassa aos métodos implícitos.
- Novos sistemas contínuos (Rössler, osciladores, modelos de mercado em tempo contínuo) devem usar `integrate_autonomous`, e não chamar o `solve_ivp` diretamente.

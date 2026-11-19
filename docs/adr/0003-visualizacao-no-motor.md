# ADR 0003 — Visualização no motor científico

- **Status:** aceita
- **Data:** 2026-11-19

## Contexto

A Fase 2 prevê visualizações dos resultados quantitativos. Elas são usadas em notebooks e relatórios, antes de existir o frontend (Fase 5). A stack lista Plotly e Matplotlib. O design system em `Assets/` define que os gráficos da interface são feitos em Plotly com os tokens de cor do QuantLab. A RULE 037 exige eixos com unidades, legendas, escalas apropriadas, tooltips e tratamento de dados ausentes.

## Problema

1. Qual biblioteca usar no motor?
2. Gráficos são "componentes de interface", que a RULE 002 proíbe no motor?
3. Como garantir que o gráfico e a análise mostrem os mesmos números?

## Alternativas

| Alternativa | A favor | Contra |
|---|---|---|
| **Matplotlib** | Leve, padrão científico, ótimo para imagens estáticas. | Sem tooltips, o que contraria a RULE 037. Não é a biblioteca do design system. |
| **Plotly** | Interativo (hover), é a biblioteca prevista pelo design system, e as figuras são objetos inspecionáveis em teste. | Dependência maior. Não traz tipagem (`py.typed`). |
| **Ambas** | Flexibilidade. | Duas implementações do mesmo gráfico, o que contraria a RULE 003. |
| **Nenhuma no motor** (só no frontend) | Motor mínimo. | Notebooks e relatórios ficariam sem gráficos padronizados até a Fase 5. |

## Decisão

- Usar **Plotly** em `quantlab.visualization`, como **dependência opcional** (extra `plot`). O núcleo numérico (`analysis`, `dynamics`, `data`) continua dependendo só de NumPy e Pandas.
- As funções devolvem objetos `plotly.graph_objects.Figure`: dados mais layout. Não há servidor, aplicação nem componente de interface, o que mantém a RULE 002. O frontend continuará construindo os próprios gráficos, com os mesmos tokens.
- **Nenhum gráfico recalcula nada.** Cada valor desenhado vem da função de análise correspondente (`drawdowns`, `historical_var`, `correlation_matrix`, `rolling_volatility`). Os testes comparam os valores da figura com os da função.
- Contrato visual, verificado por testes:
  - o título é a pergunta que o gráfico responde, e o subtítulo diz o método;
  - os eixos têm nome e unidade, e todo traço tem hover;
  - séries únicas não têm caixa de legenda;
  - dados sintéticos levam o selo DEMO DATA (`demo=True`);
  - valores com sinal usam o sinal de menos tipográfico (−) e o "+" explícito;
  - grades são linhas finas e sólidas, linhas de dados têm 2 px, áreas usam ~10% de opacidade, e o texto usa os tokens de texto, nunca a cor da série.

## Validação das cores

As cores foram verificadas com o validador de paletas (ΔE em OKLab, simulando daltonismo) sobre a superfície dos painéis, `#111820`:

| Par | Resultado |
|---|---|
| azul analítico `#3B82F6` × âmbar `#F5A623` (polos da escala divergente) | passa: ΔE 33,6 no pior tipo de daltonismo |
| azul analítico × vermelho `#EA3943` (patrimônio × drawdown) | passa: ΔE 27,2 |
| azul analítico × roxo científico `#8B5CF6` | **falha**: ΔE 1,3 para deuteranopia, praticamente idênticos |

Consequências da validação:

- **O azul analítico e o roxo científico nunca devem identificar duas séries no mesmo gráfico.** Isso afeta a Fase 3, por exemplo um gráfico que compare uma série financeira com uma trajetória de sistema dinâmico. Nesse caso, use outra cor ou outra codificação, como traço, marcador ou painéis separados.
- O ponto médio da escala divergente é `#30343A` (croma 0,012, cinza neutro), e não o token de borda `#263442`. A borda tem matiz azulado (croma 0,031), e o meio da escala precisa ser lido como "nada".
- O texto dentro das células do mapa de calor usa branco ou quase preto, conforme a luminância (WCAG) da cor da célula.

## Consequências

- Quem usa só o núcleo não instala o Plotly. Os gráficos exigem `uv sync --extra plot`. No ambiente de desenvolvimento, o Plotly já vem no grupo `dev`.
- O mypy ignora a ausência de tipos apenas para `plotly.*`.
- A exportação para PNG exige o `kaleido`, que não é dependência do projeto. As imagens usadas na revisão visual foram geradas com `uv run --with kaleido`.

## Atualização — gráficos de sistemas dinâmicos (2026-11-19)

O módulo `quantlab.visualization.dynamics` aplica a mesma decisão aos sistemas dinâmicos:

- `plot_lorenz_attractor` desenha uma trajetória já calculada por `simulate_lorenz`, sem integrar nada. O subtítulo registra o método, a tolerância e o intervalo de tempo da própria trajetória. Os parâmetros só aparecem se forem informados, e nesse caso os equilíbrios de `lorenz_fixed_points` são marcados com a sua estabilidade.
- `plot_logistic_bifurcation` desenha as amostras de `logistic_bifurcation_diagram`. Usa `Scattergl` com pontos de 2 px e opacidade 0,35, para mostrar a densidade das faixas caóticas com centenas de milhares de pontos.
- As séries de dinâmica usam só o roxo científico (`SCIENCE`). O azul analítico nunca aparece no mesmo gráfico, como exige a validação de cores acima, e os testes verificam isso.
- O template ganhou eixos de cena 3D com os mesmos tokens de grade e texto dos eixos 2D. A câmera padrão do Lorenz mostra as duas asas e os equilíbrios $C^\pm$ no centro delas.
- Um diagrama com 1 200 valores de $r$ e 250 amostras cada (300 mil pontos) gera um JSON de cerca de 7,4 MB. É aceitável em notebook. Para o frontend (Fase 5), o diagrama deve ser enviado agregado, por exemplo como histograma 2D, e não como pontos.

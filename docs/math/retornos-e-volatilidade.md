# Retornos e volatilidade

Implementação: [`quantlab.analysis.returns`](../../engine/quantlab/analysis/returns.py) e [`quantlab.analysis.volatility`](../../engine/quantlab/analysis/volatility.py). Testes: [`tests/analysis/`](../../tests/analysis/).

## Notação

| Símbolo | Significado |
|---|---|
| $P_t$ | preço na observação $t$, com $t = 0, \dots, n$ |
| $R_t$ | retorno simples entre $t-1$ e $t$ |
| $r_t$ | retorno logarítmico entre $t-1$ e $t$ |
| $C_t$ | retorno acumulado de $0$ até $t$ |
| $N$ | número de períodos por ano (252 para pregões diários) |

## Definições

**Retorno simples**

$$R_t = \frac{P_t - P_{t-1}}{P_{t-1}}, \qquad t = 1, \dots, n$$

**Retorno logarítmico**

$$r_t = \ln\left(\frac{P_t}{P_{t-1}}\right) = \ln(1 + R_t)$$

Retornos logarítmicos somam no tempo: $\sum_{t=1}^{n} r_t = \ln(P_n / P_0)$. Retornos simples se compõem por produto.

**Retorno acumulado**

$$C_t = \prod_{s=1}^{t} (1 + R_s) - 1 = \frac{P_t}{P_0} - 1$$

**Volatilidade histórica**: desvio padrão amostral dos retornos $x_t$, com média $\bar x$ e $\delta$ graus de liberdade descontados (`ddof`):

$$\hat\sigma = \sqrt{\frac{1}{n - \delta} \sum_{t=1}^{n} (x_t - \bar x)^2}$$

**Volatilidade anualizada**

$$\sigma_{\text{anual}} = \hat\sigma \sqrt{N}$$

## Hipóteses e condições de validade

- Os preços são estritamente positivos e estão ordenados no tempo, com índice único.
- A série é homogênea. Preços ajustados e não ajustados não podem ser misturados (RULE 040). Para retorno total, use preços ajustados por proventos e desdobramentos.
- O retorno simples abaixo de $-100\%$ é impossível para uma posição comprada sem alavancagem. Por isso `cumulative_returns` rejeita $R_t < -1$ e trata $R_t = -1$ como perda total: daí em diante, $C_t = -1$.
- A regra da raiz do tempo ($\sqrt{N}$) supõe retornos independentes e identicamente distribuídos, observados em intervalos regulares. Sob essa hipótese, a variância de $N$ períodos é $N$ vezes a variância de um período.
- Com $\delta = 1$, o estimador da variância é não viesado sob amostragem independente. O desvio padrão em si continua levemente viesado (desigualdade de Jensen).

## Método numérico

- **Retorno simples:** calculado como $(P_t - P_{t-1}) / P_{t-1}$, e não como $P_t / P_{t-1} - 1$. Pelo lema de Sterbenz, a subtração de dois preços vizinhos em ponto flutuante é exata. Isso preserva a precisão relativa de retornos muito pequenos. O teste `test_tiny_moves_keep_relative_accuracy` compara o resultado com a fração exata.
- **Retorno logarítmico:** `log1p` do retorno simples. Evita o cancelamento de $\ln P_t - \ln P_{t-1}$ quando os preços são próximos.
- **Retorno acumulado:** `expm1(cumsum(log1p(R)))`, que evita perder dígitos em $1 + R$ e na subtração final de 1. A perda total vira $\ln(0) = -\infty$ e $\operatorname{expm1}(-\infty) = -1$, exatamente.
- **Volatilidade:** `numpy.std`, que calcula primeiro a média e depois os desvios (duas passagens). A fórmula de uma passagem $E[x^2] - E[x]^2$ é evitada porque cancela catastroficamente quando a média é grande em relação à dispersão. O teste `test_large_mean_does_not_cause_cancellation` cobre esse caso.
- Uma série de valores iguais pode resultar em volatilidade da ordem de $10^{-18}$, e não exatamente zero, porque a média em ponto flutuante de valores como 0,004 não é exatamente 0,004. Esse resíduo é erro de arredondamento ($\approx \varepsilon\,|x|$), não um bug.

## Validação de entrada

Todas as funções rejeitam, com exceções específicas (`quantlab.exceptions`):

- objetos que não são `pandas.Series` ou que não têm dtype numérico (`TypeError`);
- séries curtas demais (`InsufficientDataError`): 2 preços para retornos, 1 retorno para o acumulado, $\max(2, \delta + 1)$ observações para a volatilidade;
- valores ausentes (`NaN`, `pd.NA`) e infinitos (`InputValidationError`);
- índice com rótulos duplicados ou fora de ordem crescente (`InputValidationError`);
- valores fora do domínio, como preços $\le 0$ ou retornos $< -1$ (`DomainError`).

As funções não limpam dados: não removem ausentes, não ordenam e não cortam valores. A limpeza é responsabilidade do módulo Market Data (Fase 2).

## Limitações

- A anualização pela raiz do tempo falha sob agrupamento de volatilidade (clusters) e autocorrelação, comuns em mercados reais. O número anualizado é uma convenção para comparar ativos, não uma previsão.
- Os 252 pregões por ano são uma convenção. O calendário real varia por mercado e por ano. Para dados semanais ou mensais, passe `periods_per_year=52` ou `12`.
- A volatilidade histórica de amostra inteira trata todo o período como um único regime. Volatilidade móvel e modelos condicionais (GARCH) ficam para fases seguintes.
- Os retornos não consideram custos de transação, impostos ou câmbio.

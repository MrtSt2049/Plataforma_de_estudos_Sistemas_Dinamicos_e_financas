# Desempenho, risco e dependência

Implementação: [`performance.py`](../../engine/quantlab/analysis/performance.py), [`drawdown.py`](../../engine/quantlab/analysis/drawdown.py), [`risk.py`](../../engine/quantlab/analysis/risk.py), [`correlation.py`](../../engine/quantlab/analysis/correlation.py) e [`indicators.py`](../../engine/quantlab/analysis/indicators.py). Testes: [`tests/analysis/`](../../tests/analysis/).

Notação geral: $x_t$ são retornos simples por período, $n$ é o número de observações e $N$ o número de períodos por ano.

## Índice de Sharpe

$$\text{SR} = \frac{\overline{x - r_f}}{\hat\sigma(x - r_f)} \sqrt{N}$$

- $r_f$ é a taxa livre de risco **por período**. Uma taxa anual efetiva (CDI, por exemplo) se converte com `periodic_rate_from_annual`:

  $$r_{\text{período}} = (1 + r_{\text{anual}})^{1/N} - 1$$

  A conversão é calculada como `expm1(log1p(r) / N)`. Para $r = 12\%$ ao ano e $N = 12$, o resultado coincide com o valor correto até o último dígito de um double. A fórmula ingênua `(1.12)**(1/12) - 1` erra na 15ª casa (erro relativo de $7{,}5 \times 10^{-15}$, comparado com um cálculo de 50 dígitos no teste `test_monthly_rate_is_correctly_rounded`).
- Uma taxa livre de risco constante desloca a média, mas não o desvio padrão.
- **Retornos com dispersão nula** tornam o índice indefinido, e a função levanta `ComputationError`. Isso inclui dispersão no nível do arredondamento: vinte cópias de 0,004 dão um desvio calculado de cerca de $10^{-18}$, o que produziria um "Sharpe" da ordem de $10^{15}$. O critério é $\hat\sigma \le 4\, n\, \varepsilon \max|x|$, o limite do erro de arredondamento da média.

**Limitações.** A anualização por $\sqrt N$ supõe retornos i.i.d. Sob autocorrelação ela distorce o índice (Lo, 2002). O erro padrão da estimativa por período é cerca de $\sqrt{(1 + \text{SR}^2/2)/n}$. Com um ano de dados diários ($n = 252$), isso dá cerca de 0,063 por período, ou cerca de 1,0 anualizado, ou seja, o índice estimado em um ano é muito impreciso.

## Drawdown

$$M_t = \max_{s \le t} P_s, \qquad D_t = \frac{P_t - M_t}{M_t} \le 0, \qquad \text{MDD} = \min_t D_t$$

- `max_drawdown` informa o valor e três datas. O **pico** é a última vez em que o máximo foi atingido antes do vale. O **vale** é o ponto mais baixo. A **recuperação** é a primeira data após o vale com preço igual ou acima do pico, ou `None` se ainda não houve recuperação.
- Em empate entre quedas igualmente piores, a primeira é informada.
- Para analisar retornos, construa o índice de riqueza $1 + C_t$ precedido do nível inicial 1. Sem esse ponto inicial, uma queda logo no primeiro período não seria contada.

## VaR e CVaR históricos

As perdas são $L_t = -x_t$, ordenadas como $L_{(1)} \le \dots \le L_{(n)}$, com nível de confiança $\alpha$ e $m = n(1-\alpha)$.

$$\text{VaR}_\alpha = L_{(\lceil n\alpha \rceil)}$$

$$\text{CVaR}_\alpha = \frac{1}{m}\left[\sum_{i=1}^{\lfloor m \rfloor} L_{[i]} + (m - \lfloor m \rfloor)\, L_{[\lfloor m \rfloor + 1]}\right]$$

Aqui $L_{[i]}$ é a $i$-ésima **maior** perda.

- **Convenção de sinal:** os dois são informados como perdas. Um VaR de 0,021 a 95% significa que 95% dos retornos observados ficaram acima de −2,1%. Se até o quantil for um ganho, o VaR sai negativo.
- O VaR é o quantil empírico, o inverso generalizado da distribuição empírica, calculado com `numpy.quantile(..., method="inverted_cdf")`. Não há interpolação: o resultado é sempre uma perda observada.
- O CVaR (Expected Shortfall) usa o estimador de Acerbi e Tasche (2002), que pondera fracionariamente a observação de fronteira. Isso o torna uma medida coerente, contínua em $\alpha$, e garante $\text{CVaR}_\alpha \ge \text{VaR}_\alpha$.
- **Amostra mínima:** a cauda precisa conter pelo menos uma observação inteira, $n(1-\alpha) \ge 1$. São 20 observações a 95% e 100 a 99%. Abaixo disso, a estimativa seria apenas a pior perda com outro nome.

Verificações nos testes:

1. valores calculados à mão com perdas $1, 2, \dots, n$;
2. o CVaR comparado com a definição integral $\frac{1}{1-\alpha}\int_\alpha^1 \text{VaR}_u\, du$, integrada numericamente;
3. para uma amostra normal grande, comparação com os valores analíticos $\sigma z_\alpha$ e $\sigma\,\varphi(z_\alpha)/(1-\alpha)$, calculados com `statistics.NormalDist`;
4. translação ($\text{VaR}(x + c) = \text{VaR}(x) - c$) e homogeneidade positiva ($\text{VaR}(\lambda x) = \lambda\,\text{VaR}(x)$).

**Limitações.** O método histórico supõe que o futuro se parece com a amostra. Ele não extrapola além da pior perda observada e reage lentamente a mudanças de regime. O horizonte é o da série de entrada (um dia, para retornos diários). Não há conversão para outros horizontes, porque a regra $\sqrt h$ exige retornos i.i.d.

## Covariância e correlação

$$\Sigma = \frac{(X - \bar X)^\top (X - \bar X)}{n - \delta}, \qquad \rho_{ij} = \frac{\Sigma_{ij}}{\sqrt{\Sigma_{ii}\Sigma_{jj}}}$$

- O cálculo é feito em duas passagens (centraliza, depois multiplica) e a matriz é simetrizada, $(\Sigma + \Sigma^\top)/2$, para eliminar a assimetria de arredondamento.
- Na correlação, entradas que o arredondamento empurra para fora de $[-1, 1]$ (como $1{,}0000000000000002$) são cortadas de volta ao intervalo, e a diagonal é exatamente 1.
- Uma coluna com dispersão nula torna a correlação indefinida, e a função levanta `ComputationError` com o nome da coluna.
- As séries precisam estar alinhadas antes da chamada. A função rejeita valores ausentes em vez de usar pares disponíveis (*pairwise*), que podem gerar matrizes não positivas semidefinidas.

**Limitações.** A correlação de Pearson mede só dependência *linear*. Ela é instável no tempo e tende a subir em crises, justamente quando a diversificação seria mais necessária. Com $n \le k$ (menos observações que ativos), a covariância é singular.

## Indicadores

- **Média móvel simples:** $\text{SMA}_t = \frac1w \sum_{i=0}^{w-1} x_{t-i}$. As posições sem janela completa são descartadas, e não preenchidas com NaN.
- **Média móvel exponencial:** $\text{EMA}_t = a\,x_t + (1-a)\,\text{EMA}_{t-1}$, com $a = 2/(s+1)$ e $\text{EMA}_0 = x_0$. Os primeiros valores são enviesados para $x_0$. O peso desse início cai abaixo de 5% depois de cerca de $3s$ observações.
- **Volatilidade móvel** (em `volatility.py`): cada janela é calculada pelo mesmo algoritmo de duas passagens da volatilidade histórica. Assim se evita a deriva das somas acumuladas que as versões *online* introduzem em séries longas.

Médias móveis descrevem o passado. Sozinhas, não são evidência de previsibilidade.

## Referências

- Sharpe, W. F. (1994). The Sharpe Ratio. *Journal of Portfolio Management* 21(1).
- Lo, A. W. (2002). The Statistics of Sharpe Ratios. *Financial Analysts Journal* 58(4).
- Acerbi, C. e Tasche, D. (2002). On the coherence of Expected Shortfall. *Journal of Banking & Finance* 26(7), 1487–1503.

# Sistema de Lorenz

Implementação: [`quantlab.dynamics.lorenz`](../../engine/quantlab/dynamics/lorenz.py), com o integrador genérico em [`quantlab.dynamics.integration`](../../engine/quantlab/dynamics/integration.py) e a estabilidade de equilíbrios em [`quantlab.dynamics.stability`](../../engine/quantlab/dynamics/stability.py). Testes: [`tests/dynamics/test_lorenz.py`](../../tests/dynamics/test_lorenz.py), [`test_integration.py`](../../tests/dynamics/test_integration.py) e [`test_flow_stability.py`](../../tests/dynamics/test_flow_stability.py). A escolha do integrador está no [ADR 0004](../adr/0004-integracao-numerica.md).

## Definição

$$\dot x = \sigma (y - x), \qquad \dot y = x(\rho - z) - y, \qquad \dot z = xy - \beta z, \qquad \sigma, \rho, \beta > 0$$

Lorenz (1963) chegou a essas equações truncando o problema da convecção numa camada de fluido aquecida por baixo em três modos. $\sigma$ é o número de Prandtl, $\rho$ é o número de Rayleigh dividido pelo seu valor crítico e $\beta$ é um fator geométrico. Os parâmetros canônicos são $\sigma = 10$, $\rho = 28$ e $\beta = 8/3$. O motor exige os três estritamente positivos (`LorenzParameters` rejeita o resto com `DomainError`), que é o domínio com significado físico.

A jacobiana é

$$DF = \begin{pmatrix} -\sigma & \sigma & 0 \\ \rho - z & -1 & -x \\ y & x & -\beta \end{pmatrix}.$$

## Propriedades estruturais

**Simetria.** O campo satisfaz $F(-x, -y, z) = (-F_1, -F_2, F_3)$. Se $(x(t), y(t), z(t))$ é solução, $(-x(t), -y(t), z(t))$ também é. Os testes verificam isso no campo (igualdade exata) e nas trajetórias integradas.

**Eixo $z$ invariante.** Com $x = y = 0$, as duas primeiras equações dão $\dot x = \dot y = 0$ e a terceira vira $\dot z = -\beta z$. Logo $z(t) = z_0 e^{-\beta t}$ é solução exata. Os testes comparam a integração numérica com essa fórmula, com tolerância relativa de $10^{-9}$ e absoluta de $10^{-11}$ (esta para os valores de $z$ já próximos de zero), e verificam que $x$ e $y$ ficam exatamente nulos.

**Dissipação.** O divergente do campo é constante:

$$\nabla \cdot F = \operatorname{tr} DF = -(\sigma + 1 + \beta).$$

Um volume de condições iniciais encolhe como $e^{-(\sigma + 1 + \beta)t}$, ou seja, $e^{-13{,}67\,t}$ nos parâmetros canônicos. O atrator, portanto, tem volume zero.

**Bola de captura.** Seja $V = x^2 + y^2 + (z - \sigma - \rho)^2$. Derivando ao longo das soluções,

$$\dot V = -2\left[\sigma x^2 + y^2 + \beta (z - c)^2 - \beta c^2\right], \qquad c = \frac{\sigma + \rho}{2},$$

que é negativo fora do elipsoide $E$: $\sigma x^2 + y^2 + \beta (z - c)^2 = \beta c^2$. Para $\sigma \ge 1$ e $\beta > 1$, o máximo de $V$ sobre $E$ é no máximo

$$R^2 = \frac{(\sigma + \rho)^2 \beta^2}{4(\beta - 1)}.$$

Basta usar $x^2 \le \sigma x^2$ e maximizar em $z$. Então a bola $V \le R^2$ é invariante: trajetórias que começam nela não saem, e as que começam fora entram. Nos parâmetros canônicos, $R^2 \approx 1540{,}27$ ($R \approx 39{,}25$, com centro em $(0, 0, 38)$). O teste parte de dentro e de fora da bola e verifica as duas afirmações.

## Equilíbrios

**Origem.** $(0, 0, 0)$ é sempre equilíbrio. Ali a jacobiana tem bloco desacoplado em $z$, com autovalor $-\beta$, e o bloco $(x, y)$ dá

$$\mu_\pm = \frac{-(\sigma + 1) \pm \sqrt{(\sigma + 1)^2 + 4\sigma(\rho - 1)}}{2}.$$

Para $\rho < 1$ os três autovalores são negativos e a origem é estável. Em $\rho = 1$, $\mu_+ = 0$, o caso não hiperbólico. Para $\rho > 1$, $\mu_+ > 0$ e a origem vira uma sela com exatamente uma direção instável.

**$C^\pm$.** Para $\rho > 1$ surgem, numa bifurcação de forquilha em $\rho = 1$,

$$C^\pm = \left(\pm\sqrt{\beta(\rho - 1)},\ \pm\sqrt{\beta(\rho - 1)},\ \rho - 1\right).$$

Em $\rho = 1$ eles coincidem com a origem, e `lorenz_fixed_points` os omite. O polinômio característico em $C^\pm$ é

$$p(\mu) = \mu^3 + (\sigma + \beta + 1)\mu^2 + \beta(\sigma + \rho)\mu + 2\sigma\beta(\rho - 1).$$

Pelo critério de Routh-Hurwitz, todas as raízes têm parte real negativa exatamente quando $(\sigma + \beta + 1)(\sigma + \rho) > 2\sigma(\rho - 1)$. Os outros dois coeficientes já são positivos para $\rho > 1$.

## Bifurcação de Hopf

Se $\sigma > \beta + 1$, a condição de Routh-Hurwitz falha a partir de

$$\rho_H = \frac{\sigma(\sigma + \beta + 3)}{\sigma - \beta - 1}.$$

Nesse valor, um par de autovalores de $C^\pm$ cruza o eixo imaginário em $\pm i\sqrt{\beta(\sigma + \rho_H)}$. Nos parâmetros canônicos, $\rho_H = 470/19 \approx 24{,}7368$ e a frequência é $\approx 9{,}6245$. A bifurcação é subcrítica: o ciclo limite instável que envolve $C^\pm$ encolhe até eles quando $\rho \to \rho_H^-$ (Sparrow, 1982; Strogatz, cap. 9).

Se $\sigma \le \beta + 1$, a desigualdade de Routh-Hurwitz vale para todo $\rho > 1$, e $C^\pm$ nunca perdem a estabilidade linear. `lorenz_hopf_rho` devolve `None` nesse caso. Os testes conferem isso em $\rho$ até 5 000.

### Regimes com $\sigma = 10$, $\beta = 8/3$

| $\rho$ | Equilíbrios (classificação do motor) | Observação |
|---|---|---|
| $0 < \rho < 1$ | origem `STABLE` | as trajetórias decaem para a origem |
| $\rho = 1$ | origem `NON_HYPERBOLIC` | forquilha |
| $1 < \rho < \rho_H$ | origem `UNSTABLE` (sela), $C^\pm$ `STABLE` | trajetórias típicas convergem para $C^+$ ou $C^-$ |
| $\rho = \rho_H$ | $C^\pm$ `NON_HYPERBOLIC` | Hopf subcrítica |
| $\rho > \rho_H$ | os três `UNSTABLE` | em $\rho = 28$, atrator estranho |

Valores da literatura, que o motor **não** verifica: caos transiente a partir de $\rho \approx 13{,}926$ (explosão homoclínica), e atrator estranho a partir de $\rho \approx 24{,}06$, coexistindo com $C^\pm$ estáveis até $\rho_H$ (Kaplan e Yorke, 1979; Sparrow, 1982). Perto de $\rho_H$ a classificação linear diz que $C^\pm$ são estáveis, mas uma trajetória pode estar no atrator caótico em vez de convergir para eles.

### Valores canônicos ($\rho = 28$), calculados pelo motor

| Equilíbrio | Posição | Autovalores |
|---|---|---|
| origem | $(0, 0, 0)$ | $11{,}8277$; $-2{,}6667$; $-22{,}8277$ |
| $C^\pm$ | $(\pm 8{,}4853, \pm 8{,}4853, 27)$ | $0{,}0940 \pm 10{,}1945\,i$; $-13{,}8546$ |

$C^\pm$ são selas-foco: uma direção estável real e um par complexo instável, que faz a trajetória espiralar para fora em torno de cada "asa" da borboleta.

## Estabilidade de equilíbrios de fluxos

`analyze_equilibrium` calcula os autovalores da jacobiana (`numpy.linalg.eigvals`) e `classify_flow_equilibrium` os classifica:

| Autovalores $\mu_i$ | Classificação |
|---|---|
| todo $\operatorname{Re}\mu_i < -\text{atol}$ | `STABLE` |
| algum $\operatorname{Re}\mu_i > \text{atol}$ | `UNSTABLE`, mesmo que outros estejam no eixo imaginário |
| caso contrário | `NON_HYPERBOLIC`: a linearização não decide |

A tolerância padrão é `DEFAULT_EIGENVALUE_ATOL = 1e-10`. Autovalores calculados por um método estável carregam erro da ordem de $\varepsilon \lVert J \rVert$. Medido no Lorenz, onde $\lVert J \rVert$ fica entre 15 e 30 nos equilíbrios, esse erro fica em torno de $2 \times 10^{-15}$. Em $\rho_H$ exato, a parte real calculada sai $-4{,}4 \times 10^{-16}$ e não zero. A $10^{-6}$ de $\rho_H$, ela vale $\pm 3{,}0 \times 10^{-8}$, bem acima da tolerância: os testes verificam que $C^\pm$ são `STABLE` em $\rho_H - 10^{-6}$, `NON_HYPERBOLIC` em $\rho_H$ e `UNSTABLE` em $\rho_H + 10^{-6}$.

## Método numérico

- A integração usa `integrate_autonomous`, que chama `scipy.integrate.solve_ivp`. O método padrão é o **DOP853** (Runge-Kutta explícito de ordem 8, Dormand-Prince), com `rtol = 1e-10` e `atol = 1e-12`. RK45 e Radau estão disponíveis, e o Radau recebe a jacobiana analítica.
- O passo de integração é adaptativo e independente da grade de saída. Os estados em $t_k = k\,\Delta t$ vêm do interpolador denso do método. Um `dt` grosso registra menos pontos, mas não piora a precisão (verificado em teste).
- A tolerância controla o erro **local** de cada passo. O erro global depende da dinâmica (ver a próxima seção).
- A simulação é determinística na mesma plataforma e com as versões travadas no `uv.lock`. A simetria $(x, y) \to (-x, -y)$ também se preserva na prática: em teste, a trajetória espelhada coincidiu com a original até a tolerância de $10^{-12}$.
- Testes de precisão contra soluções exatas: decaimento exponencial e oscilador harmônico (`test_integration.py`), eixo $z$ do Lorenz, taxa de decaimento para a origem com $\rho = 0{,}5$ e comparação entre métodos com uma referência de `rtol = 1e-13`.

Para $\rho = 0{,}5$, a distância à origem decai como $e^{\mu_+ t}$, com $\mu_+ \approx -0{,}475062$. O ajuste de $\ln\lVert\mathbf x(t)\rVert$ entre $t = 10$ e $t = 25$ deu inclinação $-0{,}475063$.

## Sensibilidade às condições iniciais

Medido com o motor: duas trajetórias canônicas partindo de $(1, 1, 1)$ e $(1, 1, 1 + 10^{-9})$ estão separadas por $7{,}2 \times 10^{-6}$ em $t = 20$, $0{,}155$ em $t = 30$ e $6{,}2$ em $t = 40$, que é da ordem do tamanho do atrator. Com $\rho = 10$, a mesma perturbação encolhe: a separação é de $1{,}6 \times 10^{-11}$ em $t = 40$.

O maior expoente de Lyapunov no caso canônico é $\lambda_{\max} \approx 0{,}906$ (valor da literatura, por exemplo Sprott, 2003, **não** calculado pelo motor). Um erro inicial $\delta_0$ chega à ordem do atrator em $t^* \approx \ln(L/\delta_0)/\lambda_{\max}$. Erros de arredondamento e de tolerância, de $10^{-10}$ a $10^{-16}$, dão um horizonte de previsibilidade de algumas dezenas de unidades de tempo. Depois disso, a trajetória calculada não está mais perto da solução exata que parte do mesmo ponto, embora continue sendo uma trajetória do atrator.

Consequência prática: estatísticas do atrator (distribuições, médias temporais, a forma da borboleta) são confiáveis. O valor de $x(t)$ em $t = 100$ a partir de um estado inicial específico não é.

## Limitações

- A classificação de estabilidade é linear. Em casos não hiperbólicos o motor só informa `NON_HYPERBOLIC`. Estabilidade linear de $C^\pm$ não implica que uma trajetória converge para eles: perto de $\rho_H$, existe também o atrator caótico.
- O motor ainda não calcula expoentes de Lyapunov de fluxos, ciclos limite, órbitas homoclínicas nem a dimensão do atrator. Os valores da literatura citados acima não são verificados.
- Parâmetros muito grandes (por exemplo $\rho \sim 10^4$) tornam a dinâmica mais rápida e o sistema mais exigente para métodos explícitos. Nesse caso, `method="Radau"` é a alternativa.
- Simular um modelo caótico mostra o que o modelo faz. Não prova que um mercado, ou qualquer sistema real, seja determinístico ou caótico.

## Referências

- E. N. Lorenz. *Deterministic Nonperiodic Flow*. Journal of the Atmospheric Sciences, 20(2), 130–141, 1963.
- C. Sparrow. *The Lorenz Equations: Bifurcations, Chaos, and Strange Attractors*. Springer, 1982.
- J. L. Kaplan e J. A. Yorke. *Preturbulence: a regime observed in a fluid flow model of Lorenz*. Communications in Mathematical Physics, 67, 93–108, 1979.
- S. H. Strogatz. *Nonlinear Dynamics and Chaos*, cap. 9. Westview Press, 2ª ed., 2015.
- J. C. Sprott. *Chaos and Time-Series Analysis*. Oxford University Press, 2003.
- J. R. Dormand e P. J. Prince. *A family of embedded Runge-Kutta formulae*. Journal of Computational and Applied Mathematics, 6(1), 19–26, 1980.
- E. Hairer, S. P. Nørsett e G. Wanner. *Solving Ordinary Differential Equations I: Nonstiff Problems*. Springer, 2ª ed., 1993 (DOP853).

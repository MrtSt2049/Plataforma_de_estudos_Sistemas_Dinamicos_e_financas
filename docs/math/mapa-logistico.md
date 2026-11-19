# Mapa logístico

Implementação: [`quantlab.dynamics.logistic`](../../engine/quantlab/dynamics/logistic.py), [`quantlab.dynamics.stability`](../../engine/quantlab/dynamics/stability.py) e [`quantlab.dynamics.orbits`](../../engine/quantlab/dynamics/orbits.py). Gráfico: [`quantlab.visualization.dynamics`](../../engine/quantlab/visualization/dynamics.py). Testes: [`tests/dynamics/`](../../tests/dynamics/).

## Definição

$$x_{t+1} = f(x_t) = r \, x_t (1 - x_t), \qquad x_t \in [0, 1], \; r \in [0, 4]$$

Para $r \in [0, 4]$, o máximo de $f$ em $[0,1]$ é $f(1/2) = r/4 \le 1$, então o intervalo $[0,1]$ é invariante: órbitas que começam nele não saem. Fora desse intervalo de $r$ isso deixa de valer, e o motor rejeita o parâmetro com `DomainError`.

A derivada é $f'(x) = r(1 - 2x)$.

## Pontos fixos e estabilidade

Um ponto fixo satisfaz $x^* = f(x^*)$. Linearizando em torno dele, uma perturbação $\varepsilon_t = x_t - x^*$ evolui como $\varepsilon_{t+1} \approx \lambda\, \varepsilon_t$, com multiplicador $\lambda = f'(x^*)$:

| Multiplicador | Classificação (`FixedPointStability`) |
|---|---|
| $\lvert\lambda\rvert < 1$ | `STABLE`: perturbações decaem |
| $\lvert\lambda\rvert > 1$ | `UNSTABLE`: perturbações crescem |
| $\lvert\lambda\rvert = 1$ | `NON_HYPERBOLIC`: a linearização não decide; é onde ocorrem bifurcações |

Para o mapa logístico:

- $x = 0$ é sempre ponto fixo, com $\lambda = r$. É estável para $r < 1$.
- Para $r > 1$ existe $x^* = 1 - 1/r$, com $\lambda = r(1 - 2x^*) = 2 - r$. É estável para $1 < r < 3$, porque $\lvert 2 - r \rvert < 1$.
- Em $r = 3$, $\lambda = -1$: começa a cascata de duplicação de período.

Em ponto flutuante, o multiplicador em $r = 3$ sai como $-1{,}0000000000000004$, e não exatamente $-1$. Por isso a classificação usa uma tolerância (`DEFAULT_MULTIPLIER_ATOL = 1e-12`) em torno de $\lvert\lambda\rvert = 1$.

## Ciclo de período 2

Para $3 < r < 1 + \sqrt 6 \approx 3{,}449$, a órbita converge para um 2-ciclo estável:

$$x_\pm = \frac{(r + 1) \pm \sqrt{(r - 3)(r + 1)}}{2r}$$

Seu multiplicador é $f'(x_+) f'(x_-) = 4 + 2r - r^2$. Os testes comparam a órbita simulada em $r = 3{,}2$ com esses valores analíticos.

## Duplicação de período e caos

A sequência de bifurcações $r_1 = 3$, $r_2 = 1 + \sqrt 6$, $r_3 \approx 3{,}5441$, … acumula em $r_\infty \approx 3{,}5699$. Além desse ponto aparecem órbitas caóticas, intercaladas com janelas periódicas. A mais visível é a janela de período 3, que começa em $r = 1 + \sqrt 8 \approx 3{,}8284$.

`detect_period` encontra o menor período $p$ tal que $\lvert x_{t+p} - x_t \rvert \le$ `atol` para todos os pontos da amostra, depois de descartado o transiente. Os testes executam o mapa com transiente de 20 000 iterações e janela de 2 000, `atol = 1e-9`, e verificam:

| $r$ | Período esperado | Motivo |
|---|---|---|
| 2,8 | 1 | ponto fixo estável |
| 3,2 | 2 | após $r_1 = 3$ |
| 3,5 | 4 | após $r_2 \approx 3{,}449$ |
| 3,555 | 8 | após $r_3 \approx 3{,}5441$ |
| 3,835 | 3 | janela de período 3 |
| 3,9 e 4,0 | nenhum até 64 | região caótica |

## Diagrama de bifurcação

`logistic_bifurcation_diagram(r_values, x0, n_transient, n_samples)` itera o mapa para cada $r_i$ a partir do mesmo $x_0$, descarta os primeiros $T$ estados e guarda os $N$ seguintes, $x_T, \dots, x_{T+N-1}$. Desenhar essas amostras contra $r$ dá o diagrama de bifurcação: um ponto onde a órbita converge para um ponto fixo, $p$ pontos num $p$-ciclo e uma faixa preenchida onde ela é caótica.

A recorrência é sequencial no tempo, mas independente entre valores de $r$. Por isso todos os $r_i$ avançam juntos, um passo vetorizado por vez (RULE 015). Cada linha do resultado é idêntica, bit a bit, à órbita de `simulate_logistic_map` com o mesmo $r$, e os testes verificam essa igualdade. Também verificam o valor único $1 - 1/r$ no regime de ponto fixo, os dois valores analíticos do 2-ciclo em $r = 3{,}2$ e, em $r = 4$, amostras espalhadas por todo o intervalo $[0, 1]$.

`quantlab.visualization.plot_logistic_bifurcation` desenha o diagrama com pontos pequenos e translúcidos, para que a densidade das faixas caóticas apareça. Linhas pontilhadas marcam os valores exatos $r = 3$, $1 + \sqrt 6$ e $1 + \sqrt 8$.

Limitações: perto de uma bifurcação a convergência é lenta, e um transiente curto deixa pontos ainda a caminho do atrator, o que borra o diagrama nessas regiões. Uma faixa que parece caótica na figura não prova caos. Para isso serve o expoente de Lyapunov.

## Expoente de Lyapunov

$$\lambda_L = \lim_{N \to \infty} \frac{1}{N} \sum_{t=0}^{N-1} \ln \lvert f'(x_t) \rvert$$

`logistic_lyapunov_exponent` estima esse limite com uma média finita, depois de descartar um transiente. $\lambda_L > 0$ indica dependência sensível às condições iniciais (caos). $\lambda_L < 0$ indica convergência para um ponto fixo ou ciclo estável.

Valores analíticos usados como teste:

| Caso | Valor exato |
|---|---|
| ponto fixo estável ($r < 1$ ou $1 < r < 3$) | $\ln\lvert\lambda\rvert$ do ponto fixo |
| 2-ciclo em $r = 3{,}2$ | $\tfrac12 \ln\lvert 4 + 2r - r^2 \rvert = \ln 0{,}4$ |
| $r = 4$ | $\ln 2$ |
| bifurcação em $r = 3$ | $0$ |
| $r = 2$ (ponto fixo superestável em $1/2$) | $-\infty$ |

Nos testes, a estimativa em $r = 4$, com $N = 200\,000$ e $x_0 = 0{,}1234$, fica a menos de $5 \times 10^{-3}$ de $\ln 2$.

## Método numérico

- A recorrência é sequencial por natureza e é avaliada num laço simples. Para os tamanhos usados (até ~$10^5$ passos) o custo é pequeno. Se for preciso escalar, a alternativa é compilar o laço (por exemplo com Numba), não vetorizá-lo.
- A simulação é determinística: os mesmos argumentos geram o mesmo array na mesma plataforma.
- Em parâmetros caóticos, o erro de arredondamento cresce à taxa $e^{\lambda_L t}$. Depois de algumas dezenas de passos, a órbita calculada já se afastou da órbita exata de $x_0$. Pelo lema de sombreamento, ela continua sendo uma órbita típica da mesma dinâmica, que é o que estatísticas como o expoente de Lyapunov exigem. Valores pontuais de $x_t$ para $t$ grande em regime caótico não devem ser interpretados como previsões.

## Limitações

- O teste de estabilidade é linear. Em casos não hiperbólicos, termos de ordem superior decidem, e o motor apenas informa `NON_HYPERBOLIC`.
- `detect_period` retornar `None` é compatível com caos, mas não prova caos: o período pode ser maior que `max_period`, ou a órbita pode ainda estar convergindo (perto de bifurcações a convergência é lenta).
- O expoente de Lyapunov é uma estimativa de tempo finito. O erro diminui aproximadamente como $1/\sqrt N$ em órbitas caóticas e depende da condição inicial. Condições iniciais eventualmente fixas, como $x_0 = 0$, $x_0 = 1$, ou $x_0 = 1/2$ com $r = 4$, dão o expoente desse ponto fixo, e não o da órbita típica.
- Simular um modelo caótico mostra o que o modelo faz. Não prova que um mercado real seja determinístico ou caótico.

# Processos de Markov em tempo contínuo

Status: **fundamentação teórica** (base matemática de apoio para a Fase 6 — modelos estocásticos, processos de saltos e transições contínuas). Ainda não há módulo dedicado implementado em `engine/quantlab/`; quando existir, esta página passará a apontar para o código e os testes correspondentes.

## Escopo e conexão com o QuantLab

Processos de Markov em tempo contínuo com espaço de estados enumerável generalizam as cadeias discretas permitindo que as transições ocorram em instantes aleatórios contínuos $t \in [0, \infty)$. Na interface entre sistemas dinâmicos e finanças quantitativas, eles conectam a teoria de equações diferenciais lineares ($P'(t) = P(t)Q$) com processos de contagem (Processo de Poisson), modelos de saltos em preços (*jump diffusion* previstos na Fase 6), migração contínua de risco de crédito e dinâmica de filas / microestrutura de livro de ofertas.

Documentos relacionados:

- [Fundamentos de probabilidade, convergência, ergodicidade e grandes desvios](fundamentos-de-probabilidade.md)
- [Esperança condicional, martingais e apreçamento em tempo discreto](esperanca-condicional-e-martingais.md)
- [Cadeias de Markov em tempo discreto](cadeias-de-markov-tempo-discreto.md)

## Notação

| Símbolo | Significado |
|---|---|
| $S$ | espaço de estados enumerável |
| $(X_t)_{t \ge 0}$ | processo estocástico em tempo contínuo com trajetórias contínuas à direita |
| $J_n$, $S_n$ | $n$-ésimo tempo de transição (salto) e $n$-ésimo tempo de permanência ($S_n = J_n - J_{n-1}$) |
| $\zeta = \sum_{n=1}^{\infty} S_n$ | tempo de explosão (acúmulo de infinitos saltos em tempo finito) |
| $Y_n = X_{J_n}$ | cadeia de transição embutida (*jump chain*) |
| $Q = (q_{ij})_{i, j \in S}$ | matriz geradora (ou matriz-$Q$ de taxas instantâneas) |
| $q_i = -q_{ii} = \sum_{j \neq i} q_{ij}$ | taxa total de saída do estado $i$ |
| $\Pi = (\pi_{ij})$ | matriz de transição da cadeia embutida ($\pi_{ij} = q_{ij}/q_i$ para $j \neq i$, se $q_i > 0$) |
| $P(t) = (p_{ij}(t))$ | matriz de probabilidades de transição no horizonte $t$ |
| $D^A$, $T_i$ | tempo de primeira chegada a $A$ e tempo de primeiro retorno a $i$ após deixar $i$ |
| $\lambda = (\lambda_i)_{i \in S}$ | distribuição invariante em tempo contínuo ($\lambda Q = 0$) |

## 1. Trajetórias, tempos de salto e explosão

Consideram-se processos $(X_t)_{t \ge 0}$ com trajetórias **contínuas à direita** (constantes por partes entre saltos): para todo $t \ge 0$, existe $\varepsilon > 0$ tal que $X_s = X_t$ para $s \in [t, t + \varepsilon)$.

Definem-se recursivamente os **tempos de salto** $J_0 = 0$ e

$$J_{n+1} = \inf \{t \ge J_n : X_t \neq X_{J_n}\},$$

os **tempos de permanência** (*holding times*) $S_n = J_n - J_{n-1}$ (se $J_{n-1} < \infty$; caso contrário $S_n = \infty$), a **cadeia embutida** $Y_n = X_{J_n}$ e o **tempo de explosão**

$$\zeta = \sup_{n \ge 0} J_n = \sum_{n=1}^{\infty} S_n.$$

- O processo é **não explosivo** se $\mathbb{P}_i(\zeta = \infty) = 1$ para todo $i \in S$. Nesse caso, as trajetórias ficam unicamente determinadas em todo $[0, \infty)$ pelos saltos $(Y_n, S_n)$.
- Quando $\zeta < \infty$ com probabilidade positiva, convenciona-se construir o **processo mínimo**, atribuindo um estado cemitério $\infty$ para $t \ge \zeta$.

## 2. Matriz geradora $Q$ e semigrupo estocástico

Uma matriz $Q = (q_{ij})_{i, j \in S}$ é uma **matriz geradora** (ou matriz-$Q$) se satisfaz:

1. $0 \le -q_{ii} = q_i < \infty$ para todo $i \in S$;
2. $q_{ij} \ge 0$ para todos $i \neq j$;
3. $\sum_{j \in S} q_{ij} = 0$ para todo $i \in S$ (isto é, $q_i = \sum_{j \neq i} q_{ij}$).

### Exponencial matricial e equações de Kolmogorov (espaço finito)

Quando $S$ é finito, a série exponencial de matrizes $P(t) = e^{tQ} = \sum_{k=0}^{\infty} \frac{t^k}{k!} Q^k$ converge absolutamente para todo $t \ge 0$ e satisfaz:

- **Propriedade de semigrupo (Chapman–Kolmogorov):** $P(0) = I$ e $P(s + t) = P(s) P(t)$ para todos $s, t \ge 0$.
- **Equação Backward de Kolmogorov:** $P'(t) = Q P(t)$.
- **Equação Forward de Kolmogorov (Fokker–Planck discreta):** $P'(t) = P(t) Q$.
- **Derivada na origem:** $P'(0^+) = Q$, isto é, $p_{ij}(h) = \delta_{ij} + q_{ij} h + o(h)$ quando $h \to 0^+$.
- **Caracterização:** em espaço finito, $Q$ é matriz-$Q$ se e somente se $P(t) = e^{tQ}$ é matriz estocástica para todo $t \ge 0$.

Em espaços enumeráveis infinitos, a família mínima $P(t)$ ainda satisfaz as equações Backward e Forward (sob condições regulares / não-explosividade), porém $P(t)$ pode ser subestocástica ($\sum_j p_{ij}(t) < 1$) caso ocorra explosão.

## 3. Distribuição exponencial e relógios competitivos

A distribuição exponencial $T \sim \operatorname{Exp}(\lambda)$ ($\lambda > 0$, densidade $\lambda e^{-\lambda t}$ para $t \ge 0$, média $1/\lambda$) governa os tempos de permanência por ser a única distribuição contínua positiva com a **propriedade de perda de memória**:

$$\mathbb{P}(T > s + t \mid T > s) = \mathbb{P}(T > t), \qquad s, t \ge 0.$$

Dois resultados operacionais são centrais:

1. **Critério de explosão para somas de exponenciais independentes:** se $S_n \sim \operatorname{Exp}(\lambda_n)$ são independentes, então

$$\sum_{n=1}^{\infty} \frac{1}{\lambda_n} = \infty \implies \mathbb{P}\!\left(\sum_{n=1}^{\infty} S_n = \infty\right) = 1, \qquad \sum_{n=1}^{\infty} \frac{1}{\lambda_n} < \infty \implies \mathbb{P}\!\left(\sum_{n=1}^{\infty} S_n < \infty\right) = 1.$$

Em particular, se as taxas de saída são uniformemente limitadas ($\sup_i q_i < \infty$, incluindo todo espaço finito), o processo nunca explode.

2. **Competição de relógios exponenciais:** sejam $T_1, \dots, T_m$ (ou família enumerável com $q = \sum_k q_k < \infty$) variáveis independentes com $T_k \sim \operatorname{Exp}(q_k)$, e defina $T = \inf_k T_k$ e o índice vencedor $K$ tal que $T_K = T$. Então:
   - $T \sim \operatorname{Exp}(q)$;
   - $\mathbb{P}(K = k) = q_k / q$;
   - $T$ e $K$ são **independentes**.

## 4. Processo de Poisson

O **Processo de Poisson** de taxa $\lambda > 0$ é o processo de contagem $(N_t)_{t \ge 0}$ em $S = \mathbb{Z}_+$ com $N_0 = 0$ e matriz geradora $q_{i, i+1} = \lambda$, $q_{ii} = -\lambda$ (e demais entradas nulas). Como $\sup_i q_i = \lambda < \infty$, ele é não explosivo e satisfaz as propriedades fraca e forte de Markov.

### Três caracterizações equivalentes

Um processo contínuo à direita $(N_t)_{t \ge 0}$ com $N_0 = 0$ é um Processo de Poisson de taxa $\lambda$ se e somente se satisfaz qualquer uma das definições abaixo:

1. **Tempos entre chegadas:** $N_t$ só realiza saltos unitários $+1$ e os tempos entre saltos $S_1, S_2, \dots$ são i.i.d. com distribuição $\operatorname{Exp}(\lambda)$.
2. **Descrição infinitesimal:** $(N_t)$ tem incrementos independentes e, para $h \to 0^+$,
   $$\mathbb{P}(N_{t+h} - N_t = 1) = \lambda h + o(h), \qquad \mathbb{P}(N_{t+h} - N_t \ge 2) = o(h).$$
3. **Incrementos estacionários e lei de Poisson:** $(N_t)$ tem incrementos independentes e estacionários, e $N_{t+s} - N_s \sim \operatorname{Poisson}(\lambda t)$ para todos $s, t \ge 0$:
   $$\mathbb{P}(N_t = k) = e^{-\lambda t} \frac{(\lambda t)^k}{k!}, \qquad k \in \mathbb{Z}_+.$$

Processos de **nascimento puro** generalizam o Processo de Poisson permitindo taxas dependentes do estado $q_{i, i+1} = \lambda_i$; pelo critério de explosão, não explodem se e somente se $\sum_{i} \lambda_i^{-1} = \infty$ (por exemplo, o processo de Yule com $\lambda_i = \lambda i$ não explode porque a série harmônica diverge, mas $\lambda_i = \lambda i^2$ explode em tempo finito q.c.).

## 5. Construção e caracterizações de processos de Markov contínuos

Dada uma matriz geradora $Q$, define-se a **matriz da cadeia embutida** $\Pi = (\pi_{ij})$ por:

$$\pi_{ij} = \begin{cases} q_{ij} / q_i, & \text{se } q_i > 0 \text{ e } j \neq i, \\ 0, & \text{se } q_i > 0 \text{ e } j = i, \end{cases} \qquad \text{e, se } q_i = 0 \text{ (estado absorvente):} \quad \pi_{ii} = 1,\ \pi_{ij} = 0\ (j \neq i).$$

Existem duas construções probabilísticas equivalentes de um processo $\operatorname{Markov}(\mu, Q)$:

- **Construção A (cadeia embutida + tempos de permanência):** simula-se a cadeia discreta $(Y_n)_{n \ge 0} \sim \operatorname{Markov}(\mu, \Pi)$ e, condicionado à trajetória $(Y_n)$, sorteiam-se tempos de permanência independentes $S_n = T_n / q_{Y_{n-1}}$ onde $T_n \sim \operatorname{Exp}(1)$ i.i.d. (com $S_n = \infty$ se $q_{Y_{n-1}} = 0$).
- **Construção B (relógios exponenciais competitivos):** estando no estado $i$, acionam-se relógios independentes $T_{ij} \sim \operatorname{Exp}(q_{ij})$ para cada $j \neq i$; o processo permanece em $i$ pelo tempo $\inf_{j \neq i} T_{ij} \sim \operatorname{Exp}(q_i)$ e salta para o estado $j$ cujo relógio dispara primeiro (com probabilidade $q_{ij}/q_i = \pi_{ij}$).

### Propriedade forte de Markov e equivalência em espaço finito

Todo processo $\operatorname{Markov}(\mu, Q)$ satisfaz a **propriedade forte de Markov**: para qualquer tempo de parada $T$ (isto é, $\{T \le t\}$ determinado por $(X_s)_{0 \le s \le t}$), condicionado a $\{T < \infty, X_T = i\}$, o processo $(X_{T+t})_{t \ge 0}$ é $\operatorname{Markov}(\delta_i, Q)$ e independente do passado até $T$.

Quando $S$ é finito, as três descrições abaixo são equivalentes:

1. **Construção via cadeia embutida e permanências exponenciais** (Construção A/B);
2. **Descrição infinitesimal:** $\mathbb{P}(X_{t+h} = j \mid X_t = i, \mathcal{F}_t) = \delta_{ij} + q_{ij} h + o(h)$ uniformemente quando $h \to 0^+$;
3. **Semigrupo / Equações de Kolmogorov:** $(X_t)$ tem probabilidades de transição dadas por $P(t) = e^{tQ}$, única solução de $P'(t) = P(t)Q$ (e $P'(t) = QP(t)$) com $P(0) = I$.

## 6. Estrutura de classes, chegada e absorção

- **Classes de comunicação:** em tempo contínuo, $i \to j$ no processo $(X_t)$ coincide exatamente com a acessibilidade $i \to j$ na cadeia embutida $\Pi$, e equivale a $p_{ij}(t) > 0$ para **todo** $t > 0$ (ou para algum $t > 0$). Não existe barreira de paridade/periodicidade porque tempos exponenciais têm suporte positivo em todo $(0, \infty)$.
- **Probabilidades de absorção $h^A_i = \mathbb{P}_i(D^A < \infty)$:** sendo $D^A = \inf\{t \ge 0 : X_t \in A\}$, o vetor $h^A$ coincide com o da cadeia embutida $\Pi$ e é a **menor solução não negativa** de

$$h_i = 1 \quad (i \in A), \qquad \sum_{j \in S} q_{ij} h_j = 0 \quad (i \notin A).$$

- **Tempos esperados até absorção $k^A_i = \mathbb{E}_i[D^A]$:** o vetor $k^A$ é a **menor solução não negativa** de

$$k_i = 0 \quad (i \in A), \qquad -\sum_{j \in S} q_{ij} k_j = 1 \quad (i \notin A).$$

Dividindo a segunda equação por $q_i > 0$, obtém-se $k_i = \frac{1}{q_i} + \sum_{j \neq i} \pi_{ij} k_j$: o tempo esperado até $A$ é a soma do tempo médio de permanência $1/q_i$ no estado atual com a média ponderada dos tempos remanescentes após o salto.

## 7. Recorrência, transitoriedade e discretização ($h$-esqueleto)

Um estado $i$ é **recorrente** em tempo contínuo se $\mathbb{P}_i(\{t \ge 0 : X_t = i\} \text{ é ilimitado}) = 1$, e **transitório** se $\mathbb{P}_i(\{t \ge 0 : X_t = i\} \text{ é ilimitado}) = 0$.

Para $i$ não absorvente ($q_i > 0$), são equivalentes:

1. $i$ é recorrente para $(X_t)$;
2. $i$ é recorrente para a cadeia embutida $(Y_n)$ com matriz $\Pi$;
3. $\int_0^{\infty} p_{ii}(t)\,dt = \infty$;
4. Para qualquer passo $h > 0$, $i$ é recorrente para o **$h$-esqueleto discreto** $(X_{nh})_{n \ge 0}$ (cadeia discreta com matriz $P(h)$).

Assim como no caso discreto, recorrência e transitoriedade são propriedades de classe; toda classe recorrente é fechada, e toda classe finita e fechada é recorrente.

## 8. Distribuição invariante, convergência e teorema ergódico

### Medidas e distribuições invariantes

Uma medida não negativa $\lambda = (\lambda_i)_{i \in S}$ é **invariante** para $Q$ se satisfaz o sistema de **equações globais de balanço**:

$$\lambda Q = 0 \qquad \Longleftrightarrow \qquad \sum_{i \neq j} \lambda_i q_{ij} = \lambda_j q_j \quad \text{para todo } j \in S$$

(fluxo total de entrada em $j$ igual ao fluxo total de saída de $j$).

**Relação com a cadeia embutida e com $P(t)$:**

- $\lambda$ é medida invariante para $Q$ se e somente se $\mu_i = \lambda_i q_i$ é medida invariante para a cadeia embutida $\Pi$ ($\mu \Pi = \mu$). Note que a ponderação por $1/q_i$ compensa o tempo médio gasto em cada estado.
- Se $Q$ é não explosiva (ou em espaço finito), $\lambda Q = 0 \iff \lambda P(t) = \lambda$ para todo $t \ge 0$.
- **Recorrência positiva e tempo médio de retorno:** sendo $T_i = \inf\{t \ge J_1 : X_t = i\}$ o tempo de primeiro retorno a $i$ após o primeiro salto e $m_i = \mathbb{E}_i[T_i]$, uma cadeia irredutível não explosiva possui distribuição invariante $\lambda$ se e somente se é positivo recorrente ($m_i < \infty$). Nesse caso, $\lambda$ é única e satisfaz

$$\lambda_i = \frac{1}{q_i m_i} \qquad \text{para todo } i \in S.$$

- **Reversibilidade:** o balanceamento detalhado assume a forma $\lambda_i q_{ij} = \lambda_j q_{ji}$ para todos $i \neq j$, implicando automaticamente $\lambda Q = 0$.

### Convergência ao equilíbrio (ausência de periodicidade)

Diferentemente do tempo discreto, **não há obstáculo de periodicidade em tempo contínuo**: se $(X_t)$ é irredutível e não explosivo com distribuição invariante $\lambda$, então para todos $i, j \in S$,

$$\lim_{t \to \infty} p_{ij}(t) = \lambda_j = \frac{1}{q_j m_j}.$$

(A demonstração passa pela discretização em um $h$-esqueleto $(X_{nh})$, que herda $p_{ii}(h) > 0$ e portanto é automaticamente aperiódico.)

### Teorema Ergódico em tempo contínuo

Se $(X_t)$ é irredutível e positivo recorrente com distribuição invariante $\lambda$, então para toda função $f: S \to \mathbb{R}$ com $\sum_{i \in S} |f(i)| \lambda_i < \infty$ e qualquer distribuição inicial:

$$\frac{1}{t} \int_0^t f(X_u)\,du \xrightarrow{\text{q.c.}} \sum_{i \in S} f(i)\,\lambda_i \qquad (t \to \infty).$$

Em particular, a fração de tempo passada em cada estado $j$ converge q.c. para $\lambda_j$.

## Comparação direta: tempo discreto vs. tempo contínuo

| Propriedade | Tempo discreto $(\lambda, P)$ | Tempo contínuo $(\mu, Q)$ |
|---|---|---|
| Operador gerador | Matriz estocástica $P$ ($\sum_j p_{ij} = 1$) | Matriz-$Q$ ($\sum_j q_{ij} = 0$, $q_{ii} = -q_i$) |
| Evolução | $P^n$ | $P(t) = e^{tQ}$ ($P'(t) = P(t)Q = QP(t)$) |
| Permanência em $i$ | Geométrica | Exponencial $\operatorname{Exp}(q_i)$ |
| Explosão | Impossível | Possível se $\sum q_{Y_n}^{-1} < \infty$ |
| Probabilidade de chegada ($i \notin A$) | $(P - I) h = 0$ | $Q h = 0$ |
| Tempo médio até $A$ ($i \notin A$) | $(I - P) k = \mathbf{1}$ | $-Q k = \mathbf{1}$ |
| Distribuição invariante | $\pi P = \pi$ | $\lambda Q = 0$ |
| Fórmula de retorno | $\pi_i = 1 / m_i$ | $\lambda_i = 1 / (q_i m_i)$ |
| Critério de recorrência | $\sum_n p^{(n)}_{ii} = \infty$ | $\int_0^\infty p_{ii}(t)\,dt = \infty$ |
| Convergência ao equilíbrio | Requer aperiodicidade | Automática (sem periodicidade) |

## Aspectos computacionais

Para uma futura implementação em `engine/quantlab/` (ex.: `quantlab.stochastic.ctmc`), os pontos críticos são:

- **Validação de matriz-$Q$:** checar $q_{ij} \ge 0$ para $i \neq j$, $q_{ii} \le 0$ e $|\sum_j q_{ij}| \le \text{atol}$.
- **Cálculo de $P(t) = e^{tQ}$:** usar `scipy.linalg.expm` (aproximação de Padé com *scaling and squaring*), evitando diagonalização ingênua (que falha em matrizes defeituosas ou mal condicionadas) e integração explícita por Euler (que pode violar positividade quando $h \max_i q_i > 1$). Alternativamente, o método de **uniformização** (*Jensen's method*) escreve $P(t) = e^{-\gamma t} \sum_{k=0}^{\infty} \frac{(\gamma t)^k}{k!} (I + Q/\gamma)^k$ com $\gamma \ge \max_i q_i$, garantindo soma de termos estritamente não negativos sem cancelamento catastrófico.
- **Simulação exata de trajetórias:** a Construção A/B corresponde diretamente ao **algoritmo de Gillespie** (*Stochastic Simulation Algorithm*): sorteia-se $\Delta t \sim \operatorname{Exp}(q_i)$ e o próximo estado $j \neq i$ com probabilidade $q_{ij}/q_i$, sem erro de discretização temporal.
- **Distribuição invariante e absorção:** resolver $Q^\top \lambda^\top = 0$ substituindo uma linha por $\sum_i \lambda_i = 1$, e resolver $-Q_{T,T} k_T = \mathbf{1}$ por fatoração LU ou métodos esparsos.

## Limitações

- O formalismo acima trata espaço de estados **enumerável** com trajetórias constantes por partes; processos de difusão em espaço contínuo (Movimento Browniano, equações diferenciais estocásticas de Itô e Black–Scholes contínuo) exigem cálculo estocástico contínuo e geradores diferenciais de segunda ordem.
- Taxas constantes $Q$ implicam tempos de permanência exponenciais (sem memória); quando o tempo já transcorrido no estado altera a taxa de saída (envelhecimento ou memória de duração), são necessários processos semi-Markov ou taxas dependentes do tempo $Q(t)$ (cadeias não homogêneas).
- Em sistemas com múltiplas escalas de tempo (taxas $q_i$ variando por várias ordens de grandeza — rigidez / *stiffness*), o algoritmo de Gillespie executa muitos saltos em subestados rápidos e o cálculo numérico de $e^{tQ}$ requer atenção ao condicionamento.

## Referências

- R. A. Rosales. *Notas de aula em Processos Estocásticos*, cap. 2. DCM/FFCLRP–USP, 2026.
- J. R. Norris. *Markov Chains*, cap. 2–3. Cambridge University Press, 1997.
- G. R. Grimmett e D. R. Stirzacker. *Probability and Random Processes*. Oxford University Press, 3ª ed., 2001.
- C. Moler e C. Van Loan. *Nineteen Dubious Ways to Compute the Exponential of a Matrix, Twenty-Five Years Later*. SIAM Review, 45(1), 3–49, 2003.

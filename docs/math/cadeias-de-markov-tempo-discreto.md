# Cadeias de Markov em tempo discreto

Status: **fundamentação teórica** (base matemática de apoio para a Fase 6 — modelos estocásticos e mudanças de regime). Ainda não há módulo dedicado implementado em `engine/quantlab/`; quando existir, esta página passará a apontar para o código e os testes correspondentes.

## Escopo e conexão com o QuantLab

Cadeias de Markov em tempo discreto modelam sistemas estocásticos cujo estado futuro depende do histórico apenas através do estado presente. Em finanças quantitativas e sistemas dinâmicos, servem de base para modelos de mudança de regime (*regime switching*), matrizes de migração de crédito, passeios aleatórios de preços, processos de ramificação e aproximações discretas de dinâmicas contínuas.

Documentos relacionados:

- [Fundamentos de probabilidade, convergência, ergodicidade e grandes desvios](fundamentos-de-probabilidade.md)
- [Esperança condicional, martingais e apreçamento em tempo discreto](esperanca-condicional-e-martingais.md)
- [Processos de Markov em tempo contínuo](processos-de-markov-tempo-continuo.md)

## Notação

| Símbolo | Significado |
|---|---|
| $S$ | espaço de estados enumerável (finito ou infinito enumerável) |
| $\lambda = (\lambda_i)_{i \in S}$ | distribuição inicial ($\lambda_i \ge 0$, $\sum_{i \in S} \lambda_i = 1$) |
| $P = (p_{ij})_{i, j \in S}$ | matriz estocástica de transição ($p_{ij} \ge 0$, $\sum_{j \in S} p_{ij} = 1$) |
| $p^{(n)}_{ij} = (P^n)_{ij}$ | probabilidade de transição em $n$ passos de $i$ para $j$ |
| $\mathbb{P}_i(\cdot)$, $\mathbb{E}_i[\cdot]$ | probabilidade e esperança condicional ao início em $X_0 = i$ |
| $H_A$, $T_A$ | tempo de primeira chegada ($\inf\{n \ge 0 : X_n \in A\}$) e primeiro retorno ($\inf\{n \ge 1 : X_n \in A\}$) |
| $h^A_i$, $k^A_i$ | probabilidade $\mathbb{P}_i(H_A < \infty)$ e tempo esperado $\mathbb{E}_i[H_A]$ de chegada a $A$ |
| $f_i$, $m_i$ | probabilidade de retorno $\mathbb{P}_i(T_i < \infty)$ e tempo médio de retorno $\mathbb{E}_i[T_i]$ |
| $V_i$ | número total de visitas ao estado $i$, $V_i = \sum_{n=0}^{\infty} \mathbf{1}_{\{X_n = i\}}$ |
| $\pi$ | distribuição invariante ($\pi P = \pi$, $\pi_i \ge 0$, $\sum_i \pi_i = 1$) |
| $d_i$ | período do estado $i$, $\operatorname{mdc}\{n \ge 1 : p^{(n)}_{ii} > 0\}$ |

## 1. Definição, propriedade de Markov e dinâmica em $n$ passos

Um processo estocástico $(X_n)_{n \ge 0}$ com valores em $S$ é uma **cadeia de Markov homogênea** com distribuição inicial $\lambda$ e matriz de transição $P$ — denotada $\operatorname{Markov}(\lambda, P)$ — se:

1. $\mathbb{P}(X_0 = i_0) = \lambda_{i_0}$ para todo $i_0 \in S$;
2. Para todo $n \ge 0$ e quaisquer estados $i_0, \dots, i_{n+1} \in S$ com $\mathbb{P}(X_0 = i_0, \dots, X_n = i_n) > 0$,

$$\mathbb{P}(X_{n+1} = i_{n+1} \mid X_0 = i_0, \dots, X_n = i_n) = \mathbb{P}(X_{n+1} = i_{n+1} \mid X_n = i_n) = p_{i_n i_{n+1}}.$$

A matriz $P$ pode ser representada por um grafo direcionado ponderado (rede de transição) com vértices em $S$ e arestas $i \to j$ de peso $p_{ij} > 0$.

### Propriedades fundamentais

- **Probabilidade de trajetórias:** $(X_n)_{n \ge 0}$ é $\operatorname{Markov}(\lambda, P)$ se e somente se, para todo $n \ge 0$ e toda sequência $(i_0, \dots, i_n) \in S^{n+1}$,

$$\mathbb{P}(X_0 = i_0, X_1 = i_1, \dots, X_n = i_n) = \lambda_{i_0} p_{i_0 i_1} \cdots p_{i_{n-1} i_n}.$$

- **Propriedade fraca de Markov:** condicionado a $X_m = i$, o processo futuro $(X_{m+n})_{n \ge 0}$ é $\operatorname{Markov}(\delta_i, P)$ e é independente do passado $(X_0, \dots, X_m)$.
- **Evolução em $n$ passos e Chapman–Kolmogorov:** tratando distribuições como vetores-linha, a distribuição em $n$ passos é $\mathbb{P}(X_n = j) = (\lambda P^n)_j$, e as probabilidades de transição satisfazem

$$p^{(m+n)}_{ij} = \sum_{k \in S} p^{(m)}_{ik} p^{(n)}_{kj} \qquad \Longleftrightarrow \qquad P^{m+n} = P^m P^n.$$

### Exemplo analítico: cadeia de 2 estados

Para $S = \{0, 1\}$ e

$$P = \begin{pmatrix} 1 - a & a \\ b & 1 - b \end{pmatrix}, \qquad a, b \in [0, 1],\ a + b > 0,$$

os autovalores de $P$ são $\mu_1 = 1$ e $\mu_2 = 1 - a - b$, resultando na forma fechada

$$P^n = \frac{1}{a + b} \begin{pmatrix} b & a \\ b & a \end{pmatrix} + \frac{(1 - a - b)^n}{a + b} \begin{pmatrix} a & -a \\ -b & b \end{pmatrix}.$$

Se $0 < a + b < 2$, então $|1 - a - b| < 1$ e $P^n$ converge exponencialmente para a matriz de linhas idênticas iguais à distribuição invariante $\pi = \left(\frac{b}{a+b}, \frac{a}{a+b}\right)$. Se $a = b = 1$, tem-se $\mu_2 = -1$ (cadeia periódica de período 2 que oscila sem convergir).

### Processos derivados: quando a propriedade de Markov se preserva

Nem toda função $Y_n = f(X_n)$ de uma cadeia de Markov continua sendo Markov:

- **Preservam a propriedade de Markov:**
  - Pares consecutivos $Y_n = (X_{n-1}, X_n)$ (memória finita de ordem $k$ reduz-se a ordem 1 ampliando o espaço de estados para $S^k$);
  - Subsequências em passos regulares ($k$-esqueleto) $Y_n = X_{kn}$, com matriz $P^k$;
  - Somas parciais ou máximos acumulados de variáveis i.i.d. (pois o incremento depende apenas de uma inovação independente);
  - Agregação de estados (*lumpability*): se uma partição $\{B_1, B_2, \dots\}$ de $S$ satisfaz $\sum_{j \in B_v} p_{ij}$ constante para todo $i \in B_u$, o processo agregado nos blocos é Markov.
- **Refutação:** para mostrar que $Y_n = f(X_n)$ não é Markov, basta exibir um contraexemplo concreto onde $\mathbb{P}(Y_{n+1} = y \mid Y_n = y_n, Y_{n-1} = y_{n-1})$ varia com $y_{n-1}$ (o que ocorre quando o bloco agregado mistura estados com probabilidades de saída distintas).

## 2. Classes de comunicação

- Um estado $j$ é **acessível** a partir de $i$ ($i \to j$) se existe $n \ge 0$ tal que $p^{(n)}_{ij} > 0$.
- Os estados $i$ e $j$ **comunicam-se** ($i \leftrightarrow j$) se $i \to j$ e $j \to i$. A comunicação é uma relação de equivalência que particiona $S$ em **classes de comunicação** disjuntas.
- Uma classe $C$ é **fechada** se não há saída dela: $i \in C$ e $i \to j \implies j \in C$. Caso contrário, é **aberta**.
- Um estado $i$ é **absorvente** se $\{i\}$ é uma classe fechada ($p_{ii} = 1$).
- A cadeia é **irredutível** se possui uma única classe de comunicação ($i \leftrightarrow j$ para todos $i, j \in S$).

## 3. Primeira chegada, absorção e funções geradoras

Para $A \subseteq S$, definem-se o **tempo de primeira chegada** $H_A = \inf\{n \ge 0 : X_n \in A\}$ e o **tempo de primeiro retorno** $T_A = \inf\{n \ge 1 : X_n \in A\}$ (com $\inf \emptyset = \infty$).

### Probabilidades e tempos esperados de chegada

Pela análise do primeiro passo:

1. **Probabilidades de chegada $h^A_i = \mathbb{P}_i(H_A < \infty)$:** o vetor $h^A = (h^A_i)_{i \in S}$ é a **menor solução não negativa** do sistema

$$h_i = 1 \quad (i \in A), \qquad h_i = \sum_{j \in S} p_{ij} h_j \quad (i \notin A).$$

2. **Tempos esperados de chegada $k^A_i = \mathbb{E}_i[H_A]$:** o vetor $k^A = (k^A_i)_{i \in S}$ (com valores em $[0, \infty]$) é a **menor solução não negativa** do sistema

$$k_i = 0 \quad (i \in A), \qquad k_i = 1 + \sum_{j \notin A} p_{ij} k_j \quad (i \notin A).$$

Em cadeias finitas onde $A$ é acessível a partir de todos os estados transitórios $T = S \setminus A$, escrevendo a submatriz de transição entre estados transitórios como $Q = P_{T,T}$, o raio espectral $\rho(Q) < 1$ garante que $I - Q$ é invertível. A matriz $N = (I - Q)^{-1} = \sum_{n=0}^{\infty} Q^n$ é a **matriz fundamental** (cuja entrada $N_{ij}$ é o número esperado de visitas a $j$ antes da absorção partindo de $i$), e o vetor de tempos médios até absorção é

$$k_T = (I - Q)^{-1} \mathbf{1}.$$

### Ruína do jogador e minimalidade

No passeio aleatório em $\{0, 1, \dots, a\}$ com $0$ e $a$ absorventes e passos $+1$ (prob. $p \in (0, 1)$) ou $-1$ (prob. $q = 1 - p$), a equação de primeiro passo $h_i = p h_{i+1} + q h_{i-1}$ tem equação característica $p \alpha^2 - \alpha + q = 0$, com raízes $1$ e $q/p$:

- **Probabilidade de atingir $a$ antes de $0$ (partindo de $i$):**

$$h^{\{a\}}_i = \begin{cases} \dfrac{1 - (q/p)^i}{1 - (q/p)^a}, & p \neq \dfrac{1}{2}, \\[8pt] \dfrac{i}{a}, & p = \dfrac{1}{2}. \end{cases}$$

- **Duração esperada até absorção em $\{0, a\}$:**

$$k^{\{0, a\}}_i = \begin{cases} \dfrac{i}{q - p} - \dfrac{a}{q - p}\dfrac{1 - (q/p)^i}{1 - (q/p)^a}, & p \neq \dfrac{1}{2}, \\[8pt] i(a - i), & p = \dfrac{1}{2}. \end{cases}$$

Em espaço infinito ($\mathbb{Z}_+$ com absorção em $0$), o sistema $h_i = p h_{i+1} + q h_{i-1}$ com $h_0 = 1$ admite uma família inteira de soluções $h_i = 1 + c((q/p)^i - 1)$ para $p > q$; a **condição de minimalidade não negativa** seleciona a única solução válida: $h^{\{0\}}_i = (q/p)^i$ quando $p > q$ e $h^{\{0\}}_i = 1$ quando $p \le q$.

### Cadeia de nascimento e morte em $\mathbb{Z}_+$

Com $0$ absorvente e, para $i \ge 1$, probabilidades $p_i > 0$ de subir ($i \to i + 1$) e $q_i > 0$ de descer ($i \to i - 1$), definindo $\gamma_0 = 1$ e $\gamma_i = \prod_{k=1}^{i} \frac{q_k}{p_k}$:

- Se $\sum_{i=0}^{\infty} \gamma_i = \infty$, a absorção em $0$ ocorre com probabilidade $1$ ($h^{\{0\}}_i = 1$ para todo $i$).
- Se $\sum_{i=0}^{\infty} \gamma_i < \infty$, então $h^{\{0\}}_i = \dfrac{\sum_{k=i}^{\infty} \gamma_k}{\sum_{k=0}^{\infty} \gamma_k} < 1$ para todo $i \ge 1$.

### Método de funções geradoras

Para $|z| < 1$, definem-se $G_{ij}(z) = \sum_{n=0}^{\infty} p^{(n)}_{ij} z^n$ e a função geradora do primeiro retorno $H_i(z) = \sum_{n=1}^{\infty} \mathbb{P}_i(T_i = n) z^n$. A decomposição pelo tempo do primeiro retorno gera a identidade fundamental

$$G_{ii}(z) = 1 + H_i(z)\,G_{ii}(z) \quad \Longrightarrow \quad G_{ii}(z) = \frac{1}{1 - H_i(z)},$$

de onde se obtêm $f_i = H_i(1^-)$ e o tempo médio de retorno $m_i = H'_i(1^-)$.

## 4. Propriedade forte de Markov

Uma variável $T: \Omega \to \mathbb{Z}_+ \cup \{\infty\}$ é um **tempo de parada** se o evento $\{T = m\}$ depende apenas de $(X_0, \dots, X_m)$ para todo $m \ge 0$. Tempos de primeira chegada $H_A$, primeiro retorno $T_A$ e $k$-ésima visita são tempos de parada; a **última visita** $U_A = \sup\{n \ge 0 : X_n \in A\}$ **não** é tempo de parada, pois exige conhecer toda a trajetória futura.

**Teorema (Propriedade Forte de Markov):** se $(X_n)$ é $\operatorname{Markov}(\lambda, P)$ e $T$ é tempo de parada, então, condicionado ao evento $\{T < \infty, X_T = i\}$, o processo pós-$T$ definido por $(X_{T+n})_{n \ge 0}$ é $\operatorname{Markov}(\delta_i, P)$ e independente de $(X_0, \dots, X_T)$.

**Consequências estruturais:**

- **Excursões i.i.d.:** os intervalos entre retornos sucessivos a um estado $i$ são independentes e identicamente distribuídos.
- **Distribuição geométrica das visitas:** $\mathbb{P}_i(V_i > k) = f_i^k$ para todo $k \ge 0$ (isto é, partindo de $i$, $V_i \sim \operatorname{Geométrica}(1 - f_i)$ em $\{1, 2, \dots\}$ quando $f_i < 1$).
- **Passeios *skip-free* (saltos unitários à esquerda):** em passeios que só descem de 1 em 1, atingir $0$ partindo de $k$ exige primeiro atingir $k-1$, depois $k-2$, etc., donde $h^{\{0\}}_k = \left(h^{\{0\}}_1\right)^k$.
- **Desigualdade de transitividade:** $\mathbb{P}_i(H_k < \infty) \ge \mathbb{P}_i(H_j < \infty)\,\mathbb{P}_j(H_k < \infty)$.

## 5. Recorrência, transitoriedade e passeios aleatórios

Um estado $i \in S$ é **recorrente** se $f_i = \mathbb{P}_i(T_i < \infty) = 1$, e **transitório** se $f_i < 1$. A **matriz de potencial** é $G_{ij} = \mathbb{E}_i[V_j] = \sum_{n=0}^{\infty} p^{(n)}_{ij}$.

### Critérios e propriedades de classe

1. **Dicotomia recorrência vs. transitoriedade:**

$$i \text{ é recorrente} \iff \mathbb{P}_i(V_i = \infty) = 1 \iff \sum_{n=0}^{\infty} p^{(n)}_{ii} = \infty.$$
$$i \text{ é transitório} \iff \mathbb{P}_i(V_i = \infty) = 0 \iff \sum_{n=0}^{\infty} p^{(n)}_{ii} = \frac{1}{1 - f_i} < \infty.$$

2. **Solidariedade de classe:** se $i \leftrightarrow j$, então $i$ é recorrente se e somente se $j$ é recorrente (e o mesmo vale para recorrência positiva, recorrência nula e periodicidade).
3. **Topologia das classes:**
   - Toda classe recorrente é **fechada** (logo toda classe aberta é transitória);
   - Toda classe **finita e fechada** é recorrente (em particular, toda cadeia finita possui ao menos um estado recorrente).
   - Se $P$ é irredutível e recorrente, então $\mathbb{P}_j(T_i < \infty) = 1$ para todos $i, j \in S$.
4. **Recorrência positiva vs. nula:** um estado recorrente $i$ é **positivo recorrente** se $m_i = \mathbb{E}_i[T_i] < \infty$, e **nulo recorrente** se $m_i = \infty$. Em espaços finitos, não existe recorrência nula.

### Passeio aleatório simples em $\mathbb{Z}^d$ (Teorema de Pólya)

- **Em $\mathbb{Z}$:** com passos $+1$ (prob. $p$) e $-1$ (prob. $q = 1 - p$), tem-se $p^{(2n)}_{00} = \binom{2n}{n} p^n q^n \sim \frac{(4pq)^n}{\sqrt{\pi n}}$ (pela fórmula de Stirling).
  - Para $p = 1/2$, $4pq = 1$ e $\sum p^{(2n)}_{00} = \infty$: o passeio é **recorrente nulo** ($f_0 = 1$, $m_0 = \infty$).
  - Para $p \neq 1/2$, $4pq < 1$ e a série converge: o passeio é **transitório**, com $f_0 = 1 - |p - q|$.
- **Em $\mathbb{Z}^2$ (simétrico):** projetando em eixos rotacionados de $45^\circ$ (ou pela identidade de Vandermonde), as duas coordenadas tornam-se passeios simétricos 1D independentes, donde $p^{(2n)}_{00} = \left[\binom{2n}{n} 2^{-2n}\right]^2 \sim \frac{1}{\pi n}$. A série diverge: o passeio em $\mathbb{Z}^2$ é **recorrente nulo**.
- **Em $\mathbb{Z}^d$ ($d \ge 3$, simétrico):** $p^{(2n)}_{00} = O(n^{-d/2})$, cuja série converge. Para todo $d \ge 3$, o passeio aleatório simples simétrico é **transitório**.

## 6. Medidas e distribuições invariantes

Uma medida $\mu = (\mu_i)_{i \in S}$ com $\mu_i \ge 0$ (não identicamente nula) é **invariante** para $P$ se $\mu P = \mu$, isto é, $\sum_{i \in S} \mu_i p_{ij} = \mu_j$ para todo $j \in S$. Se além disso $\sum_{i \in S} \mu_i = 1$, $\mu$ é uma **distribuição invariante** (ou estacionária), geralmente denotada por $\pi$.

- **Estacionariedade:** se $X_0 \sim \pi$ e $\pi P = \pi$, então $X_n \sim \pi$ para todo $n \ge 0$.
- **Construção via excursões:** para um estado recorrente $k$, defina o número esperado de visitas a $i$ entre dois retornos sucessivos a $k$:

$$\gamma^k_i = \mathbb{E}_k\!\left[\sum_{n=0}^{T_k - 1} \mathbf{1}_{\{X_n = i\}}\right].$$

Se $P$ é irredutível e recorrente, $\gamma^k$ é uma medida invariante estritamente positiva e finita em cada estado ($0 < \gamma^k_i < \infty$), e toda medida invariante é múltipla escalar de $\gamma^k$ (**unicidade a menos de constante**). Como $\sum_{i \in S} \gamma^k_i = \mathbb{E}_k[T_k] = m_k$, segue:

- **Teorema de existência e Lema de Kač:** uma cadeia irredutível possui distribuição invariante $\pi$ se e somente se é **positivo recorrente**; nesse caso, $\pi$ é única e satisfaz

$$\pi_i = \frac{1}{m_i} \qquad \text{para todo } i \in S.$$

### Distinção entre existência, unicidade e convergência

| Cenário | Existe $\pi$? | É única? | $p^{(n)}_{ij} \to \pi_j$? |
|---|---|---|---|
| Irredutível, positivo recorrente e aperiódica (ergódica) | Sim | Sim | Sim |
| Irredutível, positivo recorrente e periódica ($d > 1$) | Sim | Sim | Não (oscila em subcadeias de passo $d$) |
| Finita com múltiplas classes fechadas | Sim | Não (combinações convexas) | Depende do estado inicial |
| Irredutível e nulo recorrente (ex.: PAS simétrico em $\mathbb{Z}$ ou $\mathbb{Z}^2$) | Não (só medida infinita $\gamma_i = 1$) | — | $p^{(n)}_{ij} \to 0$ |
| Irredutível e transitória (ex.: PAS em $\mathbb{Z}^3$ ou $p \neq q$ em $\mathbb{Z}$) | Não (pode haver medidas infinitas, sem normalização) | — | $p^{(n)}_{ij} \to 0$ |

## 7. Periodicidade, convergência ao equilíbrio, reversibilidade e teorema ergódico

### Periodicidade e convergência

O **período** de um estado $i$ é $d_i = \operatorname{mdc}\{n \ge 1 : p^{(n)}_{ii} > 0\}$. Estados na mesma classe de comunicação têm o mesmo período. Um estado é **aperiódico** se $d_i = 1$ (condição suficiente: $p_{ii} > 0$); nesse caso, existe $n_0$ tal que $p^{(n)}_{ii} > 0$ para todo $n \ge n_0$.

Uma cadeia irredutível de período $d$ particiona $S$ em $d$ classes cíclicas $C_0, C_1, \dots, C_{d-1}$ tais que toda transição a partir de $C_r$ vai com probabilidade $1$ para $C_{(r+1) \bmod d}$.

- **Teorema de Convergência ao Equilíbrio (prova via acoplamento de Döblin):** se $P$ é irredutível, aperiódica e possui distribuição invariante $\pi$ (cadeia **ergódica**), então para quaisquer distribuição inicial $\lambda$ e estados $i, j \in S$:

$$\lim_{n\to\infty} p^{(n)}_{ij} = \pi_j = \frac{1}{m_j}, \qquad \lim_{n\to\infty} \mathbb{P}(X_n = j) = \pi_j.$$

- **Convergência no caso periódico:** para cadeia irredutível de período $d$, se $i \in C_u$ e $j \in C_v$ com $r \equiv v - u \pmod d$, então $\lim_{n\to\infty} p^{(nd + r)}_{ij} = d / m_j$ (e zero nos demais restos).

### Reversibilidade e balanceamento detalhado

Uma cadeia $\operatorname{Markov}(\pi, P)$ com $\pi$ invariante é **reversível** se, para todo $N \ge 1$, o processo reverso no tempo $Y_n = X_{N-n}$ ($0 \le n \le N$) tem a mesma lei de $(X_n)_{0 \le n \le N}$. Em geral, o processo reverso é $\operatorname{Markov}(\pi, \hat{P})$ com $\pi_j \hat{p}_{ji} = \pi_i p_{ij}$. Logo, reversibilidade equivale às **equações de balanceamento detalhado**:

$$\pi_i p_{ij} = \pi_j p_{ji} \qquad \text{para todos } i, j \in S.$$

Toda distribuição $\pi$ que satisfaz o balanceamento detalhado é automaticamente invariante ($\sum_i \pi_i p_{ij} = \sum_i \pi_j p_{ji} = \pi_j$). Em cadeias de nascimento e morte, o balanceamento detalhado $\pi_i p_i = \pi_{i+1} q_{i+1}$ fornece $\pi$ diretamente por produto telescópico.

### Teorema Ergódico para cadeias de Markov

Seja $V_i(n) = \sum_{k=0}^{n-1} \mathbf{1}_{\{X_k = i\}}$ o número de visitas a $i$ antes do passo $n$. Se $P$ é irredutível:

$$\frac{V_i(n)}{n} \xrightarrow{\text{q.c.}} \frac{1}{m_i}$$

(sem exigir aperiodicidade!). Além disso, se $P$ é positivo recorrente com distribuição invariante $\pi$ e $f: S \to \mathbb{R}$ satisfaz $\sum_{i \in S} |f(i)| \pi_i < \infty$, então

$$\frac{1}{n} \sum_{k=0}^{n-1} f(X_k) \xrightarrow{\text{q.c.}} \sum_{i \in S} f(i)\,\pi_i.$$

## 8. Processos de ramificação via função geradora

No processo de Galton–Watson $Z_{n+1} = \sum_{j=1}^{Z_n} \xi_{n,j}$ com $Z_0 = 1$ e lei de descendência com função geradora de probabilidades $H(z) = \mathbb{E}[z^\xi] = \sum_{k=0}^{\infty} \mathbb{P}(\xi = k) z^k$ ($z \in [0, 1]$):

- A função geradora de $Z_n$ é a $n$-ésima composição iterada $H_n(z) = H^{\circ n}(z) = H(H_{n-1}(z))$ (sistema dinâmico discreto em $[0, 1]$, análogo em espírito ao estudo de pontos fixos do mapa logístico em `quantlab.dynamics`).
- A probabilidade de extinção $q = \mathbb{P}(\exists n : Z_n = 0) = \lim_{n\to\infty} H_n(0)$ é a **menor raiz não negativa** de $z = H(z)$ em $[0, 1]$.
- Se $\mathbb{P}(\xi = 1) < 1$, então $q = 1 \iff \mu = \mathbb{E}[\xi] = H'(1^-) \le 1$, e $q < 1 \iff \mu > 1$.

## 9. Ferramenta auxiliar: recorrências lineares homogêneas

Problemas de absorção e potências de matrizes frequentemente reduzem-se a relações de recorrência lineares homogêneas de ordem $k$:

$$x_{n+k} = a_1 x_{n+k-1} + a_2 x_{n+k-2} + \dots + a_k x_n.$$

O conjunto de soluções forma um espaço vetorial $\mathcal{H} \cong \mathbb{R}^k$. Reescrevendo no vetor de estado $v_n = (x_n, x_{n+1}, \dots, x_{n+k-1})^\top$, obtém-se $v_{n+1} = A v_n$, onde $A$ é a **matriz companheira** cujo polinômio característico é $p(\alpha) = \alpha^k - a_1 \alpha^{k-1} - \dots - a_k$. Quando as raízes $\alpha_1, \dots, \alpha_k$ são distintas, as sequências $(\alpha_j^n)$ formam base de $\mathcal{H}$ e os coeficientes a partir das condições iniciais $(x_0, \dots, x_{k-1})$ são obtidos invertendo a **matriz de Vandermonde** $V(\alpha_1, \dots, \alpha_k)$ (cuja inversa explícita relaciona-se aos polinômios interpoladores de Lagrange). Raízes de multiplicidade $m$ contribuem com termos $n^r \alpha^n$ ($0 \le r < m$).

## Consulta rápida

| Tarefa | Equação / Critério |
|---|---|
| Verificar matriz estocástica | $p_{ij} \ge 0$ e $\sum_j p_{ij} = 1$ para todo $i$ |
| Distribuição após $n$ passos | $\lambda^{(n)} = \lambda P^n$ |
| Probabilidade de chegada a $A$ | Menor solução $\ge 0$ de $h_i = \sum_j p_{ij} h_j$ ($i \notin A$), $h_i = 1$ ($i \in A$) |
| Tempo médio até $A$ | Menor solução $\ge 0$ de $k_i = 1 + \sum_{j \notin A} p_{ij} k_j$ ($i \notin A$), $k_i = 0$ ($i \in A$); finito: $k_T = (I - Q)^{-1}\mathbf{1}$ |
| Recorrência | $f_i = 1 \iff \sum_{n=0}^\infty p^{(n)}_{ii} = \infty$ |
| Distribuição invariante | $\pi P = \pi$, $\pi \ge 0$, $\sum_i \pi_i = 1$ (ou balanceamento detalhado $\pi_i p_{ij} = \pi_j p_{ji}$) |
| Tempo médio de retorno | $m_i = 1 / \pi_i$ (irredutível e positivo recorrente) |
| Convergência $p^{(n)}_{ij} \to \pi_j$ | Irredutível + positivo recorrente + aperiódica |

## Aspectos computacionais

Para uma futura implementação em `engine/quantlab/` (ex.: `quantlab.stochastic.markov`), os principais cuidados numéricos são:

- **Validação de domínio:** verificar não negatividade ($p_{ij} \ge 0$) e normalização de linhas ($|\sum_j p_{ij} - 1| \le \text{atol}$), rejeitando `NaN`/`inf` e matrizes não quadradas.
- **Sistemas lineares vs. inversão explícita:** calcular tempos de absorção resolvendo $(I - Q) k_T = \mathbf{1}$ com `numpy.linalg.solve` (decomposição LU) em vez de inverter $I - Q$ explicitamente; quando $P$ é grande e esparsa, preferir solucionadores esparsos (`scipy.sparse.linalg`).
- **Distribuição invariante:** resolver $(P^\top - I)\pi^\top = 0$ substituindo uma equação pela restrição de normalização $\sum_i \pi_i = 1$, ou extrair o autovetor esquerdo associado a $\mu = 1$ (verificando multiplicidade 1 para confirmar unicidade). O método da potência $\lambda^{(n+1)} = \lambda^{(n)} P$ falha em convergir em cadeias periódicas e converge lentamente quando o segundo maior autovalor em módulo $|\mu_2|$ está próximo de $1$ (lacuna espectral $1 - |\mu_2|$ pequena).
- **Decomposição em classes:** identificar classes de comunicação como componentes fortemente conexas (algoritmo de Tarjan ou Kosaraju em tempo $O(|S| + |E|)$) e testar fechamento verificando se há arestas saindo de cada componente.

## Limitações

- A hipótese de homogeneidade temporal assume matriz $P$ constante ao longo do tempo; em mercados financeiros reais, probabilidades de transição entre regimes frequentemente dependem de variáveis exógenas ou variam ao longo do ciclo econômico.
- Em modelos observáveis de mercado, os regimes raramente são observados diretamente, exigindo extensões como Modelos Ocultos de Markov (*Hidden Markov Models* — HMM) e algoritmos de filtragem (Baum–Welch / Viterbi), ainda fora deste documento.
- Cadeias com espaço de estados infinito precisam ser truncadas para cálculo numérico, o que pode alterar artificialmente recorrência, absorção e existência de distribuição invariante se a fronteira de truncamento não for analisada com cuidado.

## Referências

- R. A. Rosales. *Notas de aula em Processos Estocásticos*, cap. 1 e Apêndice A. DCM/FFCLRP–USP, 2026.
- J. R. Norris. *Markov Chains*. Cambridge University Press, 1997.
- G. R. Grimmett e D. R. Stirzacker. *Probability and Random Processes*. Oxford University Press, 3ª ed., 2001.
- Material de estudo em cadeias de Markov (módulos M1–M6 e verificação numérica em `site/`).

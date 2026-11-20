# Fundamentos de probabilidade, convergência, ergodicidade e grandes desvios

Status: **fundamentação teórica** (base matemática de apoio para a Fase 6 — modelos estocásticos — e para os módulos estatísticos do motor). Ainda não há módulo dedicado implementado em `engine/quantlab/`; quando existir, esta página passará a apontar para o código e os testes correspondentes.

## Escopo e conexão com o QuantLab

A modelagem de finanças quantitativas e de sistemas dinâmicos aleatórios apoia-se na formulação axiomática da probabilidade pela teoria da medida. Este documento consolida os fundamentos que sustentam tanto a estatística de séries financeiras (LGN, TLC, caudas e grandes desvios) quanto os modelos de processos estocásticos (esperança condicional, martingais, cadeias de Markov e teoria ergódica).

Documentos complementares desta trilha:

- [Esperança condicional, martingais e apreçamento em tempo discreto](esperanca-condicional-e-martingais.md)
- [Cadeias de Markov em tempo discreto](cadeias-de-markov-tempo-discreto.md)
- [Processos de Markov em tempo contínuo](processos-de-markov-tempo-continuo.md)

## Notação

| Símbolo | Significado |
|---|---|
| $(\Omega, \mathcal{F}, \mathbb{P})$ | espaço de probabilidade (espaço amostral, $\sigma$-álgebra de eventos e medida de probabilidade) |
| $\mathcal{B}(\mathbb{R}^d)$ | $\sigma$-álgebra de Borel em $\mathbb{R}^d$ |
| $X, Y$ | variáveis aleatórias reais (funções mensuráveis $\Omega \to \mathbb{R}$) |
| $F_X(x) = \mathbb{P}(X \le x)$ | função de distribuição acumulada (FDA) |
| $\mathbb{E}[X]$, $\operatorname{Var}(X)$, $\operatorname{Cov}(X, Y)$ | esperança matemática, variância e covariância |
| $\mathcal{L}^p(\Omega, \mathcal{F}, \mathbb{P})$ | espaço das variáveis aleatórias com $\lVert X \rVert_p = (\mathbb{E}[|X|^p])^{1/p} < \infty$ |
| $\mathbf{1}_A$ | função indicadora do evento $A$ |
| $M_X(t)$, $\varphi_X(t)$ | função geradora de momentos e função característica |
| $\xrightarrow{\text{q.c.}}$, $\xrightarrow{\mathbb{P}}$, $\xrightarrow{\mathcal{L}^p}$, $\xrightarrow{d}$ | convergência quase certa, em probabilidade, em $\mathcal{L}^p$ e em distribuição |

## 1. Espaços de probabilidade e teoria da medida

Um **espaço de probabilidade** é uma terna $(\Omega, \mathcal{F}, \mathbb{P})$ satisfazendo os axiomas de Kolmogorov:

1. $\mathcal{F}$ é uma $\sigma$-álgebra de subconjuntos de $\Omega$ (contém $\Omega$, é fechada por complementos e por uniões enumeráveis).
2. $\mathbb{P}: \mathcal{F} \to [0, 1]$ é uma medida normalizada ($\mathbb{P}(\Omega) = 1$, $\mathbb{P}(\emptyset) = 0$) e $\sigma$-aditiva: para eventos disjuntos dois a dois $(A_n)_{n \ge 1}$,

$$\mathbb{P}\!\left(\bigcup_{n=1}^{\infty} A_n\right) = \sum_{n=1}^{\infty} \mathbb{P}(A_n).$$

Da $\sigma$-aditividade seguem a continuidade da probabilidade em sequências monótonas ($A_n \uparrow A \implies \mathbb{P}(A_n) \uparrow \mathbb{P}(A)$; $A_n \downarrow A \implies \mathbb{P}(A_n) \downarrow \mathbb{P}(A)$) e a subaditividade enumerável.

### Construção e unicidade de medidas

- **Teorema de extensão de Carathéodory:** toda medida $\sigma$-finita definida em uma álgebra de conjuntos estende-se de forma única para a $\sigma$-álgebra gerada. É o mecanismo formal que constrói a medida de Lebesgue em $\mathcal{B}(\mathbb{R})$ e as medidas de probabilidade a partir de funções de distribuição.
- **Teorema $\pi$-$\lambda$ de Dynkin:** se um $\pi$-sistema $\mathcal{P}$ (fechado por interseções finitas) está contido em um $\lambda$-sistema $\mathcal{L}$ (contém $\Omega$, fechado por diferenças próprias e uniões crescentes), então $\sigma(\mathcal{P}) \subseteq \mathcal{L}$. Como corolário, duas medidas de probabilidade que coincidem em um $\pi$-sistema coincidem em toda a $\sigma$-álgebra gerada por ele.
- **Teorema de Radon–Nikodým:** se $\nu$ e $\mu$ são medidas $\sigma$-finitas em $(\Omega, \mathcal{F})$ e $\nu$ é absolutamente contínua em relação a $\mu$ ($\nu \ll \mu$, isto é, $\mu(A) = 0 \implies \nu(A) = 0$), existe uma função mensurável não negativa $f = \frac{d\nu}{d\mu}$ (única $\mu$-q.t.p.) tal que $\nu(A) = \int_A f \, d\mu$ para todo $A \in \mathcal{F}$. Esse resultado fundamenta tanto as densidades contínuas quanto a definição geral de esperança condicional e a mudança de medida em finanças (medida neutra ao risco).

## 2. Probabilidade condicional e independência

Para $B \in \mathcal{F}$ com $\mathbb{P}(B) > 0$, a probabilidade condicional de $A$ dado $B$ é $\mathbb{P}(A \mid B) = \mathbb{P}(A \cap B)/\mathbb{P}(B)$. Dada uma partição enumerável $(B_k)_{k \ge 1}$ de $\Omega$ com $\mathbb{P}(B_k) > 0$:

- **Lei da probabilidade total:** $\mathbb{P}(A) = \sum_k \mathbb{P}(A \mid B_k)\mathbb{P}(B_k)$.
- **Teorema de Bayes:** $\mathbb{P}(B_j \mid A) = \frac{\mathbb{P}(A \mid B_j)\mathbb{P}(B_j)}{\sum_k \mathbb{P}(A \mid B_k)\mathbb{P}(B_k)}$, para $\mathbb{P}(A) > 0$.

Uma família de eventos $(A_i)_{i \in I}$ é **independente** se, para toda subfamília finita distinta $\{i_1, \dots, i_k\} \subseteq I$,

$$\mathbb{P}(A_{i_1} \cap \dots \cap A_{i_k}) = \prod_{m=1}^{k} \mathbb{P}(A_{i_m}).$$

Analogamente, $\sigma$-álgebras $(\mathcal{G}_i)_{i \in I}$ são independentes se essa fatoração vale para quaisquer escolhas $A_{i_m} \in \mathcal{G}_{i_m}$. Pelo teorema $\pi$-$\lambda$, basta verificar a fatoração em $\pi$-sistemas geradores.

## 3. Variáveis aleatórias, vetores e esperança

Uma **variável aleatória** é uma função mensurável $X: (\Omega, \mathcal{F}) \to (\mathbb{R}, \mathcal{B}(\mathbb{R}))$. Sua lei (distribuição) é a medida imagem $\mathbb{P}_X(B) = \mathbb{P}(X \in B)$, determinada de modo único pela FDA $F_X(x) = \mathbb{P}(X \le x)$ (não decrescente, contínua à direita com limites à esquerda, tendendo a $0$ em $-\infty$ e a $1$ em $+\infty$). A função quantil generalizada é

$$F_X^{-1}(u) = \inf \{x \in \mathbb{R} : F_X(x) \ge u\}, \qquad u \in (0, 1),$$

o que permite gerar qualquer distribuição unidimensional a partir de $U \sim \operatorname{Uniforme}(0, 1)$ via $X = F_X^{-1}(U)$. Uma distribuição pode ser discreta, absolutamente contínua (com densidade $f_X$ em relação à medida de Lebesgue), singular contínua ou uma combinação convexa dessas três componentes.

Para vetores aleatórios $X = (X_1, \dots, X_d)$:

- A soma $X + Y$ de variáveis independentes tem lei dada pela **convolução** das distribuições individuais.
- Se $X$ possui densidade conjunta $f_X$ e $g: U \to V$ é um difeomorfismo $C^1$ entre abertos de $\mathbb{R}^d$, então $Y = g(X)$ possui densidade

$$f_Y(y) = f_X\!\left(g^{-1}(y)\right)\,\left|\det Dg^{-1}(y)\right|, \qquad y \in V.$$

### Esperança como integral de Lebesgue e teoremas de passagem ao limite

A esperança $\mathbb{E}[X] = \int_\Omega X \, d\mathbb{P}$ é construída sucessivamente para funções indicadoras, funções simples, variáveis não negativas (por aproximação monótona) e variáveis integráveis ($\mathbb{E}[|X|] < \infty$, decompondo $X = X^+ - X^-$). Para qualquer função mensurável $g$ (com $g(X)$ não negativa ou integrável), vale a fórmula da mudança de variável $\mathbb{E}[g(X)] = \int_{\mathbb{R}} g(x)\, d\mathbb{P}_X(x)$.

Os três teoremas fundamentais de passagem ao limite sob a esperança são:

1. **Teorema da Convergência Monótona (TCM):** se $0 \le X_n \uparrow X$ q.c., então $\mathbb{E}[X_n] \uparrow \mathbb{E}[X]$.
2. **Lema de Fatou:** se $X_n \ge 0$ q.c., então $\mathbb{E}\!\left[\liminf_{n\to\infty} X_n\right] \le \liminf_{n\to\infty} \mathbb{E}[X_n]$.
3. **Teorema da Convergência Dominada (TCD):** se $X_n \to X$ q.c. e existe $Y \in \mathcal{L}^1$ com $|X_n| \le Y$ q.c. para todo $n$, então $X \in \mathcal{L}^1$, $\mathbb{E}[|X_n - X|] \to 0$ e $\mathbb{E}[X_n] \to \mathbb{E}[X]$.

Em espaços produto $(\Omega_1 \times \Omega_2, \mathcal{F}_1 \otimes \mathcal{F}_2, \mu_1 \otimes \mu_2)$, os teoremas de **Tonelli** (para funções não negativas) e **Fubini** (para funções integráveis) autorizam trocar a ordem das integrais iteradas.

## 4. Momentos, correlação e desigualdades

Para $X, Y \in \mathcal{L}^2$:

$$\operatorname{Var}(X) = \mathbb{E}\!\left[(X - \mathbb{E}[X])^2\right], \qquad \operatorname{Cov}(X, Y) = \mathbb{E}\!\left[(X - \mathbb{E}[X])(Y - \mathbb{E}[Y])\right], \qquad \rho(X, Y) = \frac{\operatorname{Cov}(X, Y)}{\sqrt{\operatorname{Var}(X)\operatorname{Var}(Y)}}.$$

O melhor preditor linear de $Y$ a partir de $X$ em erro quadrático médio minimiza $\mathbb{E}[(Y - a - bX)^2]$ com $b = \operatorname{Cov}(X, Y)/\operatorname{Var}(X)$ e $a = \mathbb{E}[Y] - b\mathbb{E}[X]$.

| Desigualdade | Hipóteses | Enunciado |
|---|---|---|
| **Markov** | $X \ge 0$, $a > 0$ | $\mathbb{P}(X \ge a) \le \mathbb{E}[X] / a$ |
| **Tchebyshev** | $X \in \mathcal{L}^2$, $\varepsilon > 0$ | $\mathbb{P}(|X - \mathbb{E}[X]| \ge \varepsilon) \le \operatorname{Var}(X) / \varepsilon^2$ |
| **Jensen** | $\varphi$ convexa, $X, \varphi(X) \in \mathcal{L}^1$ | $\varphi(\mathbb{E}[X]) \le \mathbb{E}[\varphi(X)]$ |
| **Cauchy–Schwarz** | $X, Y \in \mathcal{L}^2$ | $|\mathbb{E}[XY]| \le \lVert X \rVert_2 \lVert Y \rVert_2$ |
| **Hölder** | $p, q > 1$, $p^{-1} + q^{-1} = 1$ | $\mathbb{E}[|XY|] \le \lVert X \rVert_p \lVert Y \rVert_q$ |
| **Minkowski** | $p \ge 1$, $X, Y \in \mathcal{L}^p$ | $\lVert X + Y \rVert_p \le \lVert X \rVert_p + \lVert Y \rVert_p$ |
| **Lyapunov** | $0 < r \le s$ | $\lVert X \rVert_r \le \lVert X \rVert_s$ |
| **Paley–Zygmund** | $X \ge 0$, $X \in \mathcal{L}^2$, $\theta \in [0, 1]$ | $\mathbb{P}(X > \theta \mathbb{E}[X]) \ge (1 - \theta)^2 \frac{(\mathbb{E}[X])^2}{\mathbb{E}[X^2]}$ |

## 5. Modos de convergência e lemas de Borel–Cantelli

Para uma sequência $(X_n)_{n \ge 1}$ e uma variável $X$:

- **Quase certa ($X_n \xrightarrow{\text{q.c.}} X$):** $\mathbb{P}(\lim_{n\to\infty} X_n = X) = 1$.
- **Em probabilidade ($X_n \xrightarrow{\mathbb{P}} X$):** $\lim_{n\to\infty} \mathbb{P}(|X_n - X| > \varepsilon) = 0$ para todo $\varepsilon > 0$.
- **Em $\mathcal{L}^p$ ($X_n \xrightarrow{\mathcal{L}^p} X$, $p \ge 1$):** $\lim_{n\to\infty} \mathbb{E}[|X_n - X|^p] = 0$.
- **Em distribuição ($X_n \xrightarrow{d} X$):** $F_{X_n}(x) \to F_X(x)$ em todo ponto de continuidade $x$ de $F_X$ (equivalentemente, $\mathbb{E}[g(X_n)] \to \mathbb{E}[g(X)]$ para toda $g$ contínua e limitada — Teorema de Helly–Bray / Portmanteau).

### Relações entre modos de convergência

- $X_n \xrightarrow{\text{q.c.}} X \implies X_n \xrightarrow{\mathbb{P}} X \implies X_n \xrightarrow{d} X$.
- $X_n \xrightarrow{\mathcal{L}^s} X \implies X_n \xrightarrow{\mathcal{L}^r} X$ ($s \ge r \ge 1$) $\implies X_n \xrightarrow{\mathbb{P}} X$.
- $X_n \xrightarrow{\mathbb{P}} X$ implica existência de subsequência $(X_{n_k})$ tal que $X_{n_k} \xrightarrow{\text{q.c.}} X$.
- Se $X_n \xrightarrow{d} c$ (constante), então $X_n \xrightarrow{\mathbb{P}} c$.
- **Acoplamento de Skorokhod:** se $X_n \xrightarrow{d} X$, existe um espaço de probabilidade comum com cópias $\tilde{X}_n \stackrel{d}{=} X_n$ e $\tilde{X} \stackrel{d}{=} X$ tais que $\tilde{X}_n \xrightarrow{\text{q.c.}} \tilde{X}$.

### Lemas de Borel–Cantelli

Seja $\{A_n \text{ i.v.}\} = \limsup_{n\to\infty} A_n = \bigcap_{m=1}^{\infty} \bigcup_{n=m}^{\infty} A_n$ o evento de que infinitos $A_n$ ocorram:

1. **1º Lema de Borel–Cantelli:** se $\sum_{n=1}^{\infty} \mathbb{P}(A_n) < \infty$, então $\mathbb{P}(A_n \text{ i.v.}) = 0$ (sem exigir independência). Em particular, $\sum_n \mathbb{P}(|X_n - X| > \varepsilon) < \infty$ para todo $\varepsilon > 0$ garante $X_n \xrightarrow{\text{q.c.}} X$.
2. **2º Lema de Borel–Cantelli:** se os eventos $(A_n)$ são independentes e $\sum_{n=1}^{\infty} \mathbb{P}(A_n) = \infty$, então $\mathbb{P}(A_n \text{ i.v.}) = 1$.

## 6. Leis dos Grandes Números (LGN)

Seja $S_n = \sum_{k=1}^{n} X_k$ a soma parcial de uma sequência de variáveis aleatórias:

- **LGN Fraca (Tchebyshev / Khintchine):** se $(X_n)$ são não correlacionadas com variância uniformemente limitada, ou se são i.i.d. com $\mathbb{E}[|X_1|] < \infty$ e média $\mu$, então $S_n / n \xrightarrow{\mathbb{P}} \mu$.
- **LGN Forte de Kolmogorov / Etemadi:** se $(X_n)$ são i.i.d. (ou mesmo independentes dois a dois e identicamente distribuídas, na prova de Etemadi) com $\mathbb{E}[|X_1|] < \infty$ e $\mathbb{E}[X_1] = \mu$, então

$$\frac{1}{n} \sum_{k=1}^{n} X_k \xrightarrow{\text{q.c.}} \mu.$$

Reciprocamente, se $\mathbb{E}[|X_1|] = \infty$, então $\limsup_{n\to\infty} |S_n|/n = \infty$ q.c.

- **Teorema de Glivenko–Cantelli:** para $(X_n)$ i.i.d. com FDA $F$, a função de distribuição empírica $\hat{F}_n(x) = \frac{1}{n}\sum_{k=1}^{n} \mathbf{1}_{\{X_k \le x\}}$ converge uniformemente:

$$\sup_{x \in \mathbb{R}} \left|\hat{F}_n(x) - F(x)\right| \xrightarrow{\text{q.c.}} 0.$$

Esse resultado fornece a base assintótica de estimadores empíricos como VaR histórico (implementado em `quantlab.analysis`) e do método de **integração por Monte Carlo**, no qual a média amostral $\hat{I}_n = \frac{1}{n}\sum_{k=1}^n g(X_k)$ converge q.c. para $\mathbb{E}[g(X)]$.

## 7. Teorema do Limite Central (TLC) e transformadas

### Transformadas

- **Função geradora de momentos (FGM):** $M_X(t) = \mathbb{E}[e^{tX}]$, definida no intervalo onde é finita. Quando finita em uma vizinhança aberta da origem, determina unicamente a distribuição de $X$ e gera momentos via $M_X^{(k)}(0) = \mathbb{E}[X^k]$.
- **Função característica:** $\varphi_X(t) = \mathbb{E}[e^{itX}]$, sempre bem definida e uniformemente contínua para todo $t \in \mathbb{R}$, com $|\varphi_X(t)| \le 1$ e $\varphi_X(0) = 1$. Para $X, Y$ independentes, $\varphi_{X+Y}(t) = \varphi_X(t)\varphi_Y(t)$.
- **Fórmula de inversão e unicidade:** $\varphi_X$ determina unicamente $\mathbb{P}_X$. Em todo intervalo $[a, b]$ cujos extremos são pontos de continuidade de $F_X$,

$$F_X(b) - F_X(a) = \lim_{T \to \infty} \frac{1}{2\pi} \int_{-T}^{T} \frac{e^{-ita} - e^{-itb}}{it}\,\varphi_X(t)\,dt.$$

- **Teorema da Continuidade de Lévy:** $X_n \xrightarrow{d} X$ se e somente se $\varphi_{X_n}(t) \to \varphi_X(t)$ para todo $t \in \mathbb{R}$. Mais geralmente, se $\varphi_{X_n}(t) \to \varphi(t)$ pontualmente e $\varphi$ é contínua em $0$, então $\varphi$ é a função característica de alguma variável $X$ e $X_n \xrightarrow{d} X$ (usando confinamento / *tightness* e o Teorema de Seleção de Helly).

### Teorema do Limite Central e ferramentas assintóticas

- **TLC clássico (caso i.i.d.):** se $(X_n)$ são i.i.d. com média $\mu$ e variância $0 < \sigma^2 < \infty$, então

$$\frac{S_n - n\mu}{\sigma\sqrt{n}} \xrightarrow{d} \mathcal{N}(0, 1).$$

- **Condição de Lindeberg–Feller (arranjos triangulares):** para variáveis independentes em cada linha $(X_{n,k})_{1 \le k \le k_n}$ com média zero e $\sum_{k=1}^{k_n} \sigma_{n,k}^2 = 1$, se para todo $\varepsilon > 0$ vale

$$\lim_{n\to\infty} \sum_{k=1}^{k_n} \mathbb{E}\!\left[X_{n,k}^2\,\mathbf{1}_{\{|X_{n,k}| > \varepsilon\}}\right] = 0,$$

então $\sum_{k=1}^{k_n} X_{n,k} \xrightarrow{d} \mathcal{N}(0, 1)$. A condição de **Lyapunov** ($\sum_k \mathbb{E}[|X_{n,k}|^{2+\delta}] \to 0$ para algum $\delta > 0$) é suficiente para Lindeberg.

- **Teorema do Mapeamento Contínuo:** se $X_n \xrightarrow{d} X$ e $g$ tem conjunto de descontinuidades com probabilidade zero sob $\mathbb{P}_X$, então $g(X_n) \xrightarrow{d} g(X)$.
- **Teorema de Slutsky:** se $X_n \xrightarrow{d} X$ e $Y_n \xrightarrow{\mathbb{P}} c$ (constante), então $X_n + Y_n \xrightarrow{d} X + c$ e $X_n Y_n \xrightarrow{d} c X$.
- **Método Delta:** se $\sqrt{n}(\hat{\theta}_n - \theta) \xrightarrow{d} \mathcal{N}(0, \sigma^2)$ e $g$ é diferenciável em $\theta$ com $g'(\theta) \neq 0$, então $\sqrt{n}(g(\hat{\theta}_n) - g(\theta)) \xrightarrow{d} \mathcal{N}\!\left(0, [g'(\theta)]^2 \sigma^2\right)$.

## 8. Leis 0–1 e séries aleatórias

- **Lei 0–1 de Kolmogorov:** para uma sequência independente $(X_n)_{n \ge 1}$, a $\sigma$-álgebra caudal $\mathcal{T} = \bigcap_{n=1}^{\infty} \sigma(X_n, X_{n+1}, \dots)$ é trivial: todo evento $A \in \mathcal{T}$ satisfaz $\mathbb{P}(A) \in \{0, 1\}$.
- **Lei 0–1 de Hewitt–Savage:** para uma sequência i.i.d. $(X_n)$, todo evento invariante sob permutações finitas das coordenadas (evento permutável) tem probabilidade $0$ ou $1$.
- **Desigualdade Maximal de Kolmogorov:** se $X_1, \dots, X_n$ são independentes com média zero e variância finita, e $S_k = \sum_{j=1}^k X_j$, então para todo $\lambda > 0$:

$$\mathbb{P}\!\left(\max_{1 \le k \le n} |S_k| \ge \lambda\right) \le \frac{\operatorname{Var}(S_n)}{\lambda^2}.$$

- **Teorema das Três Séries de Kolmogorov:** uma série $\sum_{n=1}^{\infty} X_n$ de variáveis independentes converge q.c. se e somente se, para algum (ou todo) corte $c > 0$, com $Y_n = X_n \mathbf{1}_{\{|X_n| \le c\}}$, convergem simultaneamente:
  1. $\sum_{n=1}^{\infty} \mathbb{P}(|X_n| > c) < \infty$,
  2. $\sum_{n=1}^{\infty} \mathbb{E}[Y_n]$ converge em $\mathbb{R}$,
  3. $\sum_{n=1}^{\infty} \operatorname{Var}(Y_n) < \infty$.

## 9. Teoria ergódica

A teoria ergódica estabelece a ponte entre sistemas dinâmicos determinísticos (como os estudados em `quantlab.dynamics`) e teoremas limites probabilísticos.

Seja $(\Omega, \mathcal{F}, \mathbb{P})$ um espaço de probabilidade e $T: \Omega \to \Omega$ uma transformação mensurável que **preserva medida**: $\mathbb{P}(T^{-1}(A)) = \mathbb{P}(A)$ para todo $A \in \mathcal{F}$. O conjunto $\mathcal{I}_T = \{A \in \mathcal{F} : T^{-1}(A) = A\}$ é a $\sigma$-álgebra dos eventos invariantes.

- **Teorema de Recorrência de Poincaré:** para todo $A \in \mathcal{F}$, quase todo ponto $\omega \in A$ retorna a $A$ infinitas vezes sob iteração de $T$.
- **Ergodicidade:** $T$ é **ergódica** se $\mathbb{P}(A) \in \{0, 1\}$ para todo $A \in \mathcal{I}_T$.
- **Mistura (*mixing*):** $T$ é fortemente misturadora se $\lim_{n\to\infty} \mathbb{P}(A \cap T^{-n}(B)) = \mathbb{P}(A)\mathbb{P}(B)$ para quaisquer $A, B \in \mathcal{F}$. Toda transformação misturadora é ergódica, mas a recíproca falha (exemplo clássico: rotação irracional do círculo $T(x) = x + \alpha \bmod 1$, $\alpha \notin \mathbb{Q}$, que é ergódica porém não misturadora).
- **Teorema Ergódico Pontual de Birkhoff:** se $T$ preserva $\mathbb{P}$ e $f \in \mathcal{L}^1$, então

$$\frac{1}{n} \sum_{k=0}^{n-1} f(T^k \omega) \xrightarrow{\text{q.c. e } \mathcal{L}^1} \mathbb{E}[f \mid \mathcal{I}_T].$$

Quando $T$ é ergódica, $\mathbb{E}[f \mid \mathcal{I}_T] = \mathbb{E}[f]$ q.c., igualando a **média temporal** ao longo de uma trajetória típica à **média espacial** sob a medida invariante. A LGN Forte para sequências estacionárias ergódicas segue diretamente aplicando Birkhoff ao operador deslocamento (*shift*) $\theta$.

- **Teorema Ergódico de von Neumann:** para $f \in \mathcal{L}^p$ ($1 \le p < \infty$), a média temporal converge em $\mathcal{L}^p$ para $\mathbb{E}[f \mid \mathcal{I}_T]$ (no caso $p = 2$, a projeção ortogonal sobre o subespaço de funções $T$-invariantes).

## 10. Grandes desvios

Enquanto a LGN garante que $\bar{X}_n = S_n / n \to \mu$ e o TLC descreve flutuações típicas de ordem $O(n^{-1/2})$, a teoria de **grandes desvios** quantifica a taxa exponencial de decaimento de eventos raros de ordem $O(1)$ (como perdas extremas acumuladas).

Para $(X_n)$ i.i.d. com FGM $M(t) = \mathbb{E}[e^{tX_1}]$ e log-FGM (geradora de cumulantes) $\Lambda(t) = \ln M(t)$:

- **Desigualdade de Chernoff:** para todo $a \in \mathbb{R}$,

$$\mathbb{P}\!\left(\frac{S_n}{n} \ge a\right) \le \exp(-n I(a)), \qquad a \ge \mathbb{E}[X_1],$$

onde a **função taxa** é a transformada de Legendre–Fenchel de $\Lambda$:

$$I(a) = \sup_{t \in \mathbb{R}} \left[a t - \Lambda(t)\right].$$

- **Princípio dos Grandes Desvios de Cramér:** se $M(t) < \infty$ em uma vizinhança da origem (ou mais geralmente para todo $a$ no interior do domínio adequado), então para $a > \mathbb{E}[X_1]$:

$$\lim_{n\to\infty} \frac{1}{n} \ln \mathbb{P}\!\left(\frac{S_n}{n} \ge a\right) = -I(a).$$

A função $I$ é convexa, semicontínua inferiormente, não negativa e anula-se em $a = \mathbb{E}[X_1]$. Em distribuições de cauda pesada (onde $M(t) = \infty$ para todo $t > 0$), o decaimento das probabilidades extremas deixa de ser exponencial e torna-se subexponencial/polinomial — ponto crítico em gestão de risco financeiro.

## Aspectos computacionais e hipóteses práticas

- **Taxa de Monte Carlo:** pelo TLC, o erro padrão de um estimador de Monte Carlo $\hat{I}_n$ com variância $\sigma^2$ decai como $\sigma / \sqrt{n}$. Reduzir o erro por um fator de 10 exige multiplicar o número de amostras por 100, salvo quando se usam técnicas de redução de variância (variáveis antitéticas, variáveis de controle, amostragem por importância).
- **Dependência temporal e caudas pesadas:** resultados clássicos de LGN/TLC/Cramér assumem independência e existência de momentos (variância finita para TLC clássico; FGM finita em torno de zero para Cramér). Em séries financeiras reais, há agrupamento de volatilidade, autocorrelação e caudas mais pesadas que a normal (distribuições com curtose alta ou momentos superiores infinitos).
- **Estabilidade numérica:** o cálculo empírico de variância e FGM sofre de cancelamento catastrófico ou *overflow* em ponto flutuante; implementações numéricas devem empregar algoritmos de duas passagens (ou Welford) para variância e truque *log-sum-exp* ao avaliar $\Lambda(t) = \ln \mathbb{E}[e^{tX}]$.

## Limitações

- Este documento resume a base teórica de probabilidade em espaços mensuráveis gerais, sem construir ainda estimadores paramétricos, testes de hipóteses ou simulações específicas no motor.
- Resultados ergódicos para sistemas dinâmicos caóticos concretos (como o mapa logístico e o sistema de Lorenz já presentes em `quantlab.dynamics`) exigem identificar medidas invariantes físicas (SRB), o que extrapola o escopo da análise linear atualmente implementada.

## Referências

- L. T. Rolla e B. N. B. de Lima. *Probabilidade*. Notas de aula / livro aberto, 2021–2026 (CC BY-ND 4.0).
- R. Durrett. *Probability: Theory and Examples*. Cambridge University Press, 5ª ed., 2019.
- P. Billingsley. *Probability and Measure*. Wiley, 3ª ed., 1995.
- D. Williams. *Probability with Martingales*. Cambridge University Press, 1991.
- A. Dembo e O. Zeitouni. *Large Deviations Techniques and Applications*. Springer, 2ª ed., 1998.

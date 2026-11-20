# Esperança condicional, martingais e apreçamento em tempo discreto

Status: **fundamentação teórica** (base matemática de apoio para a Fase 6 — modelos estocásticos e apreçamento de derivativos). Ainda não há módulo dedicado implementado em `engine/quantlab/`; quando existir, esta página passará a apontar para o código e os testes correspondentes.

## Escopo e conexão com o QuantLab

A teoria de martingais é a linguagem matemática da ausência de arbitragem em finanças quantitativas: sob a medida de probabilidade neutra ao risco, preços descontados de ativos negociáveis e a riqueza descontada de estratégias autofinanciadas comportam-se como martingais. Este documento reúne a construção da esperança condicional, os teoremas fundamentais de martingais em tempo discreto, a transformada martingale, a representação de martingais no espaço binomial e a formulação em tempo discreto do modelo de Black–Scholes.

Documentos relacionados:

- [Fundamentos de probabilidade, convergência, ergodicidade e grandes desvios](fundamentos-de-probabilidade.md)
- [Cadeias de Markov em tempo discreto](cadeias-de-markov-tempo-discreto.md)
- [Processos de Markov em tempo contínuo](processos-de-markov-tempo-continuo.md)

## Notação

| Símbolo | Significado |
|---|---|
| $(\Omega, \mathcal{F}, \mathbb{P})$ | espaço de probabilidade |
| $(\mathcal{F}_n)_{n \ge 0}$ | filtração (família crescente de sub-$\sigma$-álgebras de $\mathcal{F}$) |
| $\mathbb{E}[X \mid \mathcal{G}]$ | esperança condicional de $X$ dada a $\sigma$-álgebra $\mathcal{G} \subseteq \mathcal{F}$ |
| $\tau$ | tempo de parada em relação a $(\mathcal{F}_n)$ |
| $X^\tau_n = X_{n \wedge \tau}$ | processo parado em $\tau$, onde $n \wedge \tau = \min(n, \tau)$ |
| $(C \circ X)_n$ | transformada martingale do processo $X$ pela estratégia previsível $C$ |
| $\langle X \rangle_n$ | variação quadrática previsível de um martingale em $\mathcal{L}^2$ |
| $B_n, S_n, R_n$ | título livre de risco, ativo arriscado e retorno simples do ativo no passo $n$ |
| $X_n, Y_n$ | riqueza nominal e riqueza descontada de uma carteira autofinanciada |

## 1. Esperança condicional

### Casos elementares

- **Dada uma partição finita ou enumerável $\mathcal{D} = \{D_1, D_2, \dots\}$ de $\Omega$** com $\mathbb{P}(D_k) > 0$: define-se $\mathbb{E}[X \mid \mathcal{D}]$ como a variável constante em cada bloco $D_k$ igual à média condicional $\mathbb{E}[X \mid D_k] = \frac{1}{\mathbb{P}(D_k)}\int_{D_k} X \, d\mathbb{P}$:

$$\mathbb{E}[X \mid \mathcal{D}](\omega) = \sum_k \mathbb{E}[X \mid D_k]\,\mathbf{1}_{D_k}(\omega).$$

- **Caso discreto e caso com densidade conjunta:** se $(X, Y)$ tem densidade conjunta $f_{X,Y}$ e marginal $f_Y(y) > 0$, a densidade condicional é $f_{X \mid Y}(x \mid y) = f_{X,Y}(x, y)/f_Y(y)$ e $\mathbb{E}[g(X) \mid Y = y] = \int_{\mathbb{R}} g(x) f_{X \mid Y}(x \mid y)\,dx$.

### Definição geral dada uma $\sigma$-álgebra

Seja $X \in \mathcal{L}^1(\Omega, \mathcal{F}, \mathbb{P})$ e $\mathcal{G} \subseteq \mathcal{F}$ uma sub-$\sigma$-álgebra. Uma **esperança condicional** de $X$ dada $\mathcal{G}$, denotada $Y = \mathbb{E}[X \mid \mathcal{G}]$, é qualquer variável aleatória tal que:

1. $Y$ é $\mathcal{G}$-mensurável e integrável;
2. Para todo evento $G \in \mathcal{G}$,

$$\int_G Y \, d\mathbb{P} = \int_G X \, d\mathbb{P} \qquad \text{(isto é, } \mathbb{E}[Y\,\mathbf{1}_G] = \mathbb{E}[X\,\mathbf{1}_G]\text{)}.$$

**Existência e unicidade:** pelo Teorema de Radon–Nikodým (aplicado à medida com sinal $\nu(G) = \int_G X\,d\mathbb{P}$ em relação à restrição $\mathbb{P}|_{\mathcal{G}}$), a esperança condicional sempre existe e é única a menos de eventos de probabilidade nula (versões q.c. iguais). Quando $X \in \mathcal{L}^2$, $\mathbb{E}[X \mid \mathcal{G}]$ coincide com a **projeção ortogonal** de $X$ no subespaço fechado $\mathcal{L}^2(\Omega, \mathcal{G}, \mathbb{P})$: ela minimiza $\mathbb{E}[(X - Z)^2]$ entre todas as variáveis $Z \in \mathcal{L}^2(\mathcal{G})$.

Em espaços poloneses (como $\mathbb{R}^d$), existe também uma **distribuição condicional regular** $\kappa(\omega, B)$ (núcleo de probabilidade que realiza $\mathbb{P}(X \in B \mid \mathcal{G})$ simultaneamente para todo boreliano $B$), permitindo escrever $\mathbb{E}[g(X) \mid \mathcal{G}](\omega) = \int g(x)\,\kappa(\omega, dx)$ q.c.

### Propriedades estruturais

Para $X, Y \in \mathcal{L}^1$ e sub-$\sigma$-álgebras $\mathcal{H} \subseteq \mathcal{G} \subseteq \mathcal{F}$ (todas as igualdades e desigualdades valem q.c.):

- **Linearidade e monotonicidade:** $\mathbb{E}[aX + bY \mid \mathcal{G}] = a\mathbb{E}[X \mid \mathcal{G}] + b\mathbb{E}[Y \mid \mathcal{G}]$; se $X \le Y$ q.c., então $\mathbb{E}[X \mid \mathcal{G}] \le \mathbb{E}[Y \mid \mathcal{G}]$.
- **Preservação da esperança:** $\mathbb{E}\!\left[\mathbb{E}[X \mid \mathcal{G}]\right] = \mathbb{E}[X]$.
- **Retirada do que é conhecido (*pull-out*):** se $Z$ é $\mathcal{G}$-mensurável e $XZ \in \mathcal{L}^1$, então $\mathbb{E}[XZ \mid \mathcal{G}] = Z\,\mathbb{E}[X \mid \mathcal{G}]$. Em particular, se $X$ é $\mathcal{G}$-mensurável, $\mathbb{E}[X \mid \mathcal{G}] = X$.
- **Propriedade da torre (esperança iterada):** $\mathbb{E}\!\left[\mathbb{E}[X \mid \mathcal{G}] \mid \mathcal{H}\right] = \mathbb{E}[X \mid \mathcal{H}]$.
- **Independência:** se $\sigma(X)$ é independente de $\mathcal{G}$, então $\mathbb{E}[X \mid \mathcal{G}] = \mathbb{E}[X]$.
- **Desigualdade de Jensen condicional e contração em $\mathcal{L}^p$:** se $\varphi$ é convexa e $X, \varphi(X) \in \mathcal{L}^1$, então $\varphi(\mathbb{E}[X \mid \mathcal{G}]) \le \mathbb{E}[\varphi(X) \mid \mathcal{G}]$. Em particular, $\lVert \mathbb{E}[X \mid \mathcal{G}] \rVert_p \le \lVert X \rVert_p$ para todo $p \ge 1$.
- **Passagem ao limite condicional:** valem versões condicionais do Teorema da Convergência Monótona, do Lema de Fatou e do Teorema da Convergência Dominada.

## 2. Filtrações, processos adaptados e martingais

Uma **filtração** é uma sequência crescente de sub-$\sigma$-álgebras $\mathcal{F}_0 \subseteq \mathcal{F}_1 \subseteq \dots \subseteq \mathcal{F}$, representando a informação disponível em cada instante $n$. A filtração natural de um processo $X = (X_n)_{n \ge 0}$ é $\mathcal{F}_n^X = \sigma(X_0, \dots, X_n)$.

- Um processo $(X_n)_{n \ge 0}$ é **adaptado** a $(\mathcal{F}_n)$ se $X_n$ é $\mathcal{F}_n$-mensurável para todo $n \ge 0$.
- Um processo $(C_n)_{n \ge 1}$ é **previsível** em relação a $(\mathcal{F}_n)$ se $C_n$ é $\mathcal{F}_{n-1}$-mensurável para todo $n \ge 1$ (isto é, decidido com a informação do instante anterior).

Um processo adaptado e integrável $(X_n)_{n \ge 0}$ ($\mathbb{E}[|X_n|] < \infty$ para todo $n$) é chamado:

- **Martingale** se $\mathbb{E}[X_{n+1} \mid \mathcal{F}_n] = X_n$ q.c. para todo $n \ge 0$;
- **Submartingale** se $\mathbb{E}[X_{n+1} \mid \mathcal{F}_n] \ge X_n$ q.c. para todo $n \ge 0$;
- **Supermartingale** se $\mathbb{E}[X_{n+1} \mid \mathcal{F}_n] \le X_n$ q.c. para todo $n \ge 0$.

Por indução usando a propriedade da torre, um martingale tem esperança constante ($\mathbb{E}[X_n] = \mathbb{E}[X_0]$), submartingales têm esperança não decrescente e supermartingales têm esperança não crescente.

### Exemplos canônicos

1. **Somas de incrementos de média zero:** se $(\xi_k)$ são independentes com $\mathbb{E}[\xi_k] = 0$, então $S_n = \sum_{k=1}^n \xi_k$ é martingale (caso particular: passeio aleatório simétrico em $\mathbb{Z}$).
2. **Produtos de fatores independentes de média 1:** se $(\eta_k)$ são independentes, integráveis e $\mathbb{E}[\eta_k] = 1$, então $M_n = \prod_{k=1}^n \eta_k$ é martingale.
3. **Martingale de Doob (fechado):** para qualquer $X \in \mathcal{L}^1$, $M_n = \mathbb{E}[X \mid \mathcal{F}_n]$ é martingale.
4. **Função convexa:** se $X_n$ é martingale e $\varphi$ é convexa com $\varphi(X_n) \in \mathcal{L}^1$, então $\varphi(X_n)$ é submartingale (por Jensen condicional). Se $X_n$ é submartingale e $\varphi$ é convexa e não decrescente, $\varphi(X_n)$ também é submartingale. Em particular, $|X_n|^p$ ($p \ge 1$) e $X_n^+$ são submartingales para todo martingale $X_n$ em $\mathcal{L}^p$.

## 3. Tempos de parada, desigualdades maximais e amostragem opcional

Uma variável $\tau: \Omega \to \mathbb{Z}_+ \cup \{\infty\}$ é um **tempo de parada** em relação a $(\mathcal{F}_n)$ se $\{\tau \le n\} \in \mathcal{F}_n$ para todo $n \ge 0$ (equivalentemente, $\{\tau = n\} \in \mathcal{F}_n$). A decisão de parar no instante $n$ depende apenas da história observada até $n$, sem antecipar o futuro.

### Teorema do Martingale Parado

Se $(X_n)$ é martingale (resp. sub/supermartingale) e $\tau$ é tempo de parada, o processo parado $X_n^\tau = X_{n \wedge \tau}$ também é martingale (resp. sub/supermartingale). Em particular, para um martingale, $\mathbb{E}[X_{n \wedge \tau}] = \mathbb{E}[X_0]$ para todo $n \ge 0$.

### Desigualdades maximais de Doob

Seja $(X_n)_{n \ge 0}$ um submartingale não negativo e $M_n^* = \max_{0 \le k \le n} X_k$. Para todo $\lambda > 0$:

$$\lambda\,\mathbb{P}(M_n^* \ge \lambda) \le \mathbb{E}\!\left[X_n\,\mathbf{1}_{\{M_n^* \ge \lambda\}}\right] \le \mathbb{E}[X_n].$$

Como consequências diretas:

- **Desigualdade de Doob–Kolmogorov:** se $(M_n)$ é martingale em $\mathcal{L}^p$ ($p \ge 1$), então $\mathbb{P}(\max_{0 \le k \le n} |M_k| \ge \lambda) \le \mathbb{E}[|M_n|^p] / \lambda^p$.
- **Desigualdade maximal de Doob em $\mathcal{L}^p$:** para um submartingale não negativo $(X_n)$ em $\mathcal{L}^p$ com $p > 1$,

$$\left\lVert \max_{0 \le k \le n} X_k \right\rVert_p \le \frac{p}{p - 1}\,\lVert X_n \rVert_p, \qquad \text{ou seja,} \qquad \mathbb{E}\!\left[\max_{0 \le k \le n} X_k^p\right] \le \left(\frac{p}{p - 1}\right)^p \mathbb{E}[X_n^p].$$

### Teorema da Amostragem Opcional

Em geral, $\mathbb{E}[X_{n \wedge \tau}] = \mathbb{E}[X_0]$ **não** implica automaticamente $\mathbb{E}[X_\tau] = \mathbb{E}[X_0]$ quando $\tau$ pode ser arbitrariamente grande. Um contraexemplo clássico é a estratégia de dobra em um jogo justo (parar na primeira vez que o ganho acumulado atinge $+1$): o tempo de parada é finito q.c., $X_\tau = 1$ q.c., porém $\mathbb{E}[X_0] = 0 \neq 1 = \mathbb{E}[X_\tau]$ porque o capital arriscado cresce sem limite antes da parada.

Para um martingale $(X_n)$ e um tempo de parada $\tau$, a igualdade $\mathbb{E}[X_\tau] = \mathbb{E}[X_0]$ vale (e para supermartingales, $\mathbb{E}[X_\tau] \le \mathbb{E}[X_0]$) sob qualquer uma das condições suficientes abaixo:

1. $\tau$ é limitado ($\tau \le N$ q.c. para alguma constante $N$);
2. $\tau < \infty$ q.c. e o processo parado $|X_{n \wedge \tau}| \le K$ é uniformemente limitado;
3. $\mathbb{E}[\tau] < \infty$ e os incrementos são uniformemente limitados em esperança condicional ($\mathbb{E}[|X_{n+1} - X_n| \mid \mathcal{F}_n] \le C$ q.c. em $\{n < \tau\}$);
4. A família $\{X_{n \wedge \tau}\}_{n \ge 0}$ é uniformemente integrável (em particular, se o martingale é fechado por $X_\infty \in \mathcal{L}^1$).

### Aplicações imediatas

- **Identidade de Wald:** se $(\xi_k)_{k \ge 1}$ são i.i.d. integráveis com média $\mu$, $S_n = \sum_{k=1}^n \xi_k$ e $\tau$ é tempo de parada com $\mathbb{E}[\tau] < \infty$, então $\mathbb{E}[S_\tau] = \mu\,\mathbb{E}[\tau]$. Se adicionalmente $\operatorname{Var}(\xi_1) = \sigma^2 < \infty$ e $\mu = 0$, então $\mathbb{E}[S_\tau^2] = \sigma^2 \mathbb{E}[\tau]$.
- **Ruína do apostador via martingais:** seja $S_n$ um passeio aleatório simples em $\{0, 1, \dots, a\}$ começando em $x$, com passos $+1$ (probabilidade $p$) e $-1$ (probabilidade $q = 1 - p$), e $\tau = \inf\{n \ge 0 : S_n \in \{0, a\}\}$:
  - Se $p = q = 1/2$, tanto $S_n$ quanto $S_n^2 - n$ são martingais; amostragem opcional fornece $\mathbb{P}_x(S_\tau = a) = x / a$ e $\mathbb{E}_x[\tau] = x(a - x)$.
  - Se $p \neq q$, o processo $M_n = (q/p)^{S_n}$ é martingale limitado até $\tau$; amostragem opcional fornece diretamente

$$\mathbb{P}_x(S_\tau = a) = \frac{1 - (q/p)^x}{1 - (q/p)^a}.$$

## 4. Convergência de martingales e integrabilidade uniforme

### Travessias ascendentes e convergência quase certa

Dado um intervalo $[a, b]$ ($a < b$), seja $U_n([a, b]; X)$ o número de **travessias ascendentes** (*upcrossings*) de $a$ até $b$ completadas pelo processo $X$ até o instante $n$.

- **Desigualdade das travessias ascendentes de Doob:** se $(X_n)$ é supermartingale,

$$\mathbb{E}\!\left[U_n([a, b]; X)\right] \le \frac{\mathbb{E}[(X_n - a)^-]}{b - a},$$

onde $u^- = \max(-u, 0)$.

- **Teorema de Convergência Quase Certa de Doob:** se $(X_n)_{n \ge 0}$ é um supermartingale (ou submartingale, ou martingale) limitado em $\mathcal{L}^1$, isto é, $\sup_{n \ge 0} \mathbb{E}[|X_n|] < \infty$, então existe $X_\infty \in \mathcal{L}^1$ tal que

$$X_n \xrightarrow{\text{q.c.}} X_\infty.$$

**Corolário fundamental:** todo supermartingale não negativo $(X_n \ge 0)$ converge quase certamente para uma variável integrável $X_\infty \ge 0$ (pois $\mathbb{E}[|X_n|] = \mathbb{E}[X_n] \le \mathbb{E}[X_0] < \infty$).

### Aplicação: processo de ramificação (Galton–Watson)

Seja $Z_0 = 1$ e $Z_{n+1} = \sum_{j=1}^{Z_n} \xi_{n,j}$, onde $\xi_{n,j}$ são cópias i.i.d. em $\mathbb{Z}_+$ com média $\lambda = \mathbb{E}[\xi] \in (0, \infty)$. Então $M_n = \lambda^{-n} Z_n$ é um martingale não negativo e converge q.c. para um limite $M_\infty \in \mathcal{L}^1$:

- **Subcrítico ($\lambda < 1$):** $\mathbb{P}(Z_n \ge 1) \le \mathbb{E}[Z_n] = \lambda^n$, cuja soma converge; pelo 1º Lema de Borel–Cantelli, $Z_n = 0$ eventualmente q.c. (extinção certa).
- **Crítico ($\lambda = 1$, com $\mathbb{P}(\xi = 1) < 1$):** $Z_n = M_n$ converge q.c. para um inteiro $Z_\infty$, o que força extinção q.c. ($\mathbb{P}(Z_n \to 0) = 1$).
- **Supercrítico ($\lambda > 1$):** se $\operatorname{Var}(\xi) < \infty$, então $(M_n)$ é limitado em $\mathcal{L}^2$, donde $M_n \to M_\infty$ em $\mathcal{L}^2$ e em $\mathcal{L}^1$, com $\mathbb{E}[M_\infty] = 1$; logo $\mathbb{P}(M_\infty > 0) > 0$, e no evento $\{M_\infty > 0\}$ a população cresce exponencialmente como $Z_n \sim \lambda^n M_\infty$.

### Integrabilidade uniforme e convergência em $\mathcal{L}^1$ e $\mathcal{L}^p$

A convergência q.c. de um martingale não garante convergência em $\mathcal{L}^1$ (nem que $\mathbb{E}[X_\infty] = \mathbb{E}[X_0]$). A condição exata que fecha essa lacuna é a **integrabilidade uniforme (IU)**: uma família $(X_i)_{i \in I}$ é IU se

$$\lim_{K \to \infty} \sup_{i \in I} \mathbb{E}\!\left[|X_i|\,\mathbf{1}_{\{|X_i| > K\}}\right] = 0.$$

- **Teorema de Vitali:** $X_n \xrightarrow{\mathcal{L}^1} X$ se e somente se $X_n \xrightarrow{\mathbb{P}} X$ e $(X_n)$ é IU.
- **Convergência em $\mathcal{L}^1$ de martingales:** para um martingale $(X_n)$, são equivalentes:
  1. $(X_n)$ é uniformemente integrável;
  2. $X_n$ converge em $\mathcal{L}^1$ (e q.c.) para algum $X_\infty \in \mathcal{L}^1$;
  3. Existe $Z \in \mathcal{L}^1$ tal que $X_n = \mathbb{E}[Z \mid \mathcal{F}_n]$ q.c. para todo $n$ (neste caso, $X_\infty = \mathbb{E}[Z \mid \mathcal{F}_\infty]$ com $\mathcal{F}_\infty = \sigma(\bigcup_n \mathcal{F}_n)$).
- **Convergência em $\mathcal{L}^p$ ($p > 1$):** se $(X_n)$ é martingale limitado em $\mathcal{L}^p$ ($\sup_n \mathbb{E}[|X_n|^p] < \infty$), então $X_n \to X_\infty$ q.c. e em $\mathcal{L}^p$ (consequência da desigualdade maximal em $\mathcal{L}^p$ e TCD).

## 5. Decomposição de Doob e variação quadrática

**Teorema da Decomposição de Doob:** todo processo adaptado e integrável $(X_n)_{n \ge 0}$ admite decomposição única (a menos de equivalência q.c.)

$$X_n = X_0 + M_n + A_n,$$

onde $(M_n)$ é um martingale com $M_0 = 0$ e $(A_n)$ é um processo **previsível** com $A_0 = 0$, chamado **compensador** de $X$:

$$A_n = \sum_{k=1}^{n} \mathbb{E}\!\left[X_k - X_{k-1} \mid \mathcal{F}_{k-1}\right], \qquad M_n = X_n - X_0 - A_n.$$

O processo $(X_n)$ é submartingale se e somente se $(A_n)$ é não decrescente q.c.

### Variação quadrática previsível

Se $(M_n)$ é um martingale em $\mathcal{L}^2$ com $M_0 = 0$, então $(M_n^2)$ é um submartingale. O compensador previsível e não decrescente de $M_n^2$ é a **variação quadrática previsível** $\langle M \rangle_n$:

$$\langle M \rangle_n = \sum_{k=1}^{n} \mathbb{E}\!\left[(M_k - M_{k-1})^2 \mid \mathcal{F}_{k-1}\right],$$

de modo que $M_n^2 - \langle M \rangle_n$ é martingale e $\mathbb{E}[M_n^2] = \mathbb{E}[\langle M \rangle_n]$. Para dois martingales $M, N \in \mathcal{L}^2$, a **covariância quadrática previsível** é $\langle M, N \rangle_n = \sum_{k=1}^n \mathbb{E}[(M_k - M_{k-1})(N_k - N_{k-1}) \mid \mathcal{F}_{k-1}]$, tornando $M_n N_n - \langle M, N \rangle_n$ martingale.

## 6. Transformada martingale e representação no espaço binomial

### Transformada martingale (integral estocástica discreta)

Dado um processo $(X_n)_{n \ge 0}$ e um processo **previsível** $(C_n)_{n \ge 1}$ (interpretado como tamanho da aposta ou quantidade de ações mantidas durante o período $[n-1, n]$), define-se a **transformada martingale** $(C \circ X)$ por $(C \circ X)_0 = 0$ e

$$(C \circ X)_n = \sum_{k=1}^{n} C_k (X_k - X_{k-1}), \qquad n \ge 1.$$

**Propriedade fundamental:** se $(X_n)$ é martingale (resp. supermartingale) e $(C_n)$ é previsível limitado (e não negativo no caso de supermartingale), então $(C \circ X)_n$ também é martingale (resp. supermartingale). Em termos de jogos e mercados, **nenhuma estratégia previsível de alocação cria ganho esperado positivo a partir de um jogo justo ou desfavorável** (*you cannot beat the system*).

### Lema de Representação de Martingales no espaço binomial

Considere o espaço finito $\Omega = \{-1, +1\}^N$ com projeções coordenadas i.i.d. $\xi_1, \dots, \xi_N$, $\mathbb{P}(\xi_n = 1) = p \in (0, 1)$, $\mathbb{P}(\xi_n = -1) = 1 - p$, e filtração natural $\mathcal{F}_n = \sigma(\xi_1, \dots, \xi_n)$ (com $\mathcal{F}_0 = \{\emptyset, \Omega\}$). O processo centrado

$$Z_n = \sum_{k=1}^{n} (\xi_k - (2p - 1)), \qquad Z_0 = 0,$$

é um martingale.

**Lema de Representação:** todo martingale $(M_n)_{0 \le n \le N}$ na filtração $(\mathcal{F}_n)$ admite uma representação única da forma

$$M_n = M_0 + (H \circ Z)_n = M_0 + \sum_{k=1}^{n} H_k (Z_k - Z_{k-1}),$$

onde $(H_k)_{1 \le k \le N}$ é um processo **previsível** dado explicitamente pela sensibilidade do martingale ao salto no passo $k$:

$$H_k(\xi_1, \dots, \xi_{k-1}) = \frac{M_k(\xi_1, \dots, \xi_{k-1}, +1) - M_k(\xi_1, \dots, \xi_{k-1}, -1)}{2}.$$

Esse resultado é o análogo discreto do teorema de representação de martingales para o movimento browniano e explica matematicamente a **completude** do modelo binomial: qualquer pagamento contingente $\mathcal{F}_N$-mensurável pode ser replicado exatamente por uma estratégia previsível.

## 7. Versão em tempo discreto do modelo de Black–Scholes

Considere um mercado discreto com dois ativos nos instantes $n = 0, 1, \dots, N$:

- **Título livre de risco (*bond*):** parte de $B_0 > 0$ com taxa determinística constante $r > -1$ por período:

$$B_n = (1 + r)^n B_0.$$

- **Ativo arriscado (*stock*):** preço positivo adaptado $S_n$, com retorno simples no período $n$ dado por

$$R_n = \frac{S_n - S_{n-1}}{S_{n-1}} \iff S_n = (1 + R_n) S_{n-1}.$$

### Carteira autofinanciada e riqueza descontada

Uma **estratégia de negociação** consiste em um par de processos **previsíveis** $(A_n, V_n)_{n \ge 1}$, onde $A_n$ é a quantidade de unidades do ativo arriscado e $V_n$ a quantidade do título livre de risco escolhidas em $n - 1$ para o período $[n-1, n]$. A riqueza da carteira após a realização dos preços em $n$ é

$$X_n = A_n S_n + V_n B_n, \qquad n \ge 1,$$

com capital inicial $X_0$. A estratégia é **autofinanciada** se o rebalanceamento em $n - 1$ não injeta nem retira recursos externos:

$$A_n S_{n-1} + V_n B_{n-1} = X_{n-1} \qquad (n \ge 1).$$

Substituindo $V_n B_n = (1 + r) V_n B_{n-1} = (1 + r)(X_{n-1} - A_n S_{n-1})$ na expressão de $X_n$, obtém-se a equação de evolução da riqueza nominal:

$$X_n - X_{n-1} = r X_{n-1} + A_n S_{n-1} (R_n - r).$$

Definindo a **riqueza descontada** $Y_n = (1 + r)^{-n} X_n$ e o **preço descontado** $\tilde{S}_n = (1 + r)^{-n} S_n$, a dinâmica simplifica-se para

$$Y_n - Y_{n-1} = (1 + r)^{-n} A_n S_{n-1} (R_n - r) = A_n (\tilde{S}_n - \tilde{S}_{n-1}),$$

ou seja, a riqueza descontada é exatamente a **transformada martingale** do preço descontado pela posição previsível $A$:

$$Y_n = Y_0 + (A \circ \tilde{S})_n.$$

### Ligação com medida neutra ao risco e apreçamento

No modelo binomial em que $R_n \in \{d, u\}$ com $-1 < d < r < u$ (condição de ausência de arbitragem), existe uma única medida de probabilidade equivalente $\mathbb{Q}$ (a **medida neutra ao risco**, com probabilidade de alta $q = \frac{r - d}{u - d} \in (0, 1)$) sob a qual $\mathbb{E}_{\mathbb{Q}}[R_n \mid \mathcal{F}_{n-1}] = r$, tornando $\tilde{S}_n$ um $\mathbb{Q}$-martingale.

Consequentemente:

1. Para toda estratégia autofinanciada, a riqueza descontada $Y_n = Y_0 + (A \circ \tilde{S})_n$ é um $\mathbb{Q}$-martingale.
2. Pelo Lema de Representação no espaço binomial, para qualquer derivativo com pagamento $\mathcal{F}_N$-mensurável $H$ no vencimento $N$, o processo $M_n = \mathbb{E}_{\mathbb{Q}}[(1+r)^{-N} H \mid \mathcal{F}_n]$ admite representação única $M_n = M_0 + (A \circ \tilde{S})_n$, fornecendo simultaneamente:
   - o **preço justo sem arbitragem** em $n = 0$: $V_0 = \mathbb{E}_{\mathbb{Q}}\!\left[(1 + r)^{-N} H\right]$;
   - a **estratégia replicadora (*delta-hedging*)** explícita $A_n = \frac{V_n(\text{alta}) - V_n(\text{baixa})}{S_n(\text{alta}) - S_n(\text{baixa})}$.

No limite contínuo (quando $N \to \infty$ com escala adequada para $r$, $u$ e $d$), o modelo binomial converge para a fórmula contínua de Black–Scholes–Merton.

## Aspectos computacionais

- **Árvores binomiais recombinantes:** quando os fatores multiplicativos $(1 + u)$ e $(1 + d)$ são constantes, o número de nós no passo $n$ cresce linearmente ($n + 1$) em vez de exponencialmente ($2^n$), permitindo apreçar derivativos europeus e americanos por indução retroativa (*backward induction*) em tempo $O(N^2)$ e memória $O(N)$.
- **Verificação numérica de propriedades de martingale:** em simulações de Monte Carlo sob medida neutra ao risco, testar se a média amostral de $\tilde{S}_n$ coincide com $S_0$ dentro do erro padrão $\hat{\sigma}/\sqrt{M}$ é uma checagem direta de implementação correta de esquemas discretos.
- **Precisão de ponto flutuante:** no cálculo de $q = (r - d)/(u - d)$ e de potências $(1 + r)^{-n}$ para $N$ grande, deve-se validar estritamente a condição de não arbitragem $d < r < u$ e usar exponenciação/logaritmo com `log1p`/`expm1` para evitar perda de precisão em passos muito curtos.

## Limitações

- O modelo binomial discreto assume mercado sem atritos (ausência de custos de transação, impostos, *bid-ask spread* e restrições de venda a descoberto), taxa livre de risco constante e liquidez infinita.
- Em mercados incompletos (por exemplo, com mais de dois estados por passo, volatilidade estocástica ou saltos de amplitude aleatória), a medida martingale equivalente não é única e o Lema de Representação deixa de garantir replicação exata.
- Estratégias reais de *hedging* em tempo discreto estão sujeitas a erro de discretização e risco de salto de preço (*gap risk*).

## Referências

- D. Williams. *Probability with Martingales*, cap. 9–15. Cambridge University Press, 1991.
- L. T. Rolla e B. N. B. de Lima. *Probabilidade*, cap. 11–12. Notas de aula / livro aberto, 2021–2026 (CC BY-ND 4.0).
- Notas manuscritas e transcrição sobre Esperança Condicional, Martingais e Black–Scholes em Tempo Discreto (referenciando Williams, cap. 15).
- S. E. Shreve. *Stochastic Calculus for Finance I: The Binomial Asset Pricing Model*. Springer, 2004.

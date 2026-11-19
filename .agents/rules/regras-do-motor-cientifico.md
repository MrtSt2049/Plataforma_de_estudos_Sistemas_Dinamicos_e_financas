---
trigger: manual
---

4. REGRAS DO MOTOR CIENTÍFICO

RULE 013 — Fundamentação matemática

Todo algoritmo científico relevante deve possuir fundamentação matemática.

A implementação deve ser precedida, quando pertinente, por:

Definição.

Formulação.

Hipóteses.

Condições de validade.

Interpretação.

Método computacional.

Limitações.

RULE 014 — Validação numérica

Considere explicitamente:

Precisão de ponto flutuante.

Erros de arredondamento.

Estabilidade numérica.

Condicionamento.

Convergência.

Tolerâncias.

Sensibilidade aos parâmetros.

Não confunda precisão numérica com precisão matemática.

RULE 015 — Vetorização

Priorize operações vetorizadas com NumPy e Pandas quando forem adequadas.

Evite loops Python desnecessários sobre grandes conjuntos de dados.

Não sacrifique clareza ou correção para obter otimizações prematuras.

RULE 016 — Entradas científicas

Valide:

Dimensões.

Tipos.

Valores ausentes.

Valores infinitos.

Domínio matemático.

Ordenação temporal.

Tamanho mínimo de amostras.

Consistência das unidades.

RULE 017 — Reprodutibilidade

Experimentos aleatórios devem permitir o controle da semente.

Registre parâmetros, versões, dados utilizados e configurações relevantes.

RULE 018 — Não inventar resultados

Não produza resultados científicos sem execução ou fundamentação.

Diferencie claramente resultados reais, estimativas, aproximações e exemplos hipotéticos.


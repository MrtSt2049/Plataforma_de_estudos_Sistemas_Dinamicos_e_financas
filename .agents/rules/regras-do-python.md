---
trigger: manual
---

3. REGRAS DE PYTHON

RULE 007 — Versão e ambiente

Utilize Python 3.12 ou superior, respeitando a versão fixada pelo projeto.

Utilize uv para gerenciamento de dependências e ambiente.

Não utilize instalações globais como dependência do projeto.

Registre dependências no pyproject.toml.

Utilize arquivos de lock para reproduzir ambientes.

RULE 008 — Type hints

Utilize tipagem explícita em funções, métodos e interfaces públicas.

Exemplo:

def calculate_returns(
    prices: pd.Series,
) -> pd.Series:
    ...

Evite utilizar Any indiscriminadamente.

RULE 009 — Organização do código

Uma função deve possuir uma responsabilidade clara.

Evite funções excessivamente extensas.

Evite classes sem necessidade.

Prefira composição quando adequada.

Não utilize variáveis com nomes ambíguos.

Evite números mágicos.

Extraia constantes relevantes.

RULE 010 — Tratamento de erros

Utilize exceções específicas.

Valide entradas.

Não esconda erros.

Não utilize except Exception como mecanismo padrão.

Apresente mensagens de erro informativas.

Diferencie erros de validação, infraestrutura e cálculo.

RULE 011 — Docstrings

Funções públicas, classes e módulos relevantes devem possuir documentação.

Explique:

Objetivo.

Parâmetros.

Tipo de retorno.

Exceções.

Restrições.

Referências matemáticas quando aplicáveis.

RULE 012 — Estilo

Utilize Ruff para linting e formatação.

Mantenha consistência de nomenclatura:

snake_case para funções e variáveis.

PascalCase para classes.

UPPER_SNAKE_CASE para constantes.
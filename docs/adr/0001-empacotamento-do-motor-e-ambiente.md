# ADR 0001 — Empacotamento do motor científico e ambiente de desenvolvimento

- **Status:** aceita
- **Data:** 2026-11-19

## Contexto

A Fase 1 cria o primeiro código do QuantLab: o motor científico em `engine/quantlab`. O README já fixa a stack (Python 3.12+, uv, NumPy, Pandas, Pytest, Ruff, Mypy) e a estrutura prevista do repositório, em que o motor fica em `engine/quantlab`, os testes em `tests/` e o backend Django, mais tarde, em `backend/`.

## Problema

Era preciso decidir como o motor vira um pacote Python instalável e reprodutível. A decisão define:

- onde fica o `pyproject.toml`;
- qual backend de build usar;
- o nome de importação do pacote;
- como fixar a versão do Python e das dependências;
- quais regras de lint e tipagem são verificadas.

## Alternativas

1. **`pyproject.toml` na raiz, pacote em `engine/quantlab`.** Um único projeto `quantlab`. O backend de build aponta para o diretório `engine/`. Os testes ficam em `tests/` na raiz, como no README.
2. **`pyproject.toml` dentro de `engine/`** (`engine/pyproject.toml`, `engine/tests/`). O motor fica autocontido, mas a estrutura diverge do README e os comandos passam a ser rodados de dentro de `engine/`.
3. **Workspace do uv** com membros `engine/` e, depois, `backend/`. Resolve bem vários pacotes, mas hoje só existe um. Seria uma abstração antecipada (RULE 005).

Para o build, as opções consideradas foram o **Hatchling**, maduro e independente do uv, e o **uv_build**, nativo do uv mas com a versão do backend acoplada à versão do uv.

## Decisão

- Adotar a alternativa 1: `pyproject.toml` na raiz, pacote em `engine/quantlab`, importado como `quantlab`.
- Usar o **Hatchling** como backend de build (`packages = ["engine/quantlab"]`).
- Exigir `requires-python = ">=3.12"` e fixar o ambiente de desenvolvimento em Python 3.13 (`.python-version`).
- Versionar o `uv.lock` para reproduzir o ambiente exato (RULE 007).
- Dependências de execução: apenas `numpy` e `pandas`. SciPy, SymPy, DuckDB e as bibliotecas de visualização entram quando um módulo precisar delas.
- Dependências de desenvolvimento num grupo `dev`: `pytest`, `pytest-cov`, `ruff`, `mypy`, `pandas-stubs`.
- Mypy em modo `strict`. Ruff com docstrings no padrão NumPy (RULE 011) e checagem de números mágicos (RULE 009).
- Pytest com `filterwarnings = error`: avisos numéricos do NumPy (overflow, divisão por zero, valor inválido) fazem o teste falhar.
- A independência do motor (RULE 002) é verificada por teste (`tests/test_architecture.py`), que analisa os imports de todos os módulos do pacote.

## Justificativa

A alternativa 1 é a única que mantém exatamente a estrutura publicada no README sem introduzir camadas novas. O nome de importação `quantlab` não depende do diretório físico, então mover o motor no futuro não quebra quem o usa. O Hatchling evita prender o build a uma versão específica do uv.

## Consequências

- Os comandos rodam a partir da raiz: `uv sync`, `uv run pytest`, `uv run ruff check .`, `uv run mypy`.
- Quando o backend Django for criado (Fase 4), ele será outro projeto Python. Será preciso decidir, em novo ADR, entre um workspace do uv ou um `pyproject.toml` separado em `backend/` que depende do `quantlab`.
- O `filterwarnings = error` obriga cada operação que gera aviso de forma intencional (por exemplo `log1p(-1)` para perda total) a declarar isso com `np.errstate`. Isso é desejado: nenhum aviso numérico passa despercebido.

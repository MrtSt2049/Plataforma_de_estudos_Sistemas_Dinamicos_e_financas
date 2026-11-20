"""Architectural constraints of the scientific engine (RULE 002)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

import quantlab
from quantlab.exceptions import DomainError, InputValidationError, InsufficientDataError

ENGINE_ROOT = Path(quantlab.__file__).parent

FORBIDDEN_TOP_LEVEL_PACKAGES = {
    "django",
    "rest_framework",
    "drf_spectacular",
    "supabase",
    "postgrest",
    "gotrue",
    "requests",
    "httpx",
    "aiohttp",
    "urllib3",
    "flask",
    "fastapi",
    "celery",
    "redis",
    # Network clients and connectors live outside the engine (docs/adr/0005):
    # the engine never imports them, the connectors import the engine.
    "yfinance",
    "curl_cffi",
    "quantlab_connectors",
}


def _imported_top_level_packages(source: Path) -> set[str]:
    tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    packages: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            packages.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            packages.add(node.module.split(".")[0])
    return packages


ENGINE_MODULES = sorted(ENGINE_ROOT.rglob("*.py"))


def test_engine_modules_were_found() -> None:
    """Guards against a wrong ENGINE_ROOT, which would make the import check vacuous."""
    assert (ENGINE_ROOT / "__init__.py") in ENGINE_MODULES


@pytest.mark.parametrize(
    "module", ENGINE_MODULES, ids=lambda p: p.relative_to(ENGINE_ROOT).as_posix()
)
def test_engine_does_not_import_application_layers(module: Path) -> None:
    forbidden = _imported_top_level_packages(module) & FORBIDDEN_TOP_LEVEL_PACKAGES
    assert not forbidden, f"{module.name} imports {sorted(forbidden)}"


def test_validation_errors_are_value_errors() -> None:
    """Callers that only know the built-in ValueError still catch engine validation errors."""
    for error in (InputValidationError, InsufficientDataError, DomainError):
        assert issubclass(error, ValueError)

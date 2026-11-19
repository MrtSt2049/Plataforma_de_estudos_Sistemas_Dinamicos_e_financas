"""Linear stability of equilibria of continuous-time systems."""

from __future__ import annotations

import math

import numpy as np
import pytest

from quantlab.dynamics import (
    Equilibrium,
    FixedPointStability,
    analyze_equilibrium,
    classify_flow_equilibrium,
)
from quantlab.exceptions import InputValidationError

# --- classify_flow_equilibrium -------------------------------------------------------------------


@pytest.mark.parametrize(
    ("eigenvalues", "expected"),
    [
        ([-1.0, -2.0], FixedPointStability.STABLE),
        ([-0.1 + 3j, -0.1 - 3j], FixedPointStability.STABLE),  # stable focus
        ([1.0, -2.0], FixedPointStability.UNSTABLE),  # saddle
        ([0.2 + 1j, 0.2 - 1j], FixedPointStability.UNSTABLE),  # unstable focus
        ([1j, -1j], FixedPointStability.NON_HYPERBOLIC),  # linear centre
        ([0.0, -1.0], FixedPointStability.NON_HYPERBOLIC),
        ([0.0, 1.0], FixedPointStability.UNSTABLE),  # a positive real part decides
        ([-5.0], FixedPointStability.STABLE),
    ],
)
def test_classification(eigenvalues: list[complex], expected: FixedPointStability) -> None:
    assert classify_flow_equilibrium(eigenvalues) is expected


def test_real_parts_within_tolerance_count_as_zero() -> None:
    assert classify_flow_equilibrium([5e-11, -1.0]) is FixedPointStability.NON_HYPERBOLIC
    assert classify_flow_equilibrium([-5e-11, -1.0]) is FixedPointStability.NON_HYPERBOLIC
    assert classify_flow_equilibrium([5e-11, -1.0], atol=0.0) is FixedPointStability.UNSTABLE


@pytest.mark.parametrize("bad", [[], [[1.0, 2.0]], [math.nan], [complex(math.inf, 0.0)]])
def test_rejects_invalid_eigenvalues(bad: object) -> None:
    with pytest.raises(InputValidationError, match="eigenvalues"):
        classify_flow_equilibrium(bad)  # type: ignore[arg-type]


def test_rejects_non_numeric_eigenvalues() -> None:
    with pytest.raises(TypeError, match="eigenvalues"):
        classify_flow_equilibrium(["a", "b"])


@pytest.mark.parametrize("atol", [-1e-9, math.nan])
def test_rejects_invalid_tolerance(atol: float) -> None:
    with pytest.raises(InputValidationError, match="atol"):
        classify_flow_equilibrium([-1.0], atol=atol)


# --- analyze_equilibrium -------------------------------------------------------------------------


def test_damped_oscillator_is_a_stable_focus() -> None:
    # x'' + 2 zeta w x' + w^2 x = 0 has eigenvalues -zeta w +- i w sqrt(1 - zeta^2).
    omega, zeta = 2.0, 0.25
    jacobian = [[0.0, 1.0], [-(omega**2), -2.0 * zeta * omega]]
    equilibrium = analyze_equilibrium([0.0, 0.0], jacobian)
    imaginary = omega * math.sqrt(1.0 - zeta**2)
    np.testing.assert_allclose(
        equilibrium.eigenvalues,
        [complex(-zeta * omega, imaginary), complex(-zeta * omega, -imaginary)],
        atol=1e-14,
    )
    assert equilibrium.stability is FixedPointStability.STABLE


def test_eigenvalues_are_sorted_by_real_then_imaginary_part() -> None:
    # Block diagonal: three real eigenvalues and a rotation block with eigenvalues +-4i.
    block = np.zeros((5, 5))
    block[:3, :3] = np.diag([-3.0, 2.0, -1.0])
    block[3:, 3:] = [[0.0, -4.0], [4.0, 0.0]]
    equilibrium = analyze_equilibrium(np.zeros(5), block)
    assert equilibrium.eigenvalues == pytest.approx([2.0, 4j, -4j, -1.0, -3.0], abs=1e-14)
    assert equilibrium.stability is FixedPointStability.UNSTABLE


def test_returns_plain_python_values() -> None:
    equilibrium = analyze_equilibrium(np.array([1, 2]), np.array([[-1, 0], [0, -2]]))
    assert equilibrium == Equilibrium(
        location=(1.0, 2.0),
        eigenvalues=(complex(-1.0), complex(-2.0)),
        stability=FixedPointStability.STABLE,
    )
    assert all(type(coordinate) is float for coordinate in equilibrium.location)
    assert all(type(value) is complex for value in equilibrium.eigenvalues)


@pytest.mark.parametrize(
    ("location", "jacobian", "match"),
    [
        ([], [[1.0]], "location"),
        ([[0.0, 0.0]], [[1.0]], "location"),
        ([0.0, 0.0], [[1.0, 0.0]], r"jacobian must have shape \(2, 2\)"),
        ([0.0], [[math.nan]], "finite"),
        ([math.inf], [[1.0]], "finite"),
    ],
)
def test_rejects_invalid_shapes_and_values(location: object, jacobian: object, match: str) -> None:
    with pytest.raises(InputValidationError, match=match):
        analyze_equilibrium(location, jacobian)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("location", "jacobian"),
    [(["a"], [[1.0]]), ([0.0], [[1j]]), ([True], [[1.0]])],
)
def test_rejects_non_real_input(location: object, jacobian: object) -> None:
    with pytest.raises(TypeError, match="real numbers"):
        analyze_equilibrium(location, jacobian)  # type: ignore[arg-type]

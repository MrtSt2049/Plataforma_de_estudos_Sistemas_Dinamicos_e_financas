"""The logistic bifurcation diagram, checked against single orbits and analytic cycles."""

from __future__ import annotations

import math

import numpy as np
import pytest

from quantlab.dynamics import logistic_bifurcation_diagram, simulate_logistic_map
from quantlab.exceptions import DomainError, InputValidationError


def test_shape_and_dtype() -> None:
    diagram = logistic_bifurcation_diagram([2.5, 3.2, 3.9], 0.2, n_transient=10, n_samples=7)
    assert diagram.shape == (3, 7)
    assert diagram.dtype == np.float64


@pytest.mark.parametrize(("n_transient", "n_samples"), [(0, 1), (0, 5), (100, 1), (300, 50)])
def test_rows_equal_single_orbits_bit_for_bit(n_transient: int, n_samples: int) -> None:
    r_values = np.linspace(2.5, 4.0, 13)
    diagram = logistic_bifurcation_diagram(
        r_values, 0.2, n_transient=n_transient, n_samples=n_samples
    )
    for row, r in zip(diagram, r_values, strict=True):
        orbit = simulate_logistic_map(float(r), 0.2, n_transient + n_samples - 1)[n_transient:]
        np.testing.assert_array_equal(row, orbit)


def test_zero_transient_starts_at_the_initial_state() -> None:
    diagram = logistic_bifurcation_diagram([3.0, 3.7], 0.3, n_transient=0, n_samples=3)
    np.testing.assert_array_equal(diagram[:, 0], [0.3, 0.3])


@pytest.mark.parametrize("r", [1.5, 2.5, 2.9])
def test_stable_fixed_point_gives_a_single_value(r: float) -> None:
    (row,) = logistic_bifurcation_diagram([r], 0.2, n_transient=5_000, n_samples=50)
    np.testing.assert_allclose(row, 1.0 - 1.0 / r, atol=1e-12)


def test_two_cycle_gives_the_two_analytic_values() -> None:
    r = 3.2
    root = math.sqrt((r - 3.0) * (r + 1.0))
    expected = [((r + 1.0) - root) / (2.0 * r), ((r + 1.0) + root) / (2.0 * r)]
    (row,) = logistic_bifurcation_diagram([r], 0.2, n_transient=5_000, n_samples=50)
    np.testing.assert_allclose(np.unique(np.round(row, 12)), expected, atol=1e-12)


def test_chaotic_samples_fill_the_unit_interval() -> None:
    (row,) = logistic_bifurcation_diagram([4.0], 0.1234, n_transient=1_000, n_samples=20_000)
    assert row.min() >= 0.0
    assert row.max() <= 1.0
    # The invariant density at r = 4 has support [0, 1]: every tenth of the interval is visited.
    counts, _ = np.histogram(row, bins=10, range=(0.0, 1.0))
    assert counts.min() > 0


@pytest.mark.parametrize("r_values", [[], [[3.0, 3.5]], [3.0, math.nan], [math.inf]])
def test_rejects_invalid_r_values(r_values: object) -> None:
    with pytest.raises(InputValidationError, match="r_values"):
        logistic_bifurcation_diagram(r_values, 0.2)  # type: ignore[arg-type]


@pytest.mark.parametrize("r_values", [[3.0, 4.1], [-0.5, 2.0]])
def test_rejects_r_outside_the_domain(r_values: list[float]) -> None:
    with pytest.raises(DomainError, match=r"r_values must lie in \[0.0, 4.0\]; found 1 value"):
        logistic_bifurcation_diagram(r_values, 0.2)


def test_rejects_invalid_initial_state_and_counts() -> None:
    with pytest.raises(DomainError, match="x0"):
        logistic_bifurcation_diagram([3.0], 1.5)
    with pytest.raises(InputValidationError, match="n_transient"):
        logistic_bifurcation_diagram([3.0], 0.2, n_transient=-1)
    with pytest.raises(InputValidationError, match="n_samples"):
        logistic_bifurcation_diagram([3.0], 0.2, n_samples=0)

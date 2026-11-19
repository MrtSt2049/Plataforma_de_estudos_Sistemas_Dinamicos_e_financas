from __future__ import annotations

import math

import numpy as np
import pytest

from quantlab.dynamics import (
    FixedPointStability,
    detect_period,
    logistic_derivative,
    logistic_fixed_points,
    logistic_lyapunov_exponent,
    logistic_map,
    simulate_logistic_map,
)
from quantlab.exceptions import DomainError, InputValidationError

TRANSIENT = 20_000
WINDOW = 2_000


def attractor_sample(r: float, x0: float = 0.2) -> np.ndarray:
    """Orbit points after the transient has been discarded."""
    return simulate_logistic_map(r, x0, TRANSIENT + WINDOW)[TRANSIENT:]


# --- the map itself ------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("x", "r", "expected"),
    [(0.5, 4.0, 1.0), (0.0, 3.7, 0.0), (1.0, 3.7, 0.0), (0.2, 3.0, 0.48), (0.5, 0.0, 0.0)],
)
def test_logistic_map_known_values(x: float, r: float, expected: float) -> None:
    assert logistic_map(x, r) == pytest.approx(expected, abs=1e-15)


def test_derivative_known_values() -> None:
    assert logistic_derivative(0.5, 3.7) == 0.0
    assert logistic_derivative(0.0, 3.7) == pytest.approx(3.7)
    assert logistic_derivative(1.0, 3.7) == pytest.approx(-3.7)


@pytest.mark.parametrize("r", [-0.1, 4.0001])
def test_rejects_r_outside_domain(r: float) -> None:
    with pytest.raises(DomainError, match=r"r must lie in \[0.0, 4.0\]"):
        logistic_map(0.5, r)


@pytest.mark.parametrize("x", [-1e-12, 1.5])
def test_rejects_state_outside_domain(x: float) -> None:
    with pytest.raises(DomainError, match="x must lie"):
        logistic_map(x, 3.0)


@pytest.mark.parametrize("bad", [math.nan, math.inf])
def test_rejects_non_finite_parameters(bad: float) -> None:
    with pytest.raises(InputValidationError, match="finite"):
        logistic_map(0.5, bad)
    with pytest.raises(InputValidationError, match="finite"):
        simulate_logistic_map(3.0, bad, 10)


@pytest.mark.parametrize("bad", ["3.0", True, None])
def test_rejects_non_numeric_parameters(bad: object) -> None:
    with pytest.raises(TypeError):
        logistic_map(0.5, bad)  # type: ignore[arg-type]


# --- simulation ----------------------------------------------------------------------------------


def test_simulation_shape_and_recurrence() -> None:
    orbit = simulate_logistic_map(3.7, 0.3, 50)
    assert orbit.shape == (51,)
    assert orbit.dtype == np.float64
    assert orbit[0] == 0.3
    np.testing.assert_array_equal(orbit[1:], 3.7 * orbit[:-1] * (1.0 - orbit[:-1]))


def test_zero_steps_returns_initial_state() -> None:
    np.testing.assert_array_equal(simulate_logistic_map(3.0, 0.4, 0), [0.4])


def test_simulation_is_deterministic() -> None:
    np.testing.assert_array_equal(
        simulate_logistic_map(3.9, 0.123, 5_000), simulate_logistic_map(3.9, 0.123, 5_000)
    )


def test_orbit_stays_in_unit_interval_at_r_max() -> None:
    orbit = simulate_logistic_map(4.0, 0.1234, 100_000)
    assert orbit.min() >= 0.0
    assert orbit.max() <= 1.0


@pytest.mark.parametrize("n_steps", [-1])
def test_rejects_negative_steps(n_steps: int) -> None:
    with pytest.raises(InputValidationError, match="n_steps"):
        simulate_logistic_map(3.0, 0.5, n_steps)


@pytest.mark.parametrize("n_steps", [10.0, True])
def test_rejects_non_integer_steps(n_steps: object) -> None:
    with pytest.raises(TypeError, match="n_steps"):
        simulate_logistic_map(3.0, 0.5, n_steps)  # type: ignore[arg-type]


# --- fixed points and stability (analytic results) -----------------------------------------------


def test_only_the_origin_exists_and_is_stable_below_r_one() -> None:
    (origin,) = logistic_fixed_points(0.5)
    assert origin.location == 0.0
    assert origin.multiplier == 0.5
    assert origin.stability is FixedPointStability.STABLE


def test_origin_is_non_hyperbolic_at_r_one() -> None:
    (origin,) = logistic_fixed_points(1.0)
    assert origin.stability is FixedPointStability.NON_HYPERBOLIC


@pytest.mark.parametrize("r", [1.1, 1.5, 2.0, 2.5, 2.9])
def test_nontrivial_fixed_point_is_stable_between_one_and_three(r: float) -> None:
    origin, nontrivial = logistic_fixed_points(r)
    assert origin.stability is FixedPointStability.UNSTABLE
    assert nontrivial.location == pytest.approx(1.0 - 1.0 / r, rel=1e-15)
    assert nontrivial.multiplier == pytest.approx(2.0 - r, abs=1e-14)
    assert nontrivial.stability is FixedPointStability.STABLE


def test_first_period_doubling_is_non_hyperbolic_at_r_three() -> None:
    _, nontrivial = logistic_fixed_points(3.0)
    assert nontrivial.location == pytest.approx(2.0 / 3.0)
    assert nontrivial.stability is FixedPointStability.NON_HYPERBOLIC


@pytest.mark.parametrize("r", [3.2, 3.5, 4.0])
def test_nontrivial_fixed_point_is_unstable_above_three(r: float) -> None:
    _, nontrivial = logistic_fixed_points(r)
    assert nontrivial.stability is FixedPointStability.UNSTABLE


@pytest.mark.parametrize(("r", "expected"), [(0.5, 0.0), (2.5, 0.6), (2.9, 1.0 - 1.0 / 2.9)])
def test_simulation_converges_to_the_stable_fixed_point(r: float, expected: float) -> None:
    assert simulate_logistic_map(r, 0.1, 5_000)[-1] == pytest.approx(expected, abs=1e-12)


def test_simulation_converges_to_the_analytic_two_cycle() -> None:
    r = 3.2
    root = math.sqrt((r - 3.0) * (r + 1.0))
    expected = sorted([((r + 1.0) - root) / (2.0 * r), ((r + 1.0) + root) / (2.0 * r)])
    np.testing.assert_allclose(sorted(attractor_sample(r)[-2:]), expected, atol=1e-14)


# --- period doubling and chaos -------------------------------------------------------------------


@pytest.mark.parametrize(
    ("r", "period"),
    [
        (2.8, 1),  # stable fixed point
        (3.2, 2),  # after the first doubling at r = 3
        (3.5, 4),  # after the second doubling at r = 1 + sqrt(6)
        (3.555, 8),  # third doubling, close to the accumulation point
        (3.835, 3),  # period-3 window inside the chaotic region
    ],
)
def test_period_doubling_cascade(r: float, period: int) -> None:
    assert detect_period(attractor_sample(r), max_period=64, atol=1e-9) == period


@pytest.mark.parametrize("r", [3.9, 4.0])
def test_chaotic_orbits_have_no_short_period(r: float) -> None:
    assert detect_period(attractor_sample(r), max_period=64, atol=1e-9) is None


def test_lyapunov_exponent_at_r_four_is_ln_two() -> None:
    estimate = logistic_lyapunov_exponent(4.0, 0.1234, n_steps=200_000)
    assert estimate == pytest.approx(math.log(2.0), abs=5e-3)


@pytest.mark.parametrize("r", [0.5, 2.5])
def test_lyapunov_exponent_of_stable_fixed_point_is_log_multiplier(r: float) -> None:
    multiplier = r if r < 1.0 else 2.0 - r
    estimate = logistic_lyapunov_exponent(r, 0.2, n_transient=2_000, n_steps=10_000)
    assert estimate == pytest.approx(math.log(abs(multiplier)), rel=1e-9)


def test_lyapunov_exponent_of_two_cycle_matches_analytic_value() -> None:
    # The 2-cycle multiplier is f'(x+) f'(x-) = 4 + 2r - r^2, so lambda = ln|4 + 2r - r^2| / 2.
    r = 3.2
    expected = 0.5 * math.log(abs(4.0 + 2.0 * r - r * r))
    estimate = logistic_lyapunov_exponent(r, 0.2, n_transient=5_000, n_steps=10_000)
    assert estimate == pytest.approx(expected, rel=1e-9)


def test_lyapunov_exponent_is_positive_in_the_chaotic_region() -> None:
    assert logistic_lyapunov_exponent(3.9, 0.2) > 0.1


def test_lyapunov_exponent_approaches_zero_at_bifurcation() -> None:
    assert abs(logistic_lyapunov_exponent(3.0, 0.2, n_steps=200_000)) < 1e-3


def test_superstable_orbit_has_minus_infinite_exponent() -> None:
    # At r = 2 the fixed point is x = 1/2, where the derivative vanishes.
    assert logistic_lyapunov_exponent(2.0, 0.1) == -math.inf


def test_lyapunov_rejects_zero_steps() -> None:
    with pytest.raises(InputValidationError, match="n_steps"):
        logistic_lyapunov_exponent(3.9, 0.2, n_steps=0)


def test_lyapunov_rejects_negative_transient() -> None:
    with pytest.raises(InputValidationError, match="n_transient"):
        logistic_lyapunov_exponent(3.9, 0.2, n_transient=-1)

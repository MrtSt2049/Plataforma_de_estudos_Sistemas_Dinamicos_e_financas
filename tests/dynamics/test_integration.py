"""Generic integration of autonomous ODEs, checked against exact solutions."""

from __future__ import annotations

import math
from types import SimpleNamespace
from typing import get_args

import numpy as np
import numpy.typing as npt
import pytest

import quantlab.dynamics.integration as integration
from quantlab.dynamics import ODE_METHODS, OdeMethod, Trajectory
from quantlab.dynamics.integration import MIN_RTOL, integrate_autonomous
from quantlab.exceptions import ComputationError, DomainError, InputValidationError

Array = npt.NDArray[np.float64]


def decay(state: Array) -> Array:
    return -0.7 * state


def oscillator(state: Array) -> Array:
    """x'' = -x as a first-order system; exact solution (cos t, -sin t) from (1, 0)."""
    return np.array([state[1], -state[0]])


def oscillator_jacobian(state: Array) -> Array:
    del state
    return np.array([[0.0, 1.0], [-1.0, 0.0]])


# --- accuracy against exact solutions ------------------------------------------------------------


@pytest.mark.parametrize("method", ODE_METHODS)
def test_exponential_decay_matches_exact_solution(method: OdeMethod) -> None:
    trajectory = integrate_autonomous(decay, [2.0, -1.0], n_steps=50, dt=0.1, method=method)
    exact = np.outer(np.exp(-0.7 * trajectory.times), [2.0, -1.0])
    np.testing.assert_allclose(trajectory.states, exact, rtol=1e-8, atol=1e-11)


@pytest.mark.parametrize("method", ODE_METHODS)
def test_harmonic_oscillator_matches_exact_solution(method: OdeMethod) -> None:
    trajectory = integrate_autonomous(
        oscillator, [1.0, 0.0], n_steps=100, dt=0.1, method=method, jacobian=oscillator_jacobian
    )
    exact = np.column_stack([np.cos(trajectory.times), -np.sin(trajectory.times)])
    np.testing.assert_allclose(trajectory.states, exact, atol=1e-8)
    energy = np.sum(trajectory.states**2, axis=1)
    np.testing.assert_allclose(energy, 1.0, atol=1e-8)


def test_sampling_interval_does_not_change_the_solution() -> None:
    fine = integrate_autonomous(oscillator, [1.0, 0.0], n_steps=100, dt=0.05)
    coarse = integrate_autonomous(oscillator, [1.0, 0.0], n_steps=10, dt=0.5)
    np.testing.assert_allclose(coarse.states, fine.states[::10], atol=1e-9)


# --- the Trajectory record -----------------------------------------------------------------------


def test_trajectory_shape_grid_and_settings() -> None:
    trajectory = integrate_autonomous(
        decay, [1.0, 2.0, 3.0], n_steps=20, dt=0.25, method="RK45", rtol=1e-8, atol=1e-10
    )
    assert trajectory.times.shape == (21,)
    assert trajectory.states.shape == (21, 3)
    np.testing.assert_array_equal(trajectory.times, 0.25 * np.arange(21))
    np.testing.assert_array_equal(trajectory.states[0], [1.0, 2.0, 3.0])
    assert (trajectory.method, trajectory.rtol, trajectory.atol) == ("RK45", 1e-8, 1e-10)
    assert trajectory.n_evaluations > 0


def test_zero_steps_returns_the_initial_state_without_integrating() -> None:
    def never_called(state: Array) -> Array:
        raise AssertionError("the vector field must not be evaluated")

    trajectory = integrate_autonomous(never_called, [1.5, -2.0], n_steps=0, dt=0.1)
    np.testing.assert_array_equal(trajectory.times, [0.0])
    np.testing.assert_array_equal(trajectory.states, [[1.5, -2.0]])
    assert trajectory.n_evaluations == 0


@pytest.mark.parametrize("n_steps", [0, 5])
def test_arrays_are_read_only(n_steps: int) -> None:
    trajectory = integrate_autonomous(decay, [1.0], n_steps=n_steps, dt=0.1)
    with pytest.raises(ValueError, match="read-only"):
        trajectory.states[0, 0] = 99.0
    with pytest.raises(ValueError, match="read-only"):
        trajectory.times[0] = 99.0


def test_initial_state_is_copied() -> None:
    initial = np.array([1.0, 0.0])
    trajectory = integrate_autonomous(oscillator, initial, n_steps=0, dt=0.1)
    initial[0] = 5.0
    assert trajectory.states[0, 0] == 1.0


def test_is_deterministic() -> None:
    first = integrate_autonomous(oscillator, [1.0, 0.0], n_steps=50, dt=0.2)
    second = integrate_autonomous(oscillator, [1.0, 0.0], n_steps=50, dt=0.2)
    np.testing.assert_array_equal(first.states, second.states)
    assert first.n_evaluations == second.n_evaluations


# --- the Jacobian is only used by implicit methods -----------------------------------------------


def test_radau_uses_the_supplied_jacobian() -> None:
    calls = 0

    def counted_jacobian(state: Array) -> Array:
        nonlocal calls
        calls += 1
        return oscillator_jacobian(state)

    integrate_autonomous(
        oscillator, [1.0, 0.0], n_steps=10, dt=0.1, method="Radau", jacobian=counted_jacobian
    )
    assert calls > 0


@pytest.mark.parametrize("method", ["DOP853", "RK45"])
def test_explicit_methods_ignore_the_jacobian_without_warning(method: OdeMethod) -> None:
    def failing_jacobian(state: Array) -> Array:
        raise AssertionError("explicit methods must not evaluate the Jacobian")

    # Pytest turns warnings into errors, so SciPy's "unused argument" warning would fail here.
    integrate_autonomous(
        oscillator, [1.0, 0.0], n_steps=10, dt=0.1, method=method, jacobian=failing_jacobian
    )


def test_radau_without_jacobian_uses_finite_differences() -> None:
    trajectory = integrate_autonomous(oscillator, [1.0, 0.0], n_steps=10, dt=0.1, method="Radau")
    np.testing.assert_allclose(trajectory.states[-1], [math.cos(1.0), -math.sin(1.0)], atol=1e-8)


def test_method_names_match_the_literal_type() -> None:
    assert set(ODE_METHODS) == set(get_args(OdeMethod.__value__))


# --- failures ------------------------------------------------------------------------------------


def test_blow_up_in_finite_time_raises_computation_error() -> None:
    # x' = x^2 from x(0) = 1 has the exact solution 1 / (1 - t), which diverges at t = 1.
    with pytest.raises(ComputationError, match="DOP853 failed"):
        integrate_autonomous(lambda state: state**2, [1.0], n_steps=20, dt=0.1)


def test_non_finite_solver_output_raises_computation_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_solver(*args: object, **kwargs: object) -> SimpleNamespace:
        return SimpleNamespace(success=True, y=np.array([[1.0, math.nan]]), nfev=3)

    monkeypatch.setattr(integration, "solve_ivp", fake_solver)
    with pytest.raises(ComputationError, match="non-finite"):
        integrate_autonomous(decay, [1.0], n_steps=1, dt=0.1)


# --- input validation ----------------------------------------------------------------------------


@pytest.mark.parametrize(
    "initial_state",
    [[], [[1.0, 2.0]], [1.0, math.nan], [math.inf], [[1.0], [2.0, 3.0]]],
)
def test_rejects_invalid_initial_state(initial_state: object) -> None:
    with pytest.raises(InputValidationError, match="initial_state"):
        integrate_autonomous(decay, initial_state, n_steps=1, dt=0.1)  # type: ignore[arg-type]


@pytest.mark.parametrize("initial_state", [["1.0"], [True, False], [1.0 + 2j], None])
def test_rejects_non_real_initial_state(initial_state: object) -> None:
    with pytest.raises(TypeError, match="initial_state must contain real numbers"):
        integrate_autonomous(decay, initial_state, n_steps=1, dt=0.1)  # type: ignore[arg-type]


def test_rejects_unknown_method() -> None:
    with pytest.raises(InputValidationError, match="method must be one of"):
        integrate_autonomous(decay, [1.0], n_steps=1, dt=0.1, method="Euler")  # type: ignore[arg-type]


def test_rejects_non_string_method() -> None:
    with pytest.raises(TypeError, match="method must be a string"):
        integrate_autonomous(decay, [1.0], n_steps=1, dt=0.1, method=45)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("options", "error", "match"),
    [
        ({"dt": 0.0}, DomainError, "dt"),
        ({"dt": -0.1}, DomainError, "dt"),
        ({"dt": math.inf}, InputValidationError, "dt"),
        ({"n_steps": -1}, InputValidationError, "n_steps"),
        ({"n_steps": 2.0}, TypeError, "n_steps"),
        ({"rtol": 0.0}, DomainError, "rtol"),
        ({"rtol": MIN_RTOL / 2}, DomainError, "100 machine epsilons"),
        ({"atol": 0.0}, DomainError, "atol"),
        ({"atol": "1e-9"}, TypeError, "atol"),
    ],
)
def test_rejects_invalid_settings(
    options: dict[str, object], error: type[Exception], match: str
) -> None:
    settings: dict[str, object] = {"n_steps": 1, "dt": 0.1, **options}
    with pytest.raises(error, match=match):
        integrate_autonomous(decay, [1.0], **settings)  # type: ignore[arg-type]


def test_rejects_an_infinite_time_horizon() -> None:
    with pytest.raises(DomainError, match="not finite"):
        integrate_autonomous(decay, [1.0], n_steps=10, dt=1e308)


def test_rejects_non_callable_functions() -> None:
    with pytest.raises(TypeError, match="vector_field must be callable"):
        integrate_autonomous([1.0], [1.0], n_steps=1, dt=0.1)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="jacobian must be callable"):
        integrate_autonomous(decay, [1.0], n_steps=1, dt=0.1, jacobian=np.eye(1))  # type: ignore[arg-type]


def test_min_rtol_is_accepted() -> None:
    trajectory = integrate_autonomous(decay, [1.0], n_steps=2, dt=0.1, rtol=MIN_RTOL)
    assert isinstance(trajectory, Trajectory)
    assert trajectory.rtol == MIN_RTOL

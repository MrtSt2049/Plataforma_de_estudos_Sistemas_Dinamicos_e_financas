"""The Lorenz system, checked against analytic results (see docs/math/sistema-lorenz.md)."""

from __future__ import annotations

import dataclasses
import math

import numpy as np
import numpy.typing as npt
import pytest

from quantlab.dynamics import (
    BETA_CANONICAL,
    CANONICAL_PARAMETERS,
    RHO_CANONICAL,
    SIGMA_CANONICAL,
    FixedPointStability,
    LorenzParameters,
    lorenz_fixed_points,
    lorenz_hopf_rho,
    lorenz_jacobian,
    lorenz_vector_field,
    simulate_lorenz,
)
from quantlab.exceptions import DomainError, InputValidationError

Array = npt.NDArray[np.float64]

STABLE = FixedPointStability.STABLE
UNSTABLE = FixedPointStability.UNSTABLE
NON_HYPERBOLIC = FixedPointStability.NON_HYPERBOLIC


def characteristic_roots(parameters: LorenzParameters) -> npt.NDArray[np.complex128]:
    """Roots of the characteristic polynomial at C+-, computed independently of the Jacobian."""
    sigma, rho, beta = parameters.sigma, parameters.rho, parameters.beta
    coefficients = [1.0, sigma + beta + 1.0, beta * (sigma + rho), 2.0 * sigma * beta * (rho - 1.0)]
    return np.roots(coefficients).astype(np.complex128)


def sort_complex(values: npt.ArrayLike) -> list[complex]:
    return sorted((complex(v) for v in np.asarray(values)), key=lambda v: (-v.real, -v.imag))


# --- parameters ----------------------------------------------------------------------------------


def test_canonical_parameters() -> None:
    assert LorenzParameters() == CANONICAL_PARAMETERS
    assert (SIGMA_CANONICAL, RHO_CANONICAL, BETA_CANONICAL) == (10.0, 28.0, 8.0 / 3.0)
    assert dataclasses.astuple(CANONICAL_PARAMETERS) == (10.0, 28.0, 8.0 / 3.0)


def test_parameters_are_stored_as_floats() -> None:
    parameters = LorenzParameters(sigma=10, rho=28, beta=3)
    assert all(type(value) is float for value in dataclasses.astuple(parameters))


def test_parameters_are_immutable() -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        CANONICAL_PARAMETERS.rho = 10.0  # type: ignore[misc]


@pytest.mark.parametrize("name", ["sigma", "rho", "beta"])
@pytest.mark.parametrize("value", [0.0, -1.0])
def test_parameters_must_be_positive(name: str, value: float) -> None:
    with pytest.raises(DomainError, match=f"{name} must be strictly positive"):
        LorenzParameters(**{name: value})


@pytest.mark.parametrize("name", ["sigma", "rho", "beta"])
def test_parameters_must_be_finite_real_numbers(name: str) -> None:
    with pytest.raises(InputValidationError, match=f"{name} must be finite"):
        LorenzParameters(**{name: math.nan})
    with pytest.raises(TypeError, match=f"{name} must be a real number"):
        LorenzParameters(**{name: "10"})  # type: ignore[arg-type]


# --- vector field and Jacobian -------------------------------------------------------------------


def test_vector_field_known_value() -> None:
    # At (1, 1, 1): sigma (1 - 1) = 0, 1 (28 - 1) - 1 = 26, 1 - 8/3 = -5/3.
    np.testing.assert_allclose(lorenz_vector_field([1.0, 1.0, 1.0]), [0.0, 26.0, -5.0 / 3.0])


def test_vector_field_respects_the_symmetry_exactly(rng: np.random.Generator) -> None:
    for x, y, z in rng.normal(scale=10.0, size=(20, 3)):
        forward = lorenz_vector_field([x, y, z])
        mirrored = lorenz_vector_field([-x, -y, z])
        np.testing.assert_array_equal(mirrored, [-forward[0], -forward[1], forward[2]])


def test_jacobian_matches_central_finite_differences(rng: np.random.Generator) -> None:
    parameters = LorenzParameters(sigma=7.0, rho=19.0, beta=2.0)
    step = 1e-6
    for state in rng.normal(scale=10.0, size=(10, 3)):
        numeric = np.empty((3, 3))
        for column in range(3):
            shift = np.zeros(3)
            shift[column] = step
            numeric[:, column] = (
                lorenz_vector_field(state + shift, parameters)
                - lorenz_vector_field(state - shift, parameters)
            ) / (2.0 * step)
        # The field is quadratic, so central differences are exact up to rounding.
        np.testing.assert_allclose(lorenz_jacobian(state, parameters), numeric, atol=1e-7)


def test_flow_contracts_volume_at_a_constant_rate(rng: np.random.Generator) -> None:
    parameters = LorenzParameters(sigma=12.0, rho=40.0, beta=1.5)
    expected = -(parameters.sigma + 1.0 + parameters.beta)
    for state in rng.normal(scale=20.0, size=(10, 3)):
        assert np.trace(lorenz_jacobian(state, parameters)) == pytest.approx(expected, abs=1e-12)


@pytest.mark.parametrize("state", [[1.0, 2.0], [[1.0, 2.0, 3.0]], [1.0, math.nan, 0.0]])
def test_rejects_invalid_state(state: object) -> None:
    with pytest.raises(InputValidationError, match="state"):
        lorenz_vector_field(state)  # type: ignore[arg-type]
    with pytest.raises(InputValidationError, match="state"):
        lorenz_jacobian(state)  # type: ignore[arg-type]


def test_rejects_parameters_of_the_wrong_type() -> None:
    with pytest.raises(TypeError, match="LorenzParameters"):
        lorenz_vector_field([1.0, 1.0, 1.0], {"sigma": 10.0})  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="LorenzParameters"):
        lorenz_fixed_points((10.0, 28.0, 8.0 / 3.0))  # type: ignore[arg-type]


# --- equilibria and their stability --------------------------------------------------------------


def test_below_rho_one_only_the_origin_exists_and_it_is_stable() -> None:
    (origin,) = lorenz_fixed_points(LorenzParameters(rho=0.5))
    assert origin.location == (0.0, 0.0, 0.0)
    assert origin.stability is STABLE


def test_origin_is_non_hyperbolic_at_the_pitchfork() -> None:
    (origin,) = lorenz_fixed_points(LorenzParameters(rho=1.0))
    assert origin.stability is NON_HYPERBOLIC
    assert origin.eigenvalues[0] == pytest.approx(0.0, abs=1e-14)


@pytest.mark.parametrize("rho", [0.3, 0.9, 1.5, 10.0, 28.0, 100.0])
def test_origin_eigenvalues_match_the_analytic_formula(rho: float) -> None:
    sigma, beta = SIGMA_CANONICAL, BETA_CANONICAL
    root = math.sqrt((sigma + 1.0) ** 2 + 4.0 * sigma * (rho - 1.0))
    expected = [-beta, (-(sigma + 1.0) + root) / 2.0, (-(sigma + 1.0) - root) / 2.0]
    origin = lorenz_fixed_points(LorenzParameters(rho=rho))[0]
    np.testing.assert_allclose(origin.eigenvalues, sort_complex(expected), atol=1e-12)


@pytest.mark.parametrize("rho", [1.5, 10.0, 28.0])
def test_above_rho_one_the_origin_is_a_saddle_with_one_unstable_direction(rho: float) -> None:
    origin = lorenz_fixed_points(LorenzParameters(rho=rho))[0]
    assert origin.stability is UNSTABLE
    assert sum(value.real > 0.0 for value in origin.eigenvalues) == 1


@pytest.mark.parametrize("rho", [1.5, 10.0, 24.5, 28.0, 99.0])
def test_c_plus_minus_location_and_vector_field(rho: float) -> None:
    parameters = LorenzParameters(rho=rho)
    _, c_plus, c_minus = lorenz_fixed_points(parameters)
    offset = math.sqrt(BETA_CANONICAL * (rho - 1.0))
    assert c_plus.location == pytest.approx((offset, offset, rho - 1.0), rel=1e-15)
    assert c_minus.location == pytest.approx((-offset, -offset, rho - 1.0), rel=1e-15)
    for equilibrium in (c_plus, c_minus):
        np.testing.assert_allclose(
            lorenz_vector_field(equilibrium.location, parameters), 0.0, atol=1e-12
        )


@pytest.mark.parametrize("rho", [1.5, 10.0, 24.5, 28.0, 99.0])
def test_c_plus_minus_eigenvalues_are_the_roots_of_the_characteristic_polynomial(
    rho: float,
) -> None:
    parameters = LorenzParameters(rho=rho)
    expected = sort_complex(characteristic_roots(parameters))
    for equilibrium in lorenz_fixed_points(parameters)[1:]:
        np.testing.assert_allclose(equilibrium.eigenvalues, expected, rtol=1e-10, atol=1e-12)


def test_canonical_equilibria_are_all_unstable() -> None:
    origin, c_plus, c_minus = lorenz_fixed_points()
    assert (origin.stability, c_plus.stability, c_minus.stability) == (UNSTABLE,) * 3
    # C+- are saddle-foci: one real stable direction and an unstable complex pair.
    leading = c_plus.eigenvalues[0]
    assert leading.real > 0.0
    assert leading.imag != 0.0
    assert c_plus.eigenvalues[2].real < 0.0
    assert c_plus.eigenvalues[2].imag == 0.0


# --- Hopf bifurcation ----------------------------------------------------------------------------


def test_canonical_hopf_threshold_is_470_over_19() -> None:
    assert lorenz_hopf_rho() == pytest.approx(470.0 / 19.0, rel=1e-15)


def test_c_plus_minus_lose_stability_at_the_hopf_threshold() -> None:
    hopf = lorenz_hopf_rho()
    assert hopf is not None
    below = lorenz_fixed_points(LorenzParameters(rho=hopf - 1e-6))
    at = lorenz_fixed_points(LorenzParameters(rho=hopf))
    above = lorenz_fixed_points(LorenzParameters(rho=hopf + 1e-6))
    assert [e.stability for e in below[1:]] == [STABLE, STABLE]
    assert [e.stability for e in at[1:]] == [NON_HYPERBOLIC, NON_HYPERBOLIC]
    assert [e.stability for e in above[1:]] == [UNSTABLE, UNSTABLE]


def test_eigenvalues_cross_the_imaginary_axis_at_the_predicted_frequency() -> None:
    hopf = lorenz_hopf_rho()
    assert hopf is not None
    _, c_plus, _ = lorenz_fixed_points(LorenzParameters(rho=hopf))
    frequency = math.sqrt(BETA_CANONICAL * (SIGMA_CANONICAL + hopf))
    assert c_plus.eigenvalues[0] == pytest.approx(complex(0.0, frequency), abs=1e-12)
    assert c_plus.eigenvalues[1] == pytest.approx(complex(0.0, -frequency), abs=1e-12)


@pytest.mark.parametrize(("sigma", "beta"), [(16.0, 4.0), (3.0, 1.0), (5.0, 0.5)])
def test_hopf_threshold_for_other_parameters(sigma: float, beta: float) -> None:
    hopf = lorenz_hopf_rho(sigma, beta)
    assert hopf == pytest.approx(sigma * (sigma + beta + 3.0) / (sigma - beta - 1.0))
    assert hopf is not None
    for rho, expected in ((hopf * 0.99, STABLE), (hopf * 1.01, UNSTABLE)):
        c_plus = lorenz_fixed_points(LorenzParameters(sigma=sigma, rho=rho, beta=beta))[1]
        assert c_plus.stability is expected


@pytest.mark.parametrize(("sigma", "beta"), [(2.0, BETA_CANONICAL), (3.0, 2.0), (1.0, 1.0)])
def test_without_hopf_c_plus_minus_stay_stable_for_every_rho(sigma: float, beta: float) -> None:
    assert lorenz_hopf_rho(sigma, beta) is None
    for rho in (2.0, 50.0, 5_000.0):
        _, c_plus, c_minus = lorenz_fixed_points(LorenzParameters(sigma=sigma, rho=rho, beta=beta))
        assert (c_plus.stability, c_minus.stability) == (STABLE, STABLE)


def test_hopf_rejects_invalid_parameters() -> None:
    with pytest.raises(DomainError, match="sigma"):
        lorenz_hopf_rho(0.0, 1.0)
    with pytest.raises(InputValidationError, match="beta"):
        lorenz_hopf_rho(10.0, math.inf)


# --- simulation ----------------------------------------------------------------------------------


def test_simulation_shape_grid_and_settings() -> None:
    trajectory = simulate_lorenz([1.0, 1.0, 1.0], n_steps=200, dt=0.01)
    assert trajectory.states.shape == (201, 3)
    np.testing.assert_array_equal(trajectory.states[0], [1.0, 1.0, 1.0])
    assert trajectory.times[-1] == pytest.approx(2.0)
    assert (trajectory.method, trajectory.rtol, trajectory.atol) == ("DOP853", 1e-10, 1e-12)


def test_simulation_is_deterministic() -> None:
    first = simulate_lorenz([1.0, 1.0, 1.0], n_steps=1_000, dt=0.01)
    second = simulate_lorenz([1.0, 1.0, 1.0], n_steps=1_000, dt=0.01)
    np.testing.assert_array_equal(first.states, second.states)


def test_z_axis_is_invariant_with_exponential_decay() -> None:
    trajectory = simulate_lorenz([0.0, 0.0, 7.0], n_steps=100, dt=0.05)
    np.testing.assert_array_equal(trajectory.states[:, :2], 0.0)
    exact = 7.0 * np.exp(-BETA_CANONICAL * trajectory.times)
    np.testing.assert_allclose(trajectory.states[:, 2], exact, rtol=1e-9, atol=1e-11)


def test_trajectories_respect_the_symmetry() -> None:
    forward = simulate_lorenz([3.0, -2.0, 15.0], n_steps=2_000, dt=0.01)
    mirrored = simulate_lorenz([-3.0, 2.0, 15.0], n_steps=2_000, dt=0.01)
    np.testing.assert_allclose(mirrored.states[:, :2], -forward.states[:, :2], atol=1e-12)
    np.testing.assert_allclose(mirrored.states[:, 2], forward.states[:, 2], atol=1e-12)


def test_trajectories_stay_in_the_trapping_ball() -> None:
    # V = x^2 + y^2 + (z - sigma - rho)^2 decreases outside an ellipsoid, so the ball
    # V <= (sigma + rho)^2 beta^2 / (4 (beta - 1)) is forward invariant (for sigma >= 1, beta > 1).
    sigma, rho, beta = SIGMA_CANONICAL, RHO_CANONICAL, BETA_CANONICAL
    radius_squared = (sigma + rho) ** 2 * beta**2 / (4.0 * (beta - 1.0))
    for start in ([1.0, 1.0, 1.0], [0.1, 0.0, 60.0], [-20.0, 25.0, 5.0]):
        x, y, z = simulate_lorenz(start, n_steps=5_000, dt=0.01).states.T
        lyapunov = x**2 + y**2 + (z - sigma - rho) ** 2
        assert lyapunov.max() <= max(lyapunov[0], radius_squared)
        assert lyapunov[-1] <= radius_squared


def test_below_rho_one_trajectories_decay_at_the_rate_of_the_leading_eigenvalue() -> None:
    parameters = LorenzParameters(rho=0.5)
    trajectory = simulate_lorenz([3.0, -2.0, 5.0], n_steps=250, dt=0.1, parameters=parameters)
    window = (trajectory.times >= 10.0) & (trajectory.times <= 25.0)
    distance = np.linalg.norm(trajectory.states[window], axis=1)
    slope = np.polyfit(trajectory.times[window], np.log(distance), 1)[0]
    leading = lorenz_fixed_points(parameters)[0].eigenvalues[0].real
    assert slope == pytest.approx(leading, rel=1e-4)


@pytest.mark.parametrize(
    ("start", "target"), [([1.0, 1.0, 1.0], 1), ([-1.0, -1.0, 1.0], 2), ([5.0, -3.0, 2.0], 2)]
)
def test_between_pitchfork_and_hopf_trajectories_converge_to_c_plus_minus(
    start: list[float], target: int
) -> None:
    parameters = LorenzParameters(rho=10.0)
    final = simulate_lorenz(start, n_steps=2_000, dt=0.05, parameters=parameters).states[-1]
    equilibrium = lorenz_fixed_points(parameters)[target]
    np.testing.assert_allclose(final, equilibrium.location, atol=1e-8)


def test_sensitive_dependence_only_in_the_chaotic_regime() -> None:
    def separation(rho: float) -> float:
        parameters = LorenzParameters(rho=rho)
        first = simulate_lorenz([1.0, 1.0, 1.0], n_steps=400, dt=0.1, parameters=parameters)
        second = simulate_lorenz([1.0, 1.0, 1.0 + 1e-9], n_steps=400, dt=0.1, parameters=parameters)
        return float(np.linalg.norm(first.states[-1] - second.states[-1]))

    assert separation(RHO_CANONICAL) > 1.0  # 1e-9 grew by more than nine orders of magnitude
    assert separation(10.0) < 1e-9  # the perturbation decayed


@pytest.mark.parametrize("method", ["RK45", "Radau"])
def test_methods_agree_with_a_tight_tolerance_reference(method: str) -> None:
    reference = simulate_lorenz([1.0, 1.0, 1.0], n_steps=100, dt=0.01, rtol=1e-13, atol=1e-14)
    trajectory = simulate_lorenz([1.0, 1.0, 1.0], n_steps=100, dt=0.01, method=method)  # type: ignore[arg-type]
    np.testing.assert_allclose(trajectory.states, reference.states, atol=1e-7)
    assert trajectory.method == method


@pytest.mark.parametrize("state", [[1.0, 1.0], [1.0, 1.0, math.inf]])
def test_simulation_rejects_invalid_initial_state(state: list[float]) -> None:
    with pytest.raises(InputValidationError, match="initial_state"):
        simulate_lorenz(state, n_steps=10, dt=0.01)


def test_simulation_rejects_parameters_of_the_wrong_type() -> None:
    with pytest.raises(TypeError, match="LorenzParameters"):
        simulate_lorenz([1.0, 1.0, 1.0], n_steps=10, dt=0.01, parameters=None)  # type: ignore[arg-type]

r"""The Lorenz system.

.. math::

    \dot x = \sigma (y - x), \qquad
    \dot y = x (\rho - z) - y, \qquad
    \dot z = x y - \beta z,
    \qquad \sigma, \rho, \beta > 0

A three-mode truncation of convection in a fluid layer heated from below (Lorenz,
1963): :math:`\sigma` is the Prandtl number, :math:`\rho` the Rayleigh number divided
by its critical value, and :math:`\beta` a geometric factor. The canonical parameters
:math:`\sigma = 10`, :math:`\rho = 28`, :math:`\beta = 8/3` give the butterfly-shaped
strange attractor.

Known results used as tests (see ``docs/math/sistema-lorenz.md``):

* The flow contracts volume at the constant rate
  :math:`\nabla \cdot F = -(\sigma + 1 + \beta)`, the trace of the Jacobian.
* It is symmetric under :math:`(x, y, z) \mapsto (-x, -y, z)`.
* The :math:`z` axis is invariant, with the exact solution
  :math:`z(t) = z_0 e^{-\beta t}` on it.
* The origin is an equilibrium, stable for :math:`\rho < 1`. At :math:`\rho = 1` a
  pitchfork bifurcation creates two more,
  :math:`C^\pm = (\pm\sqrt{\beta(\rho - 1)}, \pm\sqrt{\beta(\rho - 1)}, \rho - 1)`.
* If :math:`\sigma > \beta + 1`, :math:`C^\pm` lose stability in a subcritical Hopf
  bifurcation at :math:`\rho_H = \sigma(\sigma + \beta + 3)/(\sigma - \beta - 1)`,
  which is :math:`470/19 \approx 24.74` for the canonical :math:`\sigma` and
  :math:`\beta`. Otherwise they stay stable for every :math:`\rho > 1`.

Simulating the system shows what the *model* does. It says nothing on its own about
whether a market, or any other real system, is deterministic or chaotic.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Final

import numpy as np
import numpy.typing as npt

from quantlab._validation import validate_positive_real, validate_state_vector
from quantlab.dynamics.integration import (
    DEFAULT_ATOL,
    DEFAULT_METHOD,
    DEFAULT_RTOL,
    OdeMethod,
    Trajectory,
    integrate_autonomous,
)
from quantlab.dynamics.stability import DEFAULT_EIGENVALUE_ATOL, Equilibrium, analyze_equilibrium

SIGMA_CANONICAL: Final[float] = 10.0
"""Prandtl number used by Lorenz (1963)."""
RHO_CANONICAL: Final[float] = 28.0
"""Normalized Rayleigh number used by Lorenz (1963), in the chaotic regime."""
BETA_CANONICAL: Final[float] = 8.0 / 3.0
"""Geometric factor used by Lorenz (1963)."""
STATE_DIMENSION: Final[int] = 3
"""The state is :math:`(x, y, z)`."""

_PITCHFORK_RHO: Final[float] = 1.0
"""Value of rho at which the equilibria C+ and C- branch off the origin."""


@dataclass(frozen=True, slots=True)
class LorenzParameters:
    """Parameters of the Lorenz system, validated on construction.

    Attributes
    ----------
    sigma
        Prandtl number, ``> 0``.
    rho
        Normalized Rayleigh number, ``> 0``.
    beta
        Geometric factor, ``> 0``.

    Raises
    ------
    TypeError
        If a parameter is not a real number.
    InputValidationError
        If a parameter is NaN or infinite.
    DomainError
        If a parameter is zero or negative.
    """

    sigma: float = SIGMA_CANONICAL
    rho: float = RHO_CANONICAL
    beta: float = BETA_CANONICAL

    def __post_init__(self) -> None:
        """Validate every parameter and store it as a float."""
        for field_name in ("sigma", "rho", "beta"):
            value = validate_positive_real(getattr(self, field_name), name=field_name)
            object.__setattr__(self, field_name, value)


CANONICAL_PARAMETERS: Final = LorenzParameters()
"""``sigma = 10``, ``rho = 28``, ``beta = 8/3``."""


def _validated_parameters(parameters: object) -> LorenzParameters:
    if not isinstance(parameters, LorenzParameters):
        raise TypeError(
            f"parameters must be a LorenzParameters instance, got {type(parameters).__name__}."
        )
    return parameters


def _validated_state(state: object) -> npt.NDArray[np.float64]:
    return validate_state_vector(state, name="state", dimension=STATE_DIMENSION)


def _vector_field(
    state: npt.NDArray[np.float64], parameters: LorenzParameters
) -> npt.NDArray[np.float64]:
    """Evaluate the right-hand side without validation. Callers must validate."""
    x, y, z = state
    return np.array(
        [
            parameters.sigma * (y - x),
            x * (parameters.rho - z) - y,
            x * y - parameters.beta * z,
        ],
        dtype=np.float64,
    )


def _jacobian(
    state: npt.NDArray[np.float64], parameters: LorenzParameters
) -> npt.NDArray[np.float64]:
    """Evaluate the Jacobian without validation. Callers must validate."""
    x, y, z = state
    return np.array(
        [
            [-parameters.sigma, parameters.sigma, 0.0],
            [parameters.rho - z, -1.0, -x],
            [y, x, -parameters.beta],
        ],
        dtype=np.float64,
    )


def lorenz_vector_field(
    state: npt.ArrayLike, parameters: LorenzParameters = CANONICAL_PARAMETERS
) -> npt.NDArray[np.float64]:
    r"""Evaluate the right-hand side :math:`F(x, y, z)` of the Lorenz system.

    Parameters
    ----------
    state
        The point :math:`(x, y, z)`.
    parameters
        System parameters; canonical by default.

    Returns
    -------
    numpy.ndarray
        The time derivative :math:`(\dot x, \dot y, \dot z)`, shape ``(3,)``.

    Raises
    ------
    TypeError
        If ``state`` does not hold real numbers or ``parameters`` is not a
        :class:`LorenzParameters`.
    InputValidationError
        If ``state`` does not have three finite coordinates.
    """
    return _vector_field(_validated_state(state), _validated_parameters(parameters))


def lorenz_jacobian(
    state: npt.ArrayLike, parameters: LorenzParameters = CANONICAL_PARAMETERS
) -> npt.NDArray[np.float64]:
    r"""Evaluate the Jacobian matrix :math:`DF(x, y, z)` of the Lorenz system.

    .. math::

        DF = \begin{pmatrix}
            -\sigma & \sigma & 0 \\
            \rho - z & -1 & -x \\
            y & x & -\beta
        \end{pmatrix}

    Parameters
    ----------
    state
        The point :math:`(x, y, z)`.
    parameters
        System parameters; canonical by default.

    Returns
    -------
    numpy.ndarray
        The matrix, shape ``(3, 3)``. Its trace is :math:`-(\sigma + 1 + \beta)`
        everywhere.

    Raises
    ------
    TypeError, InputValidationError
        Same conditions as in :func:`lorenz_vector_field`.
    """
    return _jacobian(_validated_state(state), _validated_parameters(parameters))


def lorenz_fixed_points(
    parameters: LorenzParameters = CANONICAL_PARAMETERS,
    *,
    atol: float = DEFAULT_EIGENVALUE_ATOL,
) -> tuple[Equilibrium, ...]:
    r"""Return the equilibria of the Lorenz system with their linear stability.

    Parameters
    ----------
    parameters
        System parameters; canonical by default.
    atol
        Real parts of eigenvalues within ``atol`` of zero are treated as zero (see
        :func:`~quantlab.dynamics.stability.classify_flow_equilibrium`).

    Returns
    -------
    tuple of Equilibrium
        The origin always. For ``rho > 1`` also :math:`C^+` and then :math:`C^-`,
        with :math:`x = y = \pm\sqrt{\beta(\rho - 1)}` and :math:`z = \rho - 1`. At
        ``rho = 1`` they coincide with the origin and are omitted.

    Raises
    ------
    TypeError
        If ``parameters`` is not a :class:`LorenzParameters` or ``atol`` is not a
        real number.
    InputValidationError
        If ``atol`` is negative or not finite.
    """
    params = _validated_parameters(parameters)
    locations = [np.zeros(STATE_DIMENSION)]
    if params.rho > _PITCHFORK_RHO:
        offset = math.sqrt(params.beta * (params.rho - 1.0))
        height = params.rho - 1.0
        locations.append(np.array([offset, offset, height]))
        locations.append(np.array([-offset, -offset, height]))
    return tuple(
        analyze_equilibrium(location, _jacobian(location, params), atol=atol)
        for location in locations
    )


def lorenz_hopf_rho(sigma: float = SIGMA_CANONICAL, beta: float = BETA_CANONICAL) -> float | None:
    r"""Return the value of :math:`\rho` at which :math:`C^\pm` lose stability.

    At :math:`C^\pm` the characteristic polynomial is
    :math:`\mu^3 + (\sigma + \beta + 1)\mu^2 + \beta(\sigma + \rho)\mu + 2\sigma\beta(\rho - 1)`.
    By the Routh-Hurwitz criterion its roots all have negative real part exactly when
    :math:`(\sigma + \beta + 1)(\sigma + \rho) > 2\sigma(\rho - 1)`. If
    :math:`\sigma > \beta + 1` this fails above

    .. math::

        \rho_H = \frac{\sigma (\sigma + \beta + 3)}{\sigma - \beta - 1},

    where a pair of eigenvalues crosses the imaginary axis at
    :math:`\pm i\sqrt{\beta(\sigma + \rho_H)}`: a (subcritical) Hopf bifurcation.

    Parameters
    ----------
    sigma, beta
        System parameters, ``> 0``; canonical by default, giving ``470 / 19``.

    Returns
    -------
    float or None
        :math:`\rho_H`, or ``None`` if :math:`\sigma \le \beta + 1`, in which case
        :math:`C^\pm` are linearly stable for every :math:`\rho > 1`.

    Raises
    ------
    TypeError
        If ``sigma`` or ``beta`` is not a real number.
    InputValidationError
        If ``sigma`` or ``beta`` is NaN or infinite.
    DomainError
        If ``sigma`` or ``beta`` is zero or negative.
    """
    prandtl = validate_positive_real(sigma, name="sigma")
    geometry = validate_positive_real(beta, name="beta")
    if prandtl <= geometry + 1.0:
        return None
    return prandtl * (prandtl + geometry + 3.0) / (prandtl - geometry - 1.0)


def simulate_lorenz(
    initial_state: npt.ArrayLike,
    *,
    n_steps: int,
    dt: float,
    parameters: LorenzParameters = CANONICAL_PARAMETERS,
    method: OdeMethod = DEFAULT_METHOD,
    rtol: float = DEFAULT_RTOL,
    atol: float = DEFAULT_ATOL,
) -> Trajectory:
    """Integrate the Lorenz system and sample the trajectory every ``dt`` time units.

    Parameters
    ----------
    initial_state
        :math:`(x_0, y_0, z_0)`.
    n_steps
        Number of sampling intervals, ``>= 0``; the trajectory has ``n_steps + 1``
        points.
    dt
        Sampling interval, ``> 0``. The solver picks its own, adaptive, steps.
    parameters
        System parameters; canonical by default.
    method
        Solver: ``"DOP853"`` (default), ``"RK45"`` or ``"Radau"``. The Lorenz system
        is not stiff for moderate parameters, so the explicit methods are the
        efficient choice; ``"Radau"`` receives the analytic Jacobian.
    rtol, atol
        Tolerances of the solver's local error control.

    Returns
    -------
    Trajectory
        Times, states of shape ``(n_steps + 1, 3)`` and the solver settings.

    Raises
    ------
    TypeError
        If an argument has the wrong type.
    InputValidationError
        If ``initial_state`` does not have three finite coordinates, ``n_steps`` is
        negative or ``method`` is unknown.
    DomainError
        If ``dt`` or a tolerance is out of range.
    ComputationError
        If the solver fails.

    Notes
    -----
    The computation is deterministic: the same arguments give the same array on the
    same platform and library versions. In the chaotic regime, however, any error,
    from the tolerances or from rounding, grows roughly like :math:`e^{0.9 t}`
    (0.9 being the largest Lyapunov exponent at the canonical parameters, a value
    from the literature). After a few tens of time units the computed trajectory is
    no longer close to the exact solution from the same initial state, although it
    still follows the attractor. Read it as a sample of the dynamics, not as a
    forecast of the state at a given time.
    """
    params = _validated_parameters(parameters)
    start = validate_state_vector(initial_state, name="initial_state", dimension=STATE_DIMENSION)
    return integrate_autonomous(
        lambda state: _vector_field(state, params),
        start,
        n_steps=n_steps,
        dt=dt,
        jacobian=lambda state: _jacobian(state, params),
        method=method,
        rtol=rtol,
        atol=atol,
    )

r"""Numerical integration of autonomous ordinary differential equations.

Solves :math:`\dot{\mathbf x} = F(\mathbf x)`, :math:`\mathbf x(0) = \mathbf x_0`, with
the adaptive Runge-Kutta methods of :func:`scipy.integrate.solve_ivp`, and samples the
solution on a uniform time grid :math:`t_k = k\,\Delta t`.

The sampling interval :math:`\Delta t` and the integration step are independent: the
solver chooses its own steps to keep the local error within ``rtol`` and ``atol``, and
the grid values come from its dense-output interpolant, whose order matches the
method. A coarse grid therefore does not make the solution less accurate; it only
records fewer points of it. See ``docs/adr/0004-integracao-numerica.md``.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import Final, Literal

import numpy as np
import numpy.typing as npt
from scipy.integrate import solve_ivp

from quantlab._validation import validate_int, validate_positive_real, validate_state_vector
from quantlab.exceptions import ComputationError, DomainError, InputValidationError

type OdeMethod = Literal["DOP853", "RK45", "Radau"]
"""Supported solvers: two explicit Runge-Kutta pairs and one implicit method for stiff systems."""

type StateFunction = Callable[[npt.NDArray[np.float64]], npt.NDArray[np.float64]]
"""A function of the state only: the vector field :math:`F` or its Jacobian :math:`DF`."""

ODE_METHODS: Final[tuple[OdeMethod, ...]] = ("DOP853", "RK45", "Radau")
"""Names accepted by ``method``."""
IMPLICIT_METHODS: Final[frozenset[OdeMethod]] = frozenset({"Radau"})
"""Methods that use the Jacobian. SciPy warns if it is passed to the others."""

DEFAULT_METHOD: Final[OdeMethod] = "DOP853"
"""Explicit Runge-Kutta of order 8 (Dormand-Prince), efficient at tight tolerances."""
DEFAULT_RTOL: Final[float] = 1e-10
"""Relative tolerance of the local error estimate."""
DEFAULT_ATOL: Final[float] = 1e-12
"""Absolute tolerance of the local error estimate, for components close to zero."""
MIN_RTOL: Final[float] = 100.0 * float(np.finfo(np.float64).eps)
"""Smallest ``rtol`` SciPy honours; below it SciPy silently raises the value instead."""


@dataclass(frozen=True, slots=True, eq=False)
class Trajectory:
    """A numerically integrated solution of an autonomous ODE, sampled on a uniform grid.

    The arrays are read-only, so a trajectory cannot be modified after it is recorded.

    Attributes
    ----------
    times
        Sampling times, shape ``(n_points,)``, starting at 0 with constant spacing.
    states
        States at those times, shape ``(n_points, dimension)``; ``states[0]`` is the
        initial state.
    method
        Name of the solver used.
    rtol, atol
        Tolerances of the solver's local error control.
    n_evaluations
        Number of evaluations of the vector field the solver made: a measure of cost.
    """

    times: npt.NDArray[np.float64]
    states: npt.NDArray[np.float64]
    method: str
    rtol: float
    atol: float
    n_evaluations: int


def _validated_method(method: object) -> OdeMethod:
    if not isinstance(method, str):
        raise TypeError(f"method must be a string, got {type(method).__name__}.")
    for supported in ODE_METHODS:
        if method == supported:
            return supported
    raise InputValidationError(f"method must be one of {list(ODE_METHODS)}, got {method!r}.")


def _validated_tolerances(rtol: object, atol: object) -> tuple[float, float]:
    relative = validate_positive_real(rtol, name="rtol")
    if relative < MIN_RTOL:
        raise DomainError(
            f"rtol must be >= {MIN_RTOL:.3g} (100 machine epsilons), got {relative}: "
            "tighter values are below the rounding error of float64."
        )
    return relative, validate_positive_real(atol, name="atol")


def _read_only(values: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
    values.flags.writeable = False
    return values


def integrate_autonomous(
    vector_field: StateFunction,
    initial_state: npt.ArrayLike,
    *,
    n_steps: int,
    dt: float,
    jacobian: StateFunction | None = None,
    method: OdeMethod = DEFAULT_METHOD,
    rtol: float = DEFAULT_RTOL,
    atol: float = DEFAULT_ATOL,
) -> Trajectory:
    r"""Integrate an autonomous ODE and sample the solution every ``dt`` time units.

    Parameters
    ----------
    vector_field
        The right-hand side :math:`F`, mapping a state of shape ``(dimension,)`` to its
        time derivative of the same shape. It is called by the solver without
        validation, so it must be cheap and must not modify its argument.
    initial_state
        :math:`\mathbf x_0`, a one-dimensional sequence of finite real numbers.
    n_steps
        Number of sampling intervals, ``>= 0``. The trajectory has ``n_steps + 1``
        points, at times ``0, dt, ..., n_steps * dt``.
    dt
        Sampling interval, ``> 0``. It does not set the integration step.
    jacobian
        The Jacobian :math:`DF`, used only by implicit methods (``"Radau"``). Without
        it, they approximate the Jacobian by finite differences.
    method
        Solver name, one of :data:`ODE_METHODS`.
    rtol, atol
        Relative and absolute tolerances of the local error control, ``rtol >=``
        :data:`MIN_RTOL` and ``atol > 0``.

    Returns
    -------
    Trajectory
        The sampled solution together with the solver settings.

    Raises
    ------
    TypeError
        If ``vector_field`` or ``jacobian`` is not callable, ``initial_state`` does not
        hold real numbers, ``n_steps`` is not an integer, ``method`` is not a string,
        or a tolerance or ``dt`` is not a real number.
    InputValidationError
        If ``initial_state`` is not a finite non-empty vector, ``n_steps`` is
        negative, or ``method`` is unknown.
    DomainError
        If ``dt`` or a tolerance is not strictly positive, ``rtol`` is below
        :data:`MIN_RTOL`, or ``n_steps * dt`` overflows.
    ComputationError
        If the solver fails (for example because the solution blows up in finite
        time) or produces non-finite values.

    Notes
    -----
    Tolerances bound the *local* error of each step. The global error at time
    :math:`t` can be much larger: in a chaotic system it grows roughly like
    :math:`e^{\lambda_{\max} t}`, where :math:`\lambda_{\max}` is the largest
    Lyapunov exponent.
    """
    if not callable(vector_field):
        raise TypeError(f"vector_field must be callable, got {type(vector_field).__name__}.")
    if jacobian is not None and not callable(jacobian):
        raise TypeError(f"jacobian must be callable or None, got {type(jacobian).__name__}.")
    state = validate_state_vector(initial_state, name="initial_state", dimension=None)
    steps = validate_int(n_steps, name="n_steps", minimum=0)
    interval = validate_positive_real(dt, name="dt")
    solver = _validated_method(method)
    relative, absolute = _validated_tolerances(rtol, atol)

    # Checked in Python floats, which overflow to inf silently, before NumPy would warn.
    if not math.isfinite(interval * steps):
        raise DomainError(f"The time horizon n_steps * dt = {steps} * {interval} is not finite.")
    times = interval * np.arange(steps + 1, dtype=np.float64)
    if steps == 0:
        return Trajectory(
            times=_read_only(times),
            states=_read_only(state.reshape(1, -1)),
            method=solver,
            rtol=relative,
            atol=absolute,
            n_evaluations=0,
        )

    def derivative(_time: float, current: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        return vector_field(current)

    span = (0.0, float(times[-1]))
    if solver in IMPLICIT_METHODS and jacobian is not None:
        state_jacobian = jacobian

        def jacobian_matrix(
            _time: float, current: npt.NDArray[np.float64]
        ) -> npt.NDArray[np.float64]:
            return state_jacobian(current)

        solution = solve_ivp(
            derivative,
            span,
            state,
            method=solver,
            t_eval=times,
            rtol=relative,
            atol=absolute,
            jac=jacobian_matrix,
        )
    else:
        # Passing jac (even None) to an explicit method makes SciPy warn that it is unused.
        solution = solve_ivp(
            derivative, span, state, method=solver, t_eval=times, rtol=relative, atol=absolute
        )
    if not solution.success:
        raise ComputationError(f"The ODE solver {solver} failed: {solution.message}")
    states = np.ascontiguousarray(solution.y.T, dtype=np.float64)
    if not np.isfinite(states).all():
        raise ComputationError(f"The ODE solver {solver} produced non-finite states.")
    return Trajectory(
        times=_read_only(times),
        states=_read_only(states),
        method=solver,
        rtol=relative,
        atol=absolute,
        n_evaluations=int(solution.nfev),
    )

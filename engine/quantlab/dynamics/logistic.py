r"""The logistic map.

.. math::

    x_{t+1} = f(x_t) = r \, x_t (1 - x_t), \qquad x_t \in [0, 1], \; r \in [0, 4]

For :math:`r \in [0, 4]` the map sends :math:`[0, 1]` into itself, so orbits
started in the interval stay there. Its derivative is :math:`f'(x) = r(1 - 2x)`.

Known results used as tests (see ``docs/math/mapa-logistico.md``):

* :math:`x = 0` is a fixed point with multiplier :math:`r`: stable for :math:`r < 1`.
* For :math:`r > 1` there is a second fixed point :math:`x^* = 1 - 1/r` with
  multiplier :math:`2 - r`: stable for :math:`1 < r < 3`.
* The period-doubling cascade starts at :math:`r = 3` and accumulates near
  :math:`r \approx 3.5699`, beyond which chaotic orbits appear.
* At :math:`r = 4` the Lyapunov exponent is exactly :math:`\ln 2`.

Simulating the map shows what the *model* does. It says nothing on its own about
whether a real market is deterministic or chaotic.
"""

from __future__ import annotations

from typing import Final

import numpy as np
import numpy.typing as npt

from quantlab._validation import validate_closed_interval, validate_int, validate_orbit
from quantlab.dynamics.stability import FixedPoint, classify_map_fixed_point
from quantlab.exceptions import DomainError

R_MIN: Final[float] = 0.0
"""Smallest growth parameter for which the map keeps ``[0, 1]`` invariant."""
R_MAX: Final[float] = 4.0
"""Largest growth parameter for which the map keeps ``[0, 1]`` invariant."""
X_MIN: Final[float] = 0.0
"""Lower end of the state space."""
X_MAX: Final[float] = 1.0
"""Upper end of the state space."""

_NONTRIVIAL_FIXED_POINT_THRESHOLD = 1.0


def _validated_r(r: object) -> float:
    return validate_closed_interval(r, name="r", lower=R_MIN, upper=R_MAX)


def _validated_x(x: object, name: str) -> float:
    return validate_closed_interval(x, name=name, lower=X_MIN, upper=X_MAX)


def logistic_map(x: float, r: float) -> float:
    """Apply the logistic map once: ``r * x * (1 - x)``.

    Parameters
    ----------
    x
        Current state, in ``[0, 1]``.
    r
        Growth parameter, in ``[0, 4]``.

    Returns
    -------
    float
        Next state, in ``[0, 1]``.

    Raises
    ------
    TypeError
        If ``x`` or ``r`` is not a real number.
    InputValidationError
        If ``x`` or ``r`` is NaN or infinite.
    DomainError
        If ``x`` is outside ``[0, 1]`` or ``r`` is outside ``[0, 4]``.
    """
    state = _validated_x(x, "x")
    growth = _validated_r(r)
    return growth * state * (1.0 - state)


def logistic_derivative(x: float, r: float) -> float:
    """Return the derivative of the logistic map, ``f'(x) = r * (1 - 2x)``.

    Parameters
    ----------
    x
        State at which to evaluate the derivative, in ``[0, 1]``.
    r
        Growth parameter, in ``[0, 4]``.

    Returns
    -------
    float
        The derivative, in ``[-r, r]``.

    Raises
    ------
    TypeError, InputValidationError, DomainError
        Same conditions as in :func:`logistic_map`.
    """
    state = _validated_x(x, "x")
    growth = _validated_r(r)
    return growth * (1.0 - 2.0 * state)


def _iterate(r: float, x0: float, n_steps: int) -> npt.NDArray[np.float64]:
    """Iterate the map without validation. Callers must validate the arguments."""
    orbit = np.empty(n_steps + 1, dtype=np.float64)
    state = x0
    orbit[0] = state
    for step in range(1, n_steps + 1):
        state = r * state * (1.0 - state)
        orbit[step] = state
    return orbit


def simulate_logistic_map(r: float, x0: float, n_steps: int) -> npt.NDArray[np.float64]:
    """Simulate an orbit of the logistic map.

    Parameters
    ----------
    r
        Growth parameter, in ``[0, 4]``.
    x0
        Initial state, in ``[0, 1]``.
    n_steps
        Number of iterations, ``>= 0``.

    Returns
    -------
    numpy.ndarray
        float64 array of length ``n_steps + 1`` with ``orbit[0] == x0`` and
        ``orbit[t + 1] == r * orbit[t] * (1 - orbit[t])``.

    Raises
    ------
    TypeError
        If ``r`` or ``x0`` is not a real number, or ``n_steps`` is not an integer.
    InputValidationError
        If ``r`` or ``x0`` is NaN or infinite, or ``n_steps`` is negative.
    DomainError
        If ``r`` or ``x0`` is outside its domain.

    Notes
    -----
    The computation is deterministic: the same arguments always produce the same
    array on the same platform. The recurrence is inherently sequential and is
    evaluated with a plain loop. For chaotic parameters, rounding errors grow
    exponentially (at the rate of the Lyapunov exponent), so after a few dozen
    steps the computed orbit departs from the exact orbit of ``x0``. It remains a
    faithful sample of the same dynamics (shadowing), which is what statistics
    such as the Lyapunov exponent rely on.
    """
    growth = _validated_r(r)
    initial = _validated_x(x0, "x0")
    steps = validate_int(n_steps, name="n_steps", minimum=0)
    return _iterate(growth, initial, steps)


def logistic_fixed_points(r: float) -> tuple[FixedPoint, ...]:
    """Return the fixed points of the logistic map in ``[0, 1]`` with their stability.

    Parameters
    ----------
    r
        Growth parameter, in ``[0, 4]``.

    Returns
    -------
    tuple of FixedPoint
        ``x = 0`` always. For ``r > 1`` also ``x* = 1 - 1/r``. For ``r <= 1`` the
        second root ``1 - 1/r`` is not in ``(0, 1]`` (it coincides with 0 at
        ``r = 1``) and is omitted. Each multiplier is computed by evaluating
        :func:`logistic_derivative` at the fixed point.

    Raises
    ------
    TypeError, InputValidationError, DomainError
        If ``r`` is invalid, as in :func:`logistic_map`.
    """
    growth = _validated_r(r)
    locations = [0.0]
    if growth > _NONTRIVIAL_FIXED_POINT_THRESHOLD:
        locations.append(1.0 - 1.0 / growth)
    fixed_points = []
    for location in locations:
        multiplier = logistic_derivative(location, growth)
        fixed_points.append(
            FixedPoint(
                location=location,
                multiplier=multiplier,
                stability=classify_map_fixed_point(multiplier),
            )
        )
    return tuple(fixed_points)


def logistic_lyapunov_exponent(
    r: float,
    x0: float,
    *,
    n_transient: int = 1_000,
    n_steps: int = 100_000,
) -> float:
    r"""Estimate the Lyapunov exponent of the logistic map along one orbit.

    .. math::

        \lambda \approx \frac{1}{N} \sum_{t=T}^{T+N-1} \ln \lvert r (1 - 2 x_t) \rvert

    where :math:`T` is ``n_transient`` and :math:`N` is ``n_steps``. A positive
    exponent indicates sensitive dependence on initial conditions (chaos); a
    negative one indicates convergence to a stable fixed point or cycle.

    Parameters
    ----------
    r
        Growth parameter, in ``[0, 4]``.
    x0
        Initial state, in ``[0, 1]``.
    n_transient
        Iterations discarded before averaging, ``>= 0``, so that the orbit settles
        on its attractor.
    n_steps
        Number of terms in the average, ``>= 1``.

    Returns
    -------
    float
        The estimate. It is ``-inf`` when the orbit hits ``x = 1/2`` exactly,
        where the derivative vanishes: that is the superstable case (for example
        ``r = 2``, whose fixed point is ``1/2``), and :math:`-\infty` is its exact
        exponent.

    Raises
    ------
    TypeError
        If ``r`` or ``x0`` is not a real number, or the counts are not integers.
    InputValidationError
        If ``r`` or ``x0`` is NaN or infinite, or the counts are out of range.
    DomainError
        If ``r`` or ``x0`` is outside its domain.

    Notes
    -----
    This is a finite-time estimate. Its error decreases roughly like
    :math:`1/\sqrt{N}` for chaotic orbits and depends on the initial condition.
    Initial conditions that are eventually fixed (for example ``x0 = 0`` or
    ``x0 = 1``) give the exponent of that fixed point, not of the typical orbit.
    """
    growth = _validated_r(r)
    initial = _validated_x(x0, "x0")
    transient = validate_int(n_transient, name="n_transient", minimum=0)
    steps = validate_int(n_steps, name="n_steps", minimum=1)

    orbit = _iterate(growth, initial, transient + steps - 1)[transient:]
    with np.errstate(divide="ignore"):
        log_stretch = np.log(np.abs(growth * (1.0 - 2.0 * orbit)))
    return float(np.mean(log_stretch))


def logistic_bifurcation_diagram(
    r_values: npt.ArrayLike,
    x0: float,
    *,
    n_transient: int = 1_000,
    n_samples: int = 200,
) -> npt.NDArray[np.float64]:
    r"""Sample the long-run states of the logistic map for many values of ``r``.

    For each :math:`r_i`, iterate from ``x0``, discard the first ``n_transient``
    states and keep the next ``n_samples``:
    :math:`x_T, x_{T+1}, \dots, x_{T+N-1}` with :math:`T` = ``n_transient`` and
    :math:`N` = ``n_samples``. Plotting the samples against :math:`r` gives the
    bifurcation diagram: one point where the orbit settles on a fixed point, ``p``
    points on a ``p``-cycle, and a filled band where it is chaotic.

    Parameters
    ----------
    r_values
        One-dimensional sequence of growth parameters, each in ``[0, 4]``.
    x0
        Initial state shared by every ``r``, in ``[0, 1]``.
    n_transient
        Iterations discarded before sampling, ``>= 0``.
    n_samples
        States kept per value of ``r``, ``>= 1``.

    Returns
    -------
    numpy.ndarray
        float64 array of shape ``(len(r_values), n_samples)``; row ``i`` holds the
        samples for ``r_values[i]``. Each row is identical, bit for bit, to
        ``simulate_logistic_map(r_values[i], x0, n_transient + n_samples - 1)[n_transient:]``.

    Raises
    ------
    TypeError
        If ``x0`` is not a real number or a count is not an integer.
    InputValidationError
        If ``r_values`` is empty, not one-dimensional or not finite, ``x0`` is not
        finite, or a count is out of range.
    DomainError
        If a value of ``r`` lies outside ``[0, 4]`` or ``x0`` outside ``[0, 1]``.

    Notes
    -----
    The recurrence is sequential in time but independent across ``r``, so all
    values of ``r`` advance together, one vectorized step at a time. Points near a
    bifurcation converge slowly: with a short transient they can still be
    approaching the attractor, which blurs the diagram there. A sample that looks
    chaotic in the picture is not a proof of chaos (see
    :func:`logistic_lyapunov_exponent`).
    """
    growth = validate_orbit(r_values, name="r_values", min_length=1)
    outside = (growth < R_MIN) | (growth > R_MAX)
    if outside.any():
        raise DomainError(
            f"r_values must lie in [{R_MIN}, {R_MAX}]; found {int(outside.sum())} value(s) outside."
        )
    initial = _validated_x(x0, "x0")
    transient = validate_int(n_transient, name="n_transient", minimum=0)
    samples = validate_int(n_samples, name="n_samples", minimum=1)

    state = np.full(growth.shape, initial, dtype=np.float64)
    for _ in range(transient):
        state = growth * state * (1.0 - state)
    diagram = np.empty((growth.size, samples), dtype=np.float64)
    diagram[:, 0] = state
    for column in range(1, samples):
        state = growth * state * (1.0 - state)
        diagram[:, column] = state
    return diagram

"""Analysis of simulated orbits of discrete dynamical systems."""

from __future__ import annotations

import numpy as np
import numpy.typing as npt

from quantlab._validation import validate_finite_real, validate_int, validate_orbit
from quantlab.exceptions import InputValidationError

_MIN_PERIOD = 1


def detect_period(
    orbit: npt.ArrayLike,
    *,
    max_period: int = 64,
    atol: float = 1e-9,
) -> int | None:
    r"""Find the smallest period of a one-dimensional orbit, within a tolerance.

    Returns the smallest :math:`p \le` ``max_period`` such that
    :math:`|x_{t+p} - x_t| \le` ``atol`` for every pair of points in the orbit.

    Parameters
    ----------
    orbit
        One-dimensional sequence of states, with the transient already discarded:
        the test applies to *every* point, so a transient makes it fail. At least
        ``2 * max_period`` points are required, so that even the longest candidate
        period is checked over ``max_period`` pairs.
    max_period
        Largest period to test, ``>= 1``.
    atol
        Absolute tolerance, ``>= 0``. It must exceed the distance still left
        between the orbit and its cycle after the transient.

    Returns
    -------
    int or None
        The smallest period found, or ``None`` if the orbit is not periodic up to
        ``max_period`` within ``atol``. ``None`` is consistent with chaos but does
        not prove it: the period may simply exceed ``max_period``, or the orbit
        may still be converging.

    Raises
    ------
    TypeError
        If ``max_period`` is not an integer or ``atol`` is not a real number.
    InputValidationError
        If ``orbit`` is not one-dimensional or contains NaN or infinite values, or
        the parameters are out of range.
    InsufficientDataError
        If ``orbit`` has fewer than ``2 * max_period`` points.
    """
    longest = validate_int(max_period, name="max_period", minimum=_MIN_PERIOD)
    tolerance = validate_finite_real(atol, name="atol")
    if tolerance < 0.0:
        raise InputValidationError(f"atol must be non-negative, got {tolerance}.")
    values = validate_orbit(orbit, name="orbit", min_length=2 * longest)

    for period in range(_MIN_PERIOD, longest + 1):
        if np.all(np.abs(values[period:] - values[:-period]) <= tolerance):
            return period
    return None

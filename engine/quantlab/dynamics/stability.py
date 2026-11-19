r"""Linear stability of fixed points of one-dimensional maps.

For a map :math:`x_{t+1} = f(x_t)` with a fixed point :math:`x^* = f(x^*)`, a
small perturbation :math:`\varepsilon_t = x_t - x^*` evolves, to first order, as
:math:`\varepsilon_{t+1} \approx \lambda \varepsilon_t` with multiplier
:math:`\lambda = f'(x^*)`. Hence:

* :math:`|\lambda| < 1`: perturbations shrink, the fixed point is asymptotically stable;
* :math:`|\lambda| > 1`: perturbations grow, the fixed point is unstable;
* :math:`|\lambda| = 1`: non-hyperbolic case; the linearization is inconclusive and
  higher-order terms decide. Bifurcations happen at such points.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from quantlab._validation import validate_finite_real
from quantlab.exceptions import InputValidationError

DEFAULT_MULTIPLIER_ATOL: Final[float] = 1e-12
"""Half-width of the band around ``|multiplier| = 1`` treated as non-hyperbolic.

A multiplier computed in floating point carries rounding error, so a value such
as ``-1.0000000000000002`` is classified as non-hyperbolic rather than unstable.
"""


class FixedPointStability(StrEnum):
    """Linear stability class of a fixed point of a one-dimensional map."""

    STABLE = "stable"
    UNSTABLE = "unstable"
    NON_HYPERBOLIC = "non_hyperbolic"


@dataclass(frozen=True, slots=True)
class FixedPoint:
    """A fixed point of a one-dimensional map together with its linear stability.

    Attributes
    ----------
    location
        The fixed point :math:`x^*`.
    multiplier
        The derivative :math:`f'(x^*)`.
    stability
        Classification derived from ``multiplier``.
    """

    location: float
    multiplier: float
    stability: FixedPointStability


def classify_map_fixed_point(
    multiplier: float, *, atol: float = DEFAULT_MULTIPLIER_ATOL
) -> FixedPointStability:
    """Classify a fixed point of a one-dimensional map from its multiplier.

    Parameters
    ----------
    multiplier
        The derivative of the map at the fixed point, :math:`f'(x^*)`.
    atol
        Absolute tolerance: values with ``abs(abs(multiplier) - 1) <= atol`` are
        classified as non-hyperbolic.

    Returns
    -------
    FixedPointStability
        ``STABLE`` if ``|multiplier| < 1 - atol``, ``UNSTABLE`` if
        ``|multiplier| > 1 + atol``, otherwise ``NON_HYPERBOLIC``.

    Raises
    ------
    TypeError
        If ``multiplier`` or ``atol`` is not a real number.
    InputValidationError
        If ``multiplier`` or ``atol`` is NaN or infinite, or ``atol`` is negative.
    """
    magnitude = abs(validate_finite_real(multiplier, name="multiplier"))
    tolerance = validate_finite_real(atol, name="atol")
    if tolerance < 0.0:
        raise InputValidationError(f"atol must be non-negative, got {tolerance}.")
    if magnitude < 1.0 - tolerance:
        return FixedPointStability.STABLE
    if magnitude > 1.0 + tolerance:
        return FixedPointStability.UNSTABLE
    return FixedPointStability.NON_HYPERBOLIC

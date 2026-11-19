r"""Linear stability of fixed points of maps and of equilibria of flows.

**Maps.** For a one-dimensional map :math:`x_{t+1} = f(x_t)` with a fixed point
:math:`x^* = f(x^*)`, a small perturbation :math:`\varepsilon_t = x_t - x^*` evolves,
to first order, as :math:`\varepsilon_{t+1} \approx \lambda \varepsilon_t` with
multiplier :math:`\lambda = f'(x^*)`. Hence:

* :math:`|\lambda| < 1`: perturbations shrink, the fixed point is asymptotically stable;
* :math:`|\lambda| > 1`: perturbations grow, the fixed point is unstable;
* :math:`|\lambda| = 1`: non-hyperbolic case; the linearization is inconclusive and
  higher-order terms decide. Bifurcations happen at such points.

**Flows.** For an autonomous system :math:`\dot{\mathbf x} = F(\mathbf x)` with an
equilibrium :math:`F(\mathbf x^*) = 0`, a perturbation evolves, to first order, as
:math:`\dot{\boldsymbol\varepsilon} \approx J \boldsymbol\varepsilon` with
:math:`J = DF(\mathbf x^*)`. With :math:`\mu_i` the eigenvalues of :math:`J`:

* every :math:`\operatorname{Re}\mu_i < 0`: asymptotically stable;
* some :math:`\operatorname{Re}\mu_i > 0`: unstable (this holds even if other
  eigenvalues lie on the imaginary axis);
* otherwise some eigenvalue lies on the imaginary axis and none to its right:
  non-hyperbolic, the linearization is inconclusive.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final

import numpy as np
import numpy.typing as npt

from quantlab._validation import validate_finite_real
from quantlab.exceptions import InputValidationError

DEFAULT_MULTIPLIER_ATOL: Final[float] = 1e-12
"""Half-width of the band around ``|multiplier| = 1`` treated as non-hyperbolic.

A multiplier computed in floating point carries rounding error, so a value such
as ``-1.0000000000000002`` is classified as non-hyperbolic rather than unstable.
"""

DEFAULT_EIGENVALUE_ATOL: Final[float] = 1e-10
"""Half-width of the band around ``Re(eigenvalue) = 0`` treated as non-hyperbolic.

Eigenvalues computed by a backward-stable method carry an error of order
``eps * norm(J)``: about ``2e-15`` for the Lorenz Jacobian at its equilibria,
where ``norm(J)`` is between 15 and 30. The default leaves five orders of
magnitude of margin, and still separates the Lorenz Hopf bifurcation from a
parameter ``1e-6`` away from it, where the real part is about ``3e-8``.
"""


class FixedPointStability(StrEnum):
    """Linear stability class of a fixed point of a map or an equilibrium of a flow."""

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


@dataclass(frozen=True, slots=True)
class Equilibrium:
    r"""An equilibrium of a continuous-time system together with its linear stability.

    Attributes
    ----------
    location
        The equilibrium :math:`\mathbf x^*`, one coordinate per state variable.
    eigenvalues
        Eigenvalues of the Jacobian at :math:`\mathbf x^*`, sorted by decreasing real
        part and then by decreasing imaginary part.
    stability
        Classification derived from ``eigenvalues``.
    """

    location: tuple[float, ...]
    eigenvalues: tuple[complex, ...]
    stability: FixedPointStability


def _validated_atol(atol: object) -> float:
    tolerance = validate_finite_real(atol, name="atol")
    if tolerance < 0.0:
        raise InputValidationError(f"atol must be non-negative, got {tolerance}.")
    return tolerance


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
    tolerance = _validated_atol(atol)
    if magnitude < 1.0 - tolerance:
        return FixedPointStability.STABLE
    if magnitude > 1.0 + tolerance:
        return FixedPointStability.UNSTABLE
    return FixedPointStability.NON_HYPERBOLIC


def _validated_eigenvalues(eigenvalues: npt.ArrayLike) -> npt.NDArray[np.complex128]:
    try:
        values = np.asarray(eigenvalues, dtype=np.complex128)
    except (TypeError, ValueError) as error:
        raise TypeError(f"eigenvalues must be numbers: {error}") from error
    if values.ndim != 1 or values.size == 0:
        raise InputValidationError(
            f"eigenvalues must be a non-empty one-dimensional sequence, got shape {values.shape}."
        )
    if not np.isfinite(values).all():
        raise InputValidationError("eigenvalues contain NaN or infinite values.")
    return values


def classify_flow_equilibrium(
    eigenvalues: npt.ArrayLike, *, atol: float = DEFAULT_EIGENVALUE_ATOL
) -> FixedPointStability:
    """Classify an equilibrium of a continuous-time system from its Jacobian eigenvalues.

    Parameters
    ----------
    eigenvalues
        Eigenvalues of the Jacobian at the equilibrium, real or complex.
    atol
        Absolute tolerance: real parts with ``abs(real) <= atol`` are treated as zero.

    Returns
    -------
    FixedPointStability
        ``UNSTABLE`` if some real part exceeds ``atol``; otherwise ``STABLE`` if every
        real part is below ``-atol``; otherwise ``NON_HYPERBOLIC``.

    Raises
    ------
    TypeError
        If ``eigenvalues`` does not hold numbers, or ``atol`` is not a real number.
    InputValidationError
        If ``eigenvalues`` is empty, not one-dimensional or not finite, or ``atol`` is
        negative or not finite.
    """
    real_parts = _validated_eigenvalues(eigenvalues).real
    tolerance = _validated_atol(atol)
    if np.any(real_parts > tolerance):
        return FixedPointStability.UNSTABLE
    if np.all(real_parts < -tolerance):
        return FixedPointStability.STABLE
    return FixedPointStability.NON_HYPERBOLIC


def analyze_equilibrium(
    location: npt.ArrayLike,
    jacobian: npt.ArrayLike,
    *,
    atol: float = DEFAULT_EIGENVALUE_ATOL,
) -> Equilibrium:
    r"""Linearize a continuous-time system at an equilibrium and classify it.

    The caller is responsible for ``location`` being an equilibrium
    (:math:`F(\mathbf x^*) = 0`); this function only analyzes the Jacobian there.

    Parameters
    ----------
    location
        The equilibrium, a one-dimensional sequence of ``n`` finite real numbers.
    jacobian
        The ``n x n`` Jacobian matrix of the vector field at ``location``.
    atol
        Tolerance passed to :func:`classify_flow_equilibrium`.

    Returns
    -------
    Equilibrium
        The location, the eigenvalues (sorted by decreasing real part, then by
        decreasing imaginary part) and the stability class.

    Raises
    ------
    TypeError
        If ``location`` or ``jacobian`` does not hold real numbers, or ``atol`` is not
        a real number.
    InputValidationError
        If the shapes do not match, the values are not finite, or ``atol`` is invalid.
    """
    point = np.asarray(location)
    matrix = np.asarray(jacobian)
    if point.dtype.kind not in "iuf" or matrix.dtype.kind not in "iuf":
        raise TypeError("location and jacobian must contain real numbers.")
    if point.ndim != 1 or point.size == 0:
        raise InputValidationError(
            f"location must be a non-empty one-dimensional sequence, got shape {point.shape}."
        )
    dimension = point.size
    if matrix.shape != (dimension, dimension):
        raise InputValidationError(
            f"jacobian must have shape ({dimension}, {dimension}), got {matrix.shape}."
        )
    if not (np.isfinite(point).all() and np.isfinite(matrix).all()):
        raise InputValidationError("location and jacobian must be finite.")

    computed = np.linalg.eigvals(matrix.astype(np.float64)).astype(np.complex128)
    ordered = sorted((complex(value) for value in computed), key=lambda v: (-v.real, -v.imag))
    return Equilibrium(
        location=tuple(float(coordinate) for coordinate in point),
        eigenvalues=tuple(ordered),
        stability=classify_flow_equilibrium(ordered, atol=atol),
    )

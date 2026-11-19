r"""Historical Value at Risk (VaR) and Conditional Value at Risk (CVaR).

Both are computed from the empirical distribution of past returns, without
assuming any parametric model. Losses are returns with the sign flipped,
:math:`L_t = -x_t`, and both measures are reported as *losses*: a VaR of 0.021
at 95% means that 95% of the observed returns were above -2.1%.

At confidence level :math:`\alpha` (for example 0.95), with sorted losses
:math:`L_{(1)} \le \dots \le L_{(n)}`:

.. math::

    \text{VaR}_\alpha = L_{(\lceil n\alpha \rceil)}

    \text{CVaR}_\alpha = \frac{1}{m}
        \left[ \sum_{i=1}^{\lfloor m \rfloor} L_{[i]}
        + (m - \lfloor m \rfloor)\, L_{[\lfloor m \rfloor + 1]} \right],
    \qquad m = n(1 - \alpha)

where :math:`L_{[i]}` is the :math:`i`-th *largest* loss. VaR is the empirical
:math:`\alpha`-quantile of losses (the generalized inverse of their distribution
function). CVaR, also called Expected Shortfall, is the average of the worst
:math:`(1-\alpha)` fraction of outcomes, with the boundary observation weighted
fractionally (Acerbi and Tasche, 2002). This makes CVaR a coherent risk measure
and guarantees :math:`\text{CVaR}_\alpha \ge \text{VaR}_\alpha`.

Both refer to the horizon of the input returns (one day for daily returns).
See ``docs/math/desempenho-e-risco.md``.
"""

from __future__ import annotations

import math

import numpy as np
import numpy.typing as npt

from quantlab._validation import validate_open_unit_interval, validate_series
from quantlab.types import NumericSeries

_MIN_OBSERVATIONS = 2
_TAIL_SIZE_SLACK = 1e-9
"""Absorbs rounding in 1 / (1 - confidence), e.g. 1 / (1 - 0.99) = 100.00000000000009."""


def _losses(returns: object, confidence: object) -> tuple[npt.NDArray[np.float64], float]:
    """Validate the inputs and return the losses and the confidence level.

    The tail must hold at least one whole observation, ``n * (1 - confidence) >= 1``:
    below that, the estimate is just the single worst loss relabelled.
    """
    level = validate_open_unit_interval(confidence, name="confidence")
    min_length = max(_MIN_OBSERVATIONS, math.ceil(1.0 / (1.0 - level) - _TAIL_SIZE_SLACK))
    validated = validate_series(returns, name="returns", min_length=min_length)
    losses = np.asarray(-validated.to_numpy(), dtype=np.float64)
    return losses, level


def historical_var(returns: NumericSeries, *, confidence: float = 0.95) -> float:
    r"""Compute the historical Value at Risk of a return series.

    Parameters
    ----------
    returns
        Simple returns of one period, sorted by a unique, increasing index, with no
        missing or infinite values. At least ``ceil(1 / (1 - confidence))``
        observations are required (20 at 95%, 100 at 99%), so that the tail holds
        at least one observation.
    confidence
        Confidence level :math:`\alpha`, strictly between 0 and 1.

    Returns
    -------
    float
        The VaR as a loss: positive when the :math:`\alpha`-quantile of losses is a
        loss, negative if even that quantile is a gain.

    Raises
    ------
    TypeError
        If ``returns`` is not a numeric Series or ``confidence`` is not a real number.
    InputValidationError
        If the data contain missing or infinite values, the index is not strictly
        increasing, or ``confidence`` is NaN or infinite.
    DomainError
        If ``confidence`` is not strictly between 0 and 1.
    InsufficientDataError
        If there are too few observations for the requested confidence.

    Notes
    -----
    Uses ``numpy.quantile(..., method="inverted_cdf")``, which is exactly the
    generalized inverse :math:`\inf\{l : F_n(l) \ge \alpha\}` of the empirical
    distribution. The estimate is always one of the observed losses: it does not
    interpolate between them.
    """
    losses, level = _losses(returns, confidence)
    return float(np.quantile(losses, level, method="inverted_cdf"))


def historical_cvar(returns: NumericSeries, *, confidence: float = 0.95) -> float:
    """Compute the historical Conditional Value at Risk (Expected Shortfall).

    Parameters
    ----------
    returns
        Same requirements as in :func:`historical_var`.
    confidence
        Confidence level, strictly between 0 and 1.

    Returns
    -------
    float
        The CVaR as a loss. Always greater than or equal to :func:`historical_var`
        at the same confidence level.

    Raises
    ------
    TypeError, InputValidationError, DomainError, InsufficientDataError
        Same conditions as in :func:`historical_var`.

    Notes
    -----
    The fractional weight of the boundary observation makes the estimator
    continuous in ``confidence``, so rounding in ``n * (1 - confidence)`` changes
    the result only by a negligible amount.

    References
    ----------
    Acerbi, C. and Tasche, D. (2002). On the coherence of Expected Shortfall.
    *Journal of Banking & Finance* 26(7), 1487-1503.
    """
    losses, level = _losses(returns, confidence)
    largest_first = np.sort(losses)[::-1]
    tail_mass = losses.size * (1.0 - level)
    # confidence > 0 implies tail_mass < n, so the boundary index `whole` always exists.
    whole = math.floor(tail_mass)
    total = float(np.sum(largest_first[:whole]))
    total += (tail_mass - whole) * float(largest_first[whole])
    return total / tail_mass

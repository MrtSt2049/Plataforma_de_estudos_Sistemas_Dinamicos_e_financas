r"""Simple, logarithmic and cumulative returns of a price series.

Notation
--------
:math:`P_t`
    Price at observation :math:`t`, for :math:`t = 0, \dots, n`.
:math:`R_t`
    Simple (arithmetic) return, :math:`R_t = P_t / P_{t-1} - 1`.
:math:`r_t`
    Logarithmic return, :math:`r_t = \ln(P_t / P_{t-1}) = \ln(1 + R_t)`.

Assumptions
-----------
* Prices are strictly positive and ordered in time.
* Consecutive observations are what the caller wants to compare. Returns do not
  require evenly spaced observations, but annualizing them does (see
  :mod:`quantlab.analysis.volatility`).
* The series is homogeneous: do not mix adjusted and unadjusted prices
  (RULE 040). Use prices adjusted for splits and dividends when the goal is
  total return.

The full derivation and limitations are in ``docs/math/retornos-e-volatilidade.md``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from quantlab._validation import require_at_least, validate_price_series, validate_series
from quantlab.types import NumericSeries

_MIN_RETURNS = 1
_TOTAL_LOSS = -1.0


def simple_returns(prices: NumericSeries) -> pd.Series[float]:
    r"""Compute simple (arithmetic) returns from a price series.

    .. math::

        R_t = \frac{P_t - P_{t-1}}{P_{t-1}}, \qquad t = 1, \dots, n

    Parameters
    ----------
    prices
        Strictly positive prices, sorted by a unique, increasing index, with at
        least two observations and no missing or infinite values.

    Returns
    -------
    pandas.Series
        float64 series of length ``len(prices) - 1``. Each return is labelled with
        the index of the *later* observation of its pair. The first observation has
        no return and is dropped rather than filled with NaN. The name of
        ``prices`` is kept.

    Raises
    ------
    TypeError
        If ``prices`` is not a numeric :class:`pandas.Series`.
    InsufficientDataError
        If there are fewer than two prices.
    InputValidationError
        If there are missing or infinite values, or the index is not strictly increasing.
    DomainError
        If any price is zero or negative.

    Notes
    -----
    The return is computed as a difference divided by the previous price rather
    than as ``P_t / P_{t-1} - 1``. Subtracting two nearby floating-point prices is
    exact (Sterbenz lemma), so small returns keep their full relative precision;
    forming the ratio first and then subtracting one would cancel leading digits.
    """
    validated = validate_price_series(prices)
    values = validated.to_numpy()
    returns = np.diff(values) / values[:-1]
    return pd.Series(returns, index=validated.index[1:], name=validated.name)


def log_returns(prices: NumericSeries) -> pd.Series[float]:
    r"""Compute logarithmic (continuously compounded) returns from a price series.

    .. math::

        r_t = \ln\left(\frac{P_t}{P_{t-1}}\right) = \ln(1 + R_t), \qquad t = 1, \dots, n

    Log returns add up over time: :math:`\sum_{t=1}^{n} r_t = \ln(P_n / P_0)`.

    Parameters
    ----------
    prices
        Same requirements as in :func:`simple_returns`.

    Returns
    -------
    pandas.Series
        float64 series of length ``len(prices) - 1``, labelled like
        :func:`simple_returns`.

    Raises
    ------
    TypeError, InsufficientDataError, InputValidationError, DomainError
        Same conditions as in :func:`simple_returns`.

    Notes
    -----
    Computed as ``log1p`` of the simple return. For small price moves this keeps
    the relative precision that ``log(P_t) - log(P_{t-1})`` would lose to
    cancellation.
    """
    simple = simple_returns(prices)
    return pd.Series(np.log1p(simple.to_numpy()), index=simple.index, name=simple.name)


def cumulative_returns(returns: NumericSeries) -> pd.Series[float]:
    r"""Compound a series of simple returns into cumulative returns.

    .. math::

        C_t = \prod_{s=1}^{t} (1 + R_s) - 1

    If the returns come from :func:`simple_returns`, then
    :math:`C_t = P_t / P_0 - 1`. To compound log returns, use
    ``numpy.expm1(log_returns.cumsum())`` instead, because log returns add rather
    than multiply.

    Parameters
    ----------
    returns
        Simple returns, sorted by a unique, increasing index, with at least one
        observation and no missing or infinite values. Each return must be
        ``>= -1``: a simple return below -100% is impossible for an unleveraged
        long position.

    Returns
    -------
    pandas.Series
        float64 series with the same index and name as ``returns``. A return of
        exactly -1 (total loss) makes every later cumulative return equal to -1.

    Raises
    ------
    TypeError
        If ``returns`` is not a numeric :class:`pandas.Series`.
    InsufficientDataError
        If ``returns`` is empty.
    InputValidationError
        If there are missing or infinite values, or the index is not strictly increasing.
    DomainError
        If any return is below -1.

    Notes
    -----
    The product is evaluated as ``expm1(cumsum(log1p(R)))``. Working with
    ``log1p`` and ``expm1`` avoids the loss of precision of ``1 + R`` and of the
    final subtraction of one when returns are small.
    """
    validated = validate_series(returns, name="returns", min_length=_MIN_RETURNS)
    require_at_least(
        validated,
        _TOTAL_LOSS,
        name="returns",
        reason="a simple return cannot be below a total loss of -100%",
    )
    # log1p(-1) = -inf is the intended representation of a total loss: every later
    # partial sum stays -inf and expm1(-inf) = -1 exactly.
    with np.errstate(divide="ignore"):
        log_growth = np.log1p(validated.to_numpy())
    cumulative = np.expm1(np.cumsum(log_growth))
    return pd.Series(cumulative, index=validated.index, name=validated.name)

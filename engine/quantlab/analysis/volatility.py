r"""Historical and annualized volatility of a return series.

Volatility here is the sample standard deviation of returns,

.. math::

    \hat\sigma = \sqrt{\frac{1}{n - \delta} \sum_{t=1}^{n} (x_t - \bar x)^2},

where :math:`x_t` are the returns, :math:`\bar x` their mean and :math:`\delta`
the delta degrees of freedom (``ddof``). With :math:`\delta = 1` the variance
estimator is unbiased under independent sampling.

Annualization multiplies by the square root of the number of periods per year,

.. math::

    \sigma_{\text{annual}} = \hat\sigma \sqrt{N}, \qquad N = 252 \text{ for daily trading data}.

This scaling assumes returns that are independent and identically distributed
with evenly spaced observations. It fails under volatility clustering and serial
correlation, which are common in real markets, so an annualized figure is a
convention for comparison, not a forecast. See ``docs/math/retornos-e-volatilidade.md``.
"""

from __future__ import annotations

import math
from typing import Final

import numpy as np

from quantlab._validation import validate_finite_real, validate_int, validate_series
from quantlab.exceptions import DomainError
from quantlab.types import NumericSeries

TRADING_DAYS_PER_YEAR: Final[int] = 252
"""Conventional number of trading sessions per year, used to annualize daily data."""

_MIN_OBSERVATIONS = 2


def historical_volatility(returns: NumericSeries, *, ddof: int = 1) -> float:
    """Compute the sample standard deviation of a return series.

    The result is in the units of the input: daily returns give a daily volatility.

    Parameters
    ----------
    returns
        Simple or log returns, sorted by a unique, increasing index, with no
        missing or infinite values. At least ``max(2, ddof + 1)`` observations are
        required: one observation carries no information about dispersion.
    ddof
        Delta degrees of freedom. The divisor is ``n - ddof``. The default ``1``
        gives the usual sample estimator; ``0`` gives the population formula.

    Returns
    -------
    float
        Non-negative volatility.

    Raises
    ------
    TypeError
        If ``returns`` is not a numeric :class:`pandas.Series` or ``ddof`` is not an integer.
    InputValidationError
        If ``ddof`` is negative, if there are missing or infinite values, or if the
        index is not strictly increasing.
    InsufficientDataError
        If there are fewer than ``max(2, ddof + 1)`` observations.

    Notes
    -----
    :func:`numpy.std` computes the mean first and then the squared deviations
    (two-pass algorithm), which is numerically stable. The one-pass formula
    ``E[x^2] - E[x]^2`` is avoided because it cancels catastrophically when the
    mean is large relative to the dispersion.
    """
    checked_ddof = validate_int(ddof, name="ddof", minimum=0)
    validated = validate_series(
        returns, name="returns", min_length=max(_MIN_OBSERVATIONS, checked_ddof + 1)
    )
    return float(np.std(validated.to_numpy(), ddof=checked_ddof))


def annualized_volatility(
    returns: NumericSeries,
    *,
    periods_per_year: float = TRADING_DAYS_PER_YEAR,
    ddof: int = 1,
) -> float:
    r"""Annualize the historical volatility with the square-root-of-time rule.

    .. math::

        \sigma_{\text{annual}} = \hat\sigma \sqrt{N}

    Parameters
    ----------
    returns
        Same requirements as in :func:`historical_volatility`.
    periods_per_year
        Number of return periods in one year, :math:`N`. Use 252 for daily trading
        data (the default), 52 for weekly and 12 for monthly returns.
    ddof
        Delta degrees of freedom, as in :func:`historical_volatility`.

    Returns
    -------
    float
        Non-negative annualized volatility.

    Raises
    ------
    TypeError
        If ``periods_per_year`` is not a real number, or for the reasons listed in
        :func:`historical_volatility`.
    InputValidationError
        If ``periods_per_year`` is NaN or infinite, or for the reasons listed in
        :func:`historical_volatility`.
    DomainError
        If ``periods_per_year`` is not strictly positive.
    InsufficientDataError
        As in :func:`historical_volatility`.

    Notes
    -----
    The rule is exact only for i.i.d. returns observed at evenly spaced times.
    Under volatility clustering or autocorrelation it misstates the volatility of
    longer horizons.
    """
    periods = validate_finite_real(periods_per_year, name="periods_per_year")
    if periods <= 0.0:
        raise DomainError(f"periods_per_year must be strictly positive, got {periods}.")
    return historical_volatility(returns, ddof=ddof) * math.sqrt(periods)

r"""Risk-adjusted performance: the Sharpe ratio.

.. math::

    \text{SR} = \frac{\overline{x - r_f}}{\hat\sigma(x - r_f)} \sqrt{N}

where :math:`x_t` are simple returns per period, :math:`r_f` the risk-free rate
for the same period and :math:`N` the number of periods per year. The ratio
measures the average excess return earned per unit of volatility.

Limitations (see ``docs/math/desempenho-e-risco.md``): the :math:`\sqrt{N}`
annualization assumes i.i.d. returns, and a Sharpe ratio estimated from a short
sample carries a large sampling error.
"""

from __future__ import annotations

import math

import numpy as np

from quantlab._numerics import dispersion_is_negligible
from quantlab._validation import (
    validate_finite_real,
    validate_int,
    validate_positive_real,
    validate_series,
)
from quantlab.analysis.volatility import TRADING_DAYS_PER_YEAR
from quantlab.exceptions import ComputationError, DomainError
from quantlab.types import NumericSeries

_MIN_OBSERVATIONS = 2
_TOTAL_LOSS = -1.0


def periodic_rate_from_annual(
    annual_rate: float, *, periods_per_year: float = TRADING_DAYS_PER_YEAR
) -> float:
    r"""Convert an effective annual rate into the equivalent rate per period.

    .. math::

        r_{\text{period}} = (1 + r_{\text{annual}})^{1/N} - 1

    Use it to turn an annual risk-free rate (for example the CDI or a Treasury
    yield, quoted as an effective annual rate) into the per-period rate expected by
    :func:`sharpe_ratio`.

    Parameters
    ----------
    annual_rate
        Effective annual rate as a fraction (0.10 for 10% a year). Must be > -1.
    periods_per_year
        Number of periods in one year, :math:`N`.

    Returns
    -------
    float
        The compounded-equivalent rate per period.

    Raises
    ------
    TypeError
        If an argument is not a real number.
    InputValidationError
        If an argument is NaN or infinite.
    DomainError
        If ``annual_rate <= -1`` or ``periods_per_year <= 0``.

    Notes
    -----
    Evaluated as ``expm1(log1p(r) / N)`` to keep full precision for small rates.
    Brazilian rates such as the CDI are quoted on a 252 business-day basis, which is
    the default here.
    """
    rate = validate_finite_real(annual_rate, name="annual_rate")
    if rate <= _TOTAL_LOSS:
        raise DomainError(f"annual_rate must be greater than -1, got {rate}.")
    periods = validate_positive_real(periods_per_year, name="periods_per_year")
    return math.expm1(math.log1p(rate) / periods)


def sharpe_ratio(
    returns: NumericSeries,
    *,
    risk_free_rate: float = 0.0,
    periods_per_year: float = TRADING_DAYS_PER_YEAR,
    ddof: int = 1,
) -> float:
    r"""Compute the annualized Sharpe ratio of a series of simple returns.

    .. math::

        \text{SR} = \frac{\overline{x - r_f}}{\hat\sigma(x - r_f)} \sqrt{N}

    Parameters
    ----------
    returns
        Simple returns per period, sorted by a unique, increasing index, with no
        missing or infinite values and at least ``max(2, ddof + 1)`` observations.
    risk_free_rate
        Risk-free rate *per period* (not per year), as a fraction. Convert an annual
        rate with :func:`periodic_rate_from_annual`. Defaults to 0.
    periods_per_year
        Number of return periods in one year, :math:`N`. Use ``1`` to get the
        non-annualized, per-period ratio.
    ddof
        Delta degrees of freedom of the standard deviation.

    Returns
    -------
    float
        The annualized Sharpe ratio. Negative when the average excess return is
        negative.

    Raises
    ------
    TypeError
        If ``returns`` is not a numeric Series, or a parameter has the wrong type.
    InputValidationError
        If the data contain missing or infinite values, the index is not strictly
        increasing, or a parameter is NaN, infinite or out of range.
    DomainError
        If ``periods_per_year`` is not strictly positive.
    InsufficientDataError
        If there are fewer than ``max(2, ddof + 1)`` observations.
    ComputationError
        If the excess returns have zero dispersion, or a dispersion at the level of
        floating-point rounding: the ratio is then undefined.

    Notes
    -----
    A constant risk-free rate shifts every return by the same amount and does not
    change the standard deviation, only the mean. Under i.i.d. returns the standard
    error of the per-period estimate is roughly :math:`\sqrt{(1 + \text{SR}^2/2)/n}`
    (Lo, 2002), so samples of a few months give very imprecise ratios.

    References
    ----------
    Sharpe, W. F. (1994). The Sharpe Ratio. *Journal of Portfolio Management* 21(1).
    Lo, A. W. (2002). The Statistics of Sharpe Ratios. *Financial Analysts Journal* 58(4).
    """
    checked_ddof = validate_int(ddof, name="ddof", minimum=0)
    rate = validate_finite_real(risk_free_rate, name="risk_free_rate")
    periods = validate_positive_real(periods_per_year, name="periods_per_year")
    validated = validate_series(
        returns, name="returns", min_length=max(_MIN_OBSERVATIONS, checked_ddof + 1)
    )

    excess = validated.to_numpy() - rate
    dispersion = float(np.std(excess, ddof=checked_ddof))
    if dispersion_is_negligible(excess, dispersion):
        raise ComputationError(
            "The Sharpe ratio is undefined: the excess returns have zero dispersion "
            f"(computed standard deviation {dispersion:.3e} is at rounding level)."
        )
    return float(np.mean(excess)) / dispersion * math.sqrt(periods)

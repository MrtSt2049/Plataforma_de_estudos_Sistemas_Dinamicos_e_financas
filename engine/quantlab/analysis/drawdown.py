r"""Drawdowns: declines from the running maximum of a price or wealth series.

.. math::

    M_t = \max_{s \le t} P_s, \qquad D_t = \frac{P_t - M_t}{M_t} \le 0,
    \qquad \text{MDD} = \min_t D_t

:math:`D_t` is the fraction lost relative to the best level reached so far. The
maximum drawdown (MDD) is the worst such loss over the sample, reported as a
non-positive number (-0.35 for a fall of 35%).
"""

from __future__ import annotations

from collections.abc import Hashable
from dataclasses import dataclass

import numpy as np
import pandas as pd

from quantlab._validation import validate_price_series
from quantlab.types import NumericSeries


@dataclass(frozen=True, slots=True)
class MaxDrawdown:
    """The worst peak-to-trough decline of a series.

    Attributes
    ----------
    value
        Maximum drawdown as a non-positive fraction: -0.35 means a 35% fall.
        ``0.0`` when the series never falls below a previous maximum.
    peak
        Index label of the maximum that precedes the trough, or ``None`` when
        ``value`` is 0. When the maximum level is reached several times, the latest
        occurrence before the trough is used.
    trough
        Index label of the lowest point of the worst decline, or ``None`` when
        ``value`` is 0.
    recovery
        Index label of the first observation after the trough at or above the peak
        level, or ``None`` if the series has not recovered by its end (or ``value``
        is 0).
    """

    value: float
    peak: Hashable | None
    trough: Hashable | None
    recovery: Hashable | None


def drawdowns(prices: NumericSeries) -> pd.Series[float]:
    r"""Compute the drawdown at each observation, :math:`D_t = P_t / M_t - 1`.

    Parameters
    ----------
    prices
        Strictly positive prices or wealth levels, sorted by a unique, increasing
        index, with at least two observations and no missing or infinite values. To
        analyse a return series, pass the wealth index ``1 + cumulative_returns(r)``
        preceded by the initial level ``1``.

    Returns
    -------
    pandas.Series
        Non-positive float64 series with the same index and name as ``prices``.
        It equals 0 exactly at every new maximum.

    Raises
    ------
    TypeError, InsufficientDataError, InputValidationError, DomainError
        Same conditions as in :func:`quantlab.analysis.simple_returns`.

    Notes
    -----
    Computed as :math:`(P_t - M_t) / M_t` so that small declines keep their
    relative precision (the subtraction of close values is exact).
    """
    validated = validate_price_series(prices)
    values = validated.to_numpy()
    running_max = np.maximum.accumulate(values)
    return pd.Series(
        (values - running_max) / running_max, index=validated.index, name=validated.name
    )


def max_drawdown(prices: NumericSeries) -> MaxDrawdown:
    """Find the maximum drawdown with its peak, trough and recovery dates.

    Parameters
    ----------
    prices
        Same requirements as in :func:`drawdowns`.

    Returns
    -------
    MaxDrawdown
        Value and location of the worst decline. If several declines tie for the
        worst value, the first one is reported.

    Raises
    ------
    TypeError, InsufficientDataError, InputValidationError, DomainError
        Same conditions as in :func:`drawdowns`.
    """
    drawdown = drawdowns(prices)
    values = drawdown.to_numpy()
    trough_position = int(np.argmin(values))
    worst = float(values[trough_position])
    if worst == 0.0:
        return MaxDrawdown(value=0.0, peak=None, trough=None, recovery=None)

    price_values = validate_price_series(prices).to_numpy()
    peak_level = float(np.max(price_values[: trough_position + 1]))
    peak_position = int(np.flatnonzero(price_values[: trough_position + 1] == peak_level)[-1])
    recovered = np.flatnonzero(price_values[trough_position + 1 :] >= peak_level)
    recovery = drawdown.index[trough_position + 1 + int(recovered[0])] if recovered.size else None

    return MaxDrawdown(
        value=worst,
        peak=drawdown.index[peak_position],
        trough=drawdown.index[trough_position],
        recovery=recovery,
    )

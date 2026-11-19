r"""Moving-average indicators of a time series.

Simple moving average over a window of :math:`w` observations:

.. math::

    \text{SMA}_t = \frac{1}{w} \sum_{i=0}^{w-1} x_{t-i}

Exponential moving average with span :math:`s`:

.. math::

    \text{EMA}_t = a\, x_t + (1 - a)\, \text{EMA}_{t-1}, \qquad
    a = \frac{2}{s + 1}, \qquad \text{EMA}_0 = x_0

Both smooth the series and lag behind it. They describe the past; on their own
they are not evidence of predictability.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

from quantlab._validation import validate_int, validate_series
from quantlab.exceptions import InsufficientDataError
from quantlab.types import NumericSeries

_MIN_WINDOW = 1


def simple_moving_average(series: NumericSeries, window: int) -> pd.Series[float]:
    """Compute the simple moving average over a window of consecutive observations.

    Parameters
    ----------
    series
        Values sorted by a unique, increasing index, with no missing or infinite
        values and at least ``window`` observations.
    window
        Number of observations averaged, ``>= 1``. ``window=1`` returns the series.

    Returns
    -------
    pandas.Series
        float64 series of length ``len(series) - window + 1``, each value labelled
        with the *last* observation of its window. Positions without a complete
        window are dropped rather than filled with NaN.

    Raises
    ------
    TypeError
        If ``series`` is not a numeric Series or ``window`` is not an integer.
    InputValidationError
        If ``window < 1``, the data contain missing or infinite values, or the index
        is not strictly increasing.
    InsufficientDataError
        If there are fewer than ``window`` observations.
    """
    width = validate_int(window, name="window", minimum=_MIN_WINDOW)
    validated = validate_series(series, name="series", min_length=_MIN_WINDOW)
    if len(validated) < width:
        raise InsufficientDataError(
            f"series needs at least window={width} observations, got {len(validated)}."
        )
    averages = sliding_window_view(validated.to_numpy(), width).mean(axis=1)
    return pd.Series(averages, index=validated.index[width - 1 :], name=validated.name)


def exponential_moving_average(series: NumericSeries, span: int) -> pd.Series[float]:
    r"""Compute the exponential moving average with smoothing :math:`a = 2/(s+1)`.

    Parameters
    ----------
    series
        Values sorted by a unique, increasing index, with no missing or infinite
        values and at least one observation.
    span
        Span :math:`s \ge 1`. A larger span gives a smoother, slower average;
        ``span=1`` returns the series unchanged.

    Returns
    -------
    pandas.Series
        float64 series with the same index and name as ``series``.

    Raises
    ------
    TypeError
        If ``series`` is not a numeric Series or ``span`` is not an integer.
    InputValidationError
        If ``span < 1``, the data contain missing or infinite values, or the index is
        not strictly increasing.
    InsufficientDataError
        If ``series`` is empty.

    Notes
    -----
    The recursion starts at :math:`\text{EMA}_0 = x_0`, so early values are biased
    toward the first observation. The weight of that start decays as
    :math:`(1-a)^t`; after about :math:`3s` observations it falls below 5%.
    Evaluated with ``pandas.Series.ewm(span=s, adjust=False)``, which implements
    exactly this recursion.
    """
    width = validate_int(span, name="span", minimum=_MIN_WINDOW)
    validated = validate_series(series, name="series", min_length=_MIN_WINDOW)
    smoothed = validated.ewm(span=width, adjust=False).mean()
    return pd.Series(
        smoothed.to_numpy(dtype=np.float64), index=validated.index, name=validated.name
    )

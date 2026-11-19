"""Input validation shared by the engine's public functions (RULE 016).

This module is private. Public functions call these helpers so that every
algorithm rejects bad input the same way and with the same messages, instead of
each one re-implementing its own checks (RULE 003).

The helpers never repair data: they do not drop missing values, sort indexes or
clip values into a domain. Cleaning belongs to the Market Data module; the
analysis code only verifies that it received clean data.
"""

from __future__ import annotations

import math
from numbers import Integral, Real

import numpy as np
import numpy.typing as npt
import pandas as pd

from quantlab.exceptions import DomainError, InputValidationError, InsufficientDataError

_MAX_REPORTED_LABELS = 5


def _describe_labels(labels: pd.Index) -> str:
    """Return a short, readable list of index labels for error messages."""
    shown = ", ".join(repr(label) for label in labels[:_MAX_REPORTED_LABELS])
    if len(labels) > _MAX_REPORTED_LABELS:
        shown += f", ... ({len(labels) - _MAX_REPORTED_LABELS} more)"
    return f"[{shown}]"


def validate_series(series: object, *, name: str, min_length: int) -> pd.Series[float]:
    """Check that ``series`` is a clean numeric time series and return it as float64.

    Parameters
    ----------
    series
        Object to validate. Must be a :class:`pandas.Series`.
    name
        Name of the argument, used in error messages.
    min_length
        Minimum number of observations required.

    Returns
    -------
    pandas.Series
        A new float64 series with the same index and name. The input is not modified.

    Raises
    ------
    TypeError
        If ``series`` is not a Series or does not have a numeric, non-boolean dtype.
    InsufficientDataError
        If it has fewer than ``min_length`` observations.
    InputValidationError
        If it contains missing or infinite values, or if its index has duplicated
        labels or is not sorted in increasing (temporal) order.
    """
    if not isinstance(series, pd.Series):
        raise TypeError(f"{name} must be a pandas Series, got {type(series).__name__}.")
    if pd.api.types.is_bool_dtype(series.dtype) or not pd.api.types.is_numeric_dtype(series.dtype):
        raise TypeError(f"{name} must have a numeric dtype, got {series.dtype}.")
    if len(series) < min_length:
        raise InsufficientDataError(
            f"{name} needs at least {min_length} observation(s), got {len(series)}."
        )

    values = series.to_numpy(dtype=np.float64, na_value=np.nan)

    missing = np.isnan(values)
    if missing.any():
        raise InputValidationError(
            f"{name} contains {int(missing.sum())} missing value(s) at "
            f"{_describe_labels(series.index[missing])}. Clean the data before calling."
        )
    infinite = np.isinf(values)
    if infinite.any():
        raise InputValidationError(
            f"{name} contains {int(infinite.sum())} non-finite value(s) at "
            f"{_describe_labels(series.index[infinite])}."
        )

    index = series.index
    if not index.is_unique:
        duplicated = index[index.duplicated()].unique()
        raise InputValidationError(
            f"{name} has duplicated index labels: {_describe_labels(duplicated)}."
        )
    if not index.is_monotonic_increasing:
        raise InputValidationError(
            f"{name} must be sorted by its index in increasing (temporal) order."
        )

    return pd.Series(values, index=index, name=series.name, copy=False)


def require_strictly_positive(series: pd.Series[float], *, name: str) -> None:
    """Raise :class:`DomainError` if any value of ``series`` is zero or negative."""
    non_positive = series.to_numpy() <= 0.0
    if non_positive.any():
        raise DomainError(
            f"{name} must be strictly positive; found {int(non_positive.sum())} value(s) <= 0 "
            f"at {_describe_labels(series.index[non_positive])}."
        )


def require_at_least(series: pd.Series[float], bound: float, *, name: str, reason: str) -> None:
    """Raise :class:`DomainError` if any value of ``series`` is below ``bound``."""
    below = series.to_numpy() < bound
    if below.any():
        raise DomainError(
            f"{name} must be >= {bound} ({reason}); found {int(below.sum())} value(s) below "
            f"at {_describe_labels(series.index[below])}."
        )


def validate_finite_real(value: object, *, name: str) -> float:
    """Return ``value`` as a float after checking that it is a finite real number.

    Raises
    ------
    TypeError
        If ``value`` is not a real number (booleans are rejected).
    InputValidationError
        If ``value`` is NaN or infinite.
    """
    if isinstance(value, bool | np.bool_) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real number, got {type(value).__name__}.")
    as_float = float(value)
    if not math.isfinite(as_float):
        raise InputValidationError(f"{name} must be finite, got {as_float}.")
    return as_float


def validate_closed_interval(value: object, *, name: str, lower: float, upper: float) -> float:
    """Return ``value`` as a float after checking that ``lower <= value <= upper``.

    Raises
    ------
    TypeError
        If ``value`` is not a real number.
    InputValidationError
        If ``value`` is NaN or infinite.
    DomainError
        If ``value`` lies outside ``[lower, upper]``.
    """
    as_float = validate_finite_real(value, name=name)
    if not lower <= as_float <= upper:
        raise DomainError(f"{name} must lie in [{lower}, {upper}], got {as_float}.")
    return as_float


def validate_int(value: object, *, name: str, minimum: int) -> int:
    """Return ``value`` as an int after checking that it is an integer ``>= minimum``.

    Raises
    ------
    TypeError
        If ``value`` is not an integer (booleans and floats such as ``3.0`` are rejected).
    InputValidationError
        If ``value`` is smaller than ``minimum``.
    """
    if isinstance(value, bool | np.bool_) or not isinstance(value, Integral):
        raise TypeError(f"{name} must be an integer, got {type(value).__name__}.")
    as_int = int(value)
    if as_int < minimum:
        raise InputValidationError(f"{name} must be >= {minimum}, got {as_int}.")
    return as_int


def validate_orbit(orbit: npt.ArrayLike, *, name: str, min_length: int) -> npt.NDArray[np.float64]:
    """Return a one-dimensional, finite float64 copy of ``orbit``.

    Raises
    ------
    InputValidationError
        If ``orbit`` is not one-dimensional or contains NaN or infinite values.
    InsufficientDataError
        If it has fewer than ``min_length`` points.
    """
    values = np.array(orbit, dtype=np.float64)
    if values.ndim != 1:
        raise InputValidationError(
            f"{name} must be one-dimensional, got an array with shape {values.shape}."
        )
    if values.size < min_length:
        raise InsufficientDataError(
            f"{name} needs at least {min_length} point(s), got {values.size}."
        )
    if not np.isfinite(values).all():
        raise InputValidationError(f"{name} contains NaN or infinite values.")
    return values

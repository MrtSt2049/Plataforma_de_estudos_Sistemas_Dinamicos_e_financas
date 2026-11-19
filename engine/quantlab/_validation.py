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


def validate_series(
    series: object, *, name: str, min_length: int, allow_missing: bool = False
) -> pd.Series[float]:
    """Check that ``series`` is a clean numeric time series and return it as float64.

    Parameters
    ----------
    series
        Object to validate. Must be a :class:`pandas.Series`.
    name
        Name of the argument, used in error messages.
    min_length
        Minimum number of observations required.
    allow_missing
        Accept NaN (kept as NaN in the result). Only for code that displays gaps,
        such as charts; calculations must keep the default ``False``.

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
    if missing.any() and not allow_missing:
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

    _check_time_index(series.index, name=name)
    return pd.Series(values, index=series.index, name=series.name, copy=False)


def _check_time_index(index: pd.Index, *, name: str) -> None:
    """Require unique index labels sorted in increasing (temporal) order."""
    if not index.is_unique:
        duplicated = index[index.duplicated()].unique()
        raise InputValidationError(
            f"{name} has duplicated index labels: {_describe_labels(duplicated)}."
        )
    if not index.is_monotonic_increasing:
        raise InputValidationError(
            f"{name} must be sorted by its index in increasing (temporal) order."
        )


def validate_frame(frame: object, *, name: str, min_rows: int) -> pd.DataFrame:
    """Check that ``frame`` is a clean numeric table of time series and return it as float64.

    Each column is one variable (for example the returns of one asset) and each row
    one observation time. The same rules as :func:`validate_series` apply to every
    column, and column labels must be unique.

    Returns
    -------
    pandas.DataFrame
        A new float64 frame with the same index and columns. The input is not modified.

    Raises
    ------
    TypeError
        If ``frame`` is not a DataFrame or has a non-numeric or boolean column.
    InputValidationError
        If it has no columns, duplicated column labels, missing or infinite values,
        or an index that is not unique and increasing.
    InsufficientDataError
        If it has fewer than ``min_rows`` rows.
    """
    if not isinstance(frame, pd.DataFrame):
        raise TypeError(f"{name} must be a pandas DataFrame, got {type(frame).__name__}.")
    if frame.shape[1] == 0:
        raise InputValidationError(f"{name} must have at least one column.")
    if not frame.columns.is_unique:
        duplicated = frame.columns[frame.columns.duplicated()].unique()
        raise InputValidationError(
            f"{name} has duplicated column labels: {_describe_labels(duplicated)}."
        )
    for column, dtype in frame.dtypes.items():
        if pd.api.types.is_bool_dtype(dtype) or not pd.api.types.is_numeric_dtype(dtype):
            raise TypeError(f"{name} column {column!r} must be numeric, got {dtype}.")
    if len(frame) < min_rows:
        raise InsufficientDataError(f"{name} needs at least {min_rows} row(s), got {len(frame)}.")

    values = frame.to_numpy(dtype=np.float64, na_value=np.nan)
    for column_position, column in enumerate(frame.columns):
        column_values = values[:, column_position]
        if np.isnan(column_values).any():
            missing = frame.index[np.isnan(column_values)]
            raise InputValidationError(
                f"{name} column {column!r} contains {len(missing)} missing value(s) at "
                f"{_describe_labels(missing)}. Clean or align the data before calling."
            )
        if np.isinf(column_values).any():
            raise InputValidationError(
                f"{name} column {column!r} contains non-finite values at "
                f"{_describe_labels(frame.index[np.isinf(column_values)])}."
            )
    _check_time_index(frame.index, name=name)
    return pd.DataFrame(values, index=frame.index, columns=frame.columns, copy=False)


def validate_price_series(prices: object, *, name: str = "prices") -> pd.Series[float]:
    """Validate a price series: clean, at least two observations and strictly positive."""
    validated = validate_series(prices, name=name, min_length=2)
    require_strictly_positive(validated, name=name)
    return validated


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


def validate_positive_real(value: object, *, name: str) -> float:
    """Return ``value`` as a float after checking that it is finite and strictly positive.

    Raises
    ------
    TypeError
        If ``value`` is not a real number.
    InputValidationError
        If ``value`` is NaN or infinite.
    DomainError
        If ``value`` is zero or negative.
    """
    as_float = validate_finite_real(value, name=name)
    if as_float <= 0.0:
        raise DomainError(f"{name} must be strictly positive, got {as_float}.")
    return as_float


def validate_open_unit_interval(value: object, *, name: str) -> float:
    """Return ``value`` as a float after checking that ``0 < value < 1``.

    Raises
    ------
    TypeError
        If ``value`` is not a real number.
    InputValidationError
        If ``value`` is NaN or infinite.
    DomainError
        If ``value`` is not strictly between 0 and 1.
    """
    as_float = validate_finite_real(value, name=name)
    if not 0.0 < as_float < 1.0:
        raise DomainError(f"{name} must lie strictly between 0 and 1, got {as_float}.")
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

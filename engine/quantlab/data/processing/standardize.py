"""Conversion of raw price tables into the canonical schema."""

from __future__ import annotations

from collections.abc import Hashable, Mapping

import numpy as np
import pandas as pd

from quantlab.data.schema import CLOSE, INDEX_NAME, OHLCV_COLUMNS
from quantlab.exceptions import InputValidationError


def _normalized_name(label: Hashable) -> str:
    return str(label).strip().lower().replace(" ", "_")


def standardize_ohlcv(
    raw: pd.DataFrame,
    *,
    date_column: str | None = None,
    column_map: Mapping[str, str] | None = None,
) -> pd.DataFrame:
    """Convert a raw price table into the canonical OHLCV schema.

    Steps, in order:

    1. If ``date_column`` is given, that column becomes the index.
    2. Columns are renamed with ``column_map`` (exact source names to canonical
       names), then normalized: stripped, lower-cased, spaces replaced by ``_``.
    3. Only canonical columns (``open, high, low, close, volume``) are kept, in that
       order. ``close`` is required.
    4. The index is parsed as dates. A timezone-aware index is converted to naive
       local time, keeping the wall-clock time (so a daily bar stays on its date).
    5. Values are converted to float64.
    6. Rows are sorted by date with a stable sort, so duplicated dates keep their
       original relative order.

    The function does not remove duplicates, missing values or inconsistent
    prices: those are decisions for :func:`quantlab.data.clean_ohlcv`, informed by
    :func:`quantlab.data.check_ohlcv_integrity`.

    Parameters
    ----------
    raw
        Table as delivered by the source. It is not modified.
    date_column
        Name of the column holding the dates. If ``None``, the existing index is used.
    column_map
        Renames applied before normalization, for example
        ``{"Adj Close": "close"}`` when the adjusted close is wanted.

    Returns
    -------
    pandas.DataFrame
        A new table in the canonical schema.

    Raises
    ------
    TypeError
        If ``raw`` is not a DataFrame.
    InputValidationError
        If the date column is missing, dates or values cannot be parsed, a date is
        missing (NaT), ``close`` is absent, or two source columns map to the same
        canonical name.
    """
    if not isinstance(raw, pd.DataFrame):
        raise TypeError(f"raw must be a pandas DataFrame, got {type(raw).__name__}.")

    frame = raw.copy()
    if date_column is not None:
        if date_column not in frame.columns:
            raise InputValidationError(
                f"date column {date_column!r} not found; available columns: {list(frame.columns)}."
            )
        frame = frame.set_index(date_column)

    renamed = [
        _normalized_name((column_map or {}).get(str(column), column)) for column in frame.columns
    ]
    canonical = [name for name in renamed if name in OHLCV_COLUMNS]
    if len(canonical) != len(set(canonical)):
        raise InputValidationError(
            f"several source columns map to the same canonical column: {renamed}."
        )
    if CLOSE not in canonical:
        raise InputValidationError(
            f"no '{CLOSE}' column after renaming; columns are {renamed}. "
            "Pass column_map to name the closing price column."
        )
    frame.columns = pd.Index(renamed)
    frame = frame[[column for column in OHLCV_COLUMNS if column in canonical]]

    try:
        index = pd.DatetimeIndex(pd.to_datetime(frame.index))
    except (ValueError, TypeError) as error:
        raise InputValidationError(f"dates could not be parsed: {error}") from error
    if index.hasnans:
        raise InputValidationError(
            f"{int(np.count_nonzero(index.isna()))} date(s) are missing (NaT)."
        )
    if index.tz is not None:
        index = index.tz_localize(None)
    frame.index = index.rename(INDEX_NAME)

    for column in frame.columns:
        try:
            frame[column] = pd.to_numeric(frame[column], errors="raise").astype(np.float64)
        except (ValueError, TypeError) as error:
            raise InputValidationError(
                f"column {column!r} has non-numeric values: {error}"
            ) from error

    return frame.sort_index(kind="stable")

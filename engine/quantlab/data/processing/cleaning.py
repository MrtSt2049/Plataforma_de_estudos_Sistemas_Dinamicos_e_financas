"""Explicit, audited cleaning of canonical OHLCV tables.

Cleaning changes the data that every later result depends on, so it is never
implicit: the caller chooses each policy, and the returned report records exactly
what was changed. Store the report with the experiment to make results
reproducible (RULE 017).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

from quantlab._validation import validate_int
from quantlab.data.schema import PRICE_COLUMNS, VOLUME, check_canonical_frame
from quantlab.exceptions import InputValidationError

type DuplicatePolicy = Literal["first", "last"]
type MissingPolicy = Literal["drop", "ffill"]

_DUPLICATE_POLICIES: tuple[str, ...] = ("first", "last")
_MISSING_POLICIES: tuple[str, ...] = ("drop", "ffill")


@dataclass(frozen=True, slots=True)
class CleaningReport:
    """What :func:`clean_ohlcv` changed.

    Attributes
    ----------
    duplicates_policy, missing_policy, max_fill
        The policies applied.
    rows_in, rows_out
        Number of rows before and after cleaning.
    duplicate_dates_removed
        Dates of the rows discarded as duplicates (one entry per discarded row).
    rows_dropped
        Dates of the rows discarded because of missing values.
    prices_forward_filled
        Number of price values replaced by the previous observation.
    volumes_set_to_zero
        Number of missing volumes replaced by 0 (``"ffill"`` policy only).
    """

    duplicates_policy: DuplicatePolicy
    missing_policy: MissingPolicy
    max_fill: int | None
    rows_in: int
    rows_out: int
    duplicate_dates_removed: tuple[pd.Timestamp, ...]
    rows_dropped: tuple[pd.Timestamp, ...]
    prices_forward_filled: int
    volumes_set_to_zero: int


@dataclass(frozen=True, slots=True)
class CleaningResult:
    """Cleaned table and the report of what was changed."""

    data: pd.DataFrame
    report: CleaningReport


def _timestamps(index: pd.Index) -> tuple[pd.Timestamp, ...]:
    return tuple(pd.Timestamp(date) for date in index)


def clean_ohlcv(
    data: pd.DataFrame,
    *,
    duplicates: DuplicatePolicy,
    missing: MissingPolicy,
    max_fill: int | None = None,
) -> CleaningResult:
    """Remove duplicated dates and handle missing values with explicit policies.

    Parameters
    ----------
    data
        Table in the canonical schema, sorted by date (see
        :func:`quantlab.data.standardize_ohlcv`). It is not modified.
    duplicates
        Which row to keep when a date appears more than once: ``"first"`` or
        ``"last"`` in the original order (typically ``"last"`` when later rows are
        corrections).
    missing
        ``"drop"`` removes every row with a missing value in any column.
        ``"ffill"`` carries the last known price forward in the price columns, which
        assumes the price did not change; this produces zero returns on filled dates
        and understates volatility if used extensively. Missing volumes become 0
        (no recorded trading). Rows that still have missing prices afterwards (at the
        start of the series, or beyond ``max_fill``) are dropped.
    max_fill
        With ``"ffill"``, the maximum number of consecutive values filled. ``None``
        means no limit. Ignored with ``"drop"``.

    Returns
    -------
    CleaningResult
        The cleaned table and a :class:`CleaningReport`.

    Raises
    ------
    TypeError
        If ``data`` does not have the canonical structure, or ``max_fill`` is not an
        integer.
    InputValidationError
        If a policy is unknown, ``max_fill < 1``, or the dates are not sorted.

    Notes
    -----
    Infinite values, non-positive prices and inconsistent bars are *not* changed:
    they need case-by-case judgment. Detect them with
    :func:`quantlab.data.check_ohlcv_integrity`.
    """
    frame = check_canonical_frame(data)
    if duplicates not in _DUPLICATE_POLICIES:
        raise InputValidationError(
            f"duplicates must be one of {_DUPLICATE_POLICIES}, got {duplicates!r}."
        )
    if missing not in _MISSING_POLICIES:
        raise InputValidationError(f"missing must be one of {_MISSING_POLICIES}, got {missing!r}.")
    fill_limit = None if max_fill is None else validate_int(max_fill, name="max_fill", minimum=1)
    if not frame.index.is_monotonic_increasing:
        raise InputValidationError(
            "data must be sorted by date before cleaning; use standardize_ohlcv first."
        )

    rows_in = len(frame)
    duplicated = np.asarray(frame.index.duplicated(keep=duplicates))
    removed_duplicates = _timestamps(frame.index[duplicated])
    cleaned = frame.loc[~duplicated].copy()

    price_columns = [column for column in PRICE_COLUMNS if column in cleaned.columns]
    missing_prices_before = cleaned[price_columns].isna().to_numpy()
    missing_volume_before = (
        cleaned[VOLUME].isna().to_numpy()
        if VOLUME in cleaned.columns
        else np.zeros(len(cleaned), dtype=bool)
    )
    if missing == "ffill":
        cleaned[price_columns] = cleaned[price_columns].ffill(limit=fill_limit)
        if VOLUME in cleaned.columns:
            cleaned[VOLUME] = cleaned[VOLUME].fillna(0.0)

    incomplete = np.asarray(cleaned.isna().any(axis=1))
    kept = ~incomplete
    # Count only the replacements that survive in the rows that are kept.
    filled_mask = missing_prices_before & ~cleaned[price_columns].isna().to_numpy()
    filled_prices = int(filled_mask[kept].sum()) if missing == "ffill" else 0
    zero_volumes = int(missing_volume_before[kept].sum()) if missing == "ffill" else 0
    dropped = _timestamps(cleaned.index[incomplete])
    cleaned = cleaned.loc[kept]

    report = CleaningReport(
        duplicates_policy=duplicates,
        missing_policy=missing,
        max_fill=fill_limit if missing == "ffill" else None,
        rows_in=rows_in,
        rows_out=len(cleaned),
        duplicate_dates_removed=removed_duplicates,
        rows_dropped=dropped,
        prices_forward_filled=filled_prices,
        volumes_set_to_zero=zero_volumes,
    )
    return CleaningResult(data=cleaned, report=report)

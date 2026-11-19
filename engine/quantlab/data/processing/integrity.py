"""Integrity checks of canonical OHLCV tables.

The checks *report* problems; they never modify the data. Some problems can be
handled mechanically by :func:`quantlab.data.clean_ohlcv` (duplicated dates,
missing values). Others, such as a high below the low or a 60% overnight jump,
need a human decision: the bar may be a source error or a real event such as an
unadjusted split.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

import numpy as np
import numpy.typing as npt
import pandas as pd

from quantlab._validation import validate_positive_real
from quantlab.data.schema import (
    CLOSE,
    HIGH,
    LOW,
    OPEN,
    PRICE_COLUMNS,
    VOLUME,
    check_canonical_frame,
)
from quantlab.exceptions import DataIntegrityError

_DATES_SHOWN = 3
"""Number of example dates in a one-line issue description."""


class IssueKind(StrEnum):
    """Category of an integrity problem."""

    DUPLICATE_DATE = "duplicate_date"
    UNSORTED_INDEX = "unsorted_index"
    MISSING_VALUE = "missing_value"
    NON_FINITE_VALUE = "non_finite_value"
    NON_POSITIVE_PRICE = "non_positive_price"
    NEGATIVE_VOLUME = "negative_volume"
    HIGH_BELOW_LOW = "high_below_low"
    HIGH_BELOW_OPEN_OR_CLOSE = "high_below_open_or_close"
    LOW_ABOVE_OPEN_OR_CLOSE = "low_above_open_or_close"
    EXTREME_RETURN = "extreme_return"


@dataclass(frozen=True, slots=True)
class IntegrityIssue:
    """One kind of problem found in one column, with every affected date.

    Attributes
    ----------
    kind
        Category of the problem.
    column
        Affected column, or ``None`` for problems of the index or of a whole bar.
    dates
        Every affected date, in order.
    """

    kind: IssueKind
    column: str | None
    dates: tuple[pd.Timestamp, ...]

    @property
    def count(self) -> int:
        """Number of affected observations."""
        return len(self.dates)

    def describe(self) -> str:
        """Return a one-line, human-readable summary."""
        where = f" in '{self.column}'" if self.column else ""
        first = ", ".join(str(date.date()) for date in self.dates[:_DATES_SHOWN])
        more = f" (+{self.count - _DATES_SHOWN} more)" if self.count > _DATES_SHOWN else ""
        return f"{self.kind.value}{where}: {self.count} observation(s), e.g. {first}{more}"


@dataclass(frozen=True, slots=True)
class IntegrityReport:
    """Result of :func:`check_ohlcv_integrity`."""

    issues: tuple[IntegrityIssue, ...]

    @property
    def is_valid(self) -> bool:
        """Whether no problem was found."""
        return not self.issues

    def raise_if_invalid(self) -> None:
        """Raise :class:`DataIntegrityError` listing every problem, if there is any."""
        if self.issues:
            details = "; ".join(issue.describe() for issue in self.issues)
            raise DataIntegrityError(f"{len(self.issues)} integrity problem(s): {details}")


def _dates(index: pd.DatetimeIndex, mask: npt.NDArray[np.bool_]) -> tuple[pd.Timestamp, ...]:
    return tuple(pd.Timestamp(date) for date in index[mask])


def check_ohlcv_integrity(
    data: pd.DataFrame, *, max_abs_log_return: float | None = None
) -> IntegrityReport:
    r"""Check a canonical OHLCV table for data-quality problems.

    Checks performed:

    * dates: duplicated or out of order;
    * every column: missing (NaN) and infinite values;
    * price columns: values that are zero or negative;
    * volume: negative values;
    * bar consistency, when the columns exist: ``high >= low``,
      ``high >= max(open, close)`` and ``low <= min(open, close)``;
    * optionally, close-to-close moves with
      :math:`|\ln(P_t / P_{t-1})|` above ``max_abs_log_return``, which often reveal
      unadjusted splits or bad ticks.

    Comparisons involving a missing value are skipped; the missing value itself is
    reported.

    Parameters
    ----------
    data
        Table in the canonical schema (see :func:`quantlab.data.standardize_ohlcv`).
    max_abs_log_return
        Threshold for the extreme-move check, as an absolute log return
        (``0.4`` flags moves beyond about -33% / +49%). ``None`` disables the check.

    Returns
    -------
    IntegrityReport
        Every problem found. ``report.is_valid`` is ``True`` when there is none.

    Raises
    ------
    TypeError, InputValidationError
        If ``data`` does not follow the canonical schema's structure.
    DomainError
        If ``max_abs_log_return`` is not strictly positive.
    """
    frame = check_canonical_frame(data)
    threshold = (
        None
        if max_abs_log_return is None
        else validate_positive_real(max_abs_log_return, name="max_abs_log_return")
    )
    index = pd.DatetimeIndex(frame.index)
    issues: list[IntegrityIssue] = []

    def report(kind: IssueKind, column: str | None, mask: npt.NDArray[np.bool_]) -> None:
        if mask.any():
            issues.append(IntegrityIssue(kind=kind, column=column, dates=_dates(index, mask)))

    report(IssueKind.DUPLICATE_DATE, None, np.asarray(index.duplicated(keep="first")))
    if not index.is_monotonic_increasing:
        issues.append(IntegrityIssue(kind=IssueKind.UNSORTED_INDEX, column=None, dates=()))

    values = {
        column: frame[column].to_numpy(dtype=np.float64, na_value=np.nan)
        for column in frame.columns
    }
    for column, column_values in values.items():
        report(IssueKind.MISSING_VALUE, column, np.isnan(column_values))
        report(IssueKind.NON_FINITE_VALUE, column, np.isinf(column_values))
        if column in PRICE_COLUMNS:
            report(IssueKind.NON_POSITIVE_PRICE, column, column_values <= 0.0)
    if VOLUME in values:
        report(IssueKind.NEGATIVE_VOLUME, VOLUME, values[VOLUME] < 0.0)

    if HIGH in values and LOW in values:
        report(IssueKind.HIGH_BELOW_LOW, None, values[HIGH] < values[LOW])
    for body in (OPEN, CLOSE):
        if body in values and HIGH in values:
            report(IssueKind.HIGH_BELOW_OPEN_OR_CLOSE, body, values[HIGH] < values[body])
        if body in values and LOW in values:
            report(IssueKind.LOW_ABOVE_OPEN_OR_CLOSE, body, values[LOW] > values[body])

    if threshold is not None:
        close = values[CLOSE]
        usable = np.isfinite(close) & (close > 0.0)
        pair = usable[1:] & usable[:-1]
        log_moves = np.zeros(close.size - 1 if close.size else 0)
        log_moves[pair] = np.log(close[1:][pair] / close[:-1][pair])
        extreme = np.concatenate([[False], pair & (np.abs(log_moves) > threshold)])
        report(IssueKind.EXTREME_RETURN, CLOSE, extreme)

    return IntegrityReport(issues=tuple(issues))

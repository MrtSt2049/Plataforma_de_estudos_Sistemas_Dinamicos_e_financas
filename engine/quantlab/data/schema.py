"""Canonical representation of market price histories.

Every provider converts its raw data into this schema, so the rest of the engine
never depends on how a particular source names its columns or dates:

* index: a :class:`pandas.DatetimeIndex` named ``"date"``, timezone-naive, sorted;
* columns: a subset of ``open, high, low, close, volume``, always including
  ``close``, all float64;
* metadata: symbol, source, frequency, currency and whether prices are adjusted
  (RULE 040: adjusted and unadjusted prices must never be mixed silently).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final

import pandas as pd

from quantlab.exceptions import InputValidationError

OPEN: Final = "open"
HIGH: Final = "high"
LOW: Final = "low"
CLOSE: Final = "close"
VOLUME: Final = "volume"

PRICE_COLUMNS: Final[tuple[str, ...]] = (OPEN, HIGH, LOW, CLOSE)
"""Columns that hold prices and must be strictly positive."""
OHLCV_COLUMNS: Final[tuple[str, ...]] = (OPEN, HIGH, LOW, CLOSE, VOLUME)
"""All canonical columns, in their canonical order."""
INDEX_NAME: Final = "date"


class Frequency(StrEnum):
    """Sampling frequency of a price history."""

    DAILY = "1d"
    WEEKLY = "1wk"
    MONTHLY = "1mo"


@dataclass(frozen=True, slots=True)
class PriceMetadata:
    """Provenance of a price history (RULE 040).

    Attributes
    ----------
    symbol
        Asset identifier in the source's own convention (for example ``"PETR4.SA"``).
    source
        Name of the data source.
    frequency
        Sampling frequency of the observations.
    adjusted
        Whether prices are adjusted for corporate actions (splits, dividends).
        Returns computed from unadjusted prices show artificial jumps on split dates.
    currency
        ISO 4217 code of the prices (``"BRL"``, ``"USD"``), or ``None`` if unknown.
    """

    symbol: str
    source: str
    frequency: Frequency
    adjusted: bool
    currency: str | None = None


def check_canonical_frame(data: object, *, name: str = "data") -> pd.DataFrame:
    """Verify that ``data`` follows the canonical schema's structure and return it.

    Only the structure is checked (type, index, column names). Data quality
    (missing values, inconsistent prices) is the job of
    :func:`quantlab.data.check_ohlcv_integrity`.

    Raises
    ------
    TypeError
        If ``data`` is not a DataFrame or its index is not a DatetimeIndex.
    InputValidationError
        If it lacks ``close``, has non-canonical or duplicated columns, or its index
        carries a timezone.
    """
    if not isinstance(data, pd.DataFrame):
        raise TypeError(f"{name} must be a pandas DataFrame, got {type(data).__name__}.")
    if not isinstance(data.index, pd.DatetimeIndex):
        raise TypeError(
            f"{name} must have a DatetimeIndex, got {type(data.index).__name__}. "
            "Use quantlab.data.standardize_ohlcv first."
        )
    if data.index.tz is not None:
        raise InputValidationError(f"{name} index must be timezone-naive.")
    unknown = [column for column in data.columns if column not in OHLCV_COLUMNS]
    if unknown:
        raise InputValidationError(
            f"{name} has non-canonical columns {unknown}; expected a subset of {OHLCV_COLUMNS}."
        )
    if not data.columns.is_unique:
        raise InputValidationError(f"{name} has duplicated columns.")
    if CLOSE not in data.columns:
        raise InputValidationError(f"{name} must have a '{CLOSE}' column.")
    return data


@dataclass(frozen=True, slots=True)
class PriceHistory:
    """A canonical OHLCV table together with its provenance.

    Attributes
    ----------
    data
        Table in the canonical schema (see the module documentation).
    metadata
        Where the data came from and how it should be interpreted.
    """

    data: pd.DataFrame
    metadata: PriceMetadata

    def __post_init__(self) -> None:
        """Reject tables that do not follow the canonical schema."""
        check_canonical_frame(self.data)

    @property
    def close(self) -> pd.Series[float]:
        """Closing prices as a Series named after the symbol."""
        return pd.Series(
            self.data[CLOSE].to_numpy(dtype="float64"),
            index=self.data.index,
            name=self.metadata.symbol,
        )

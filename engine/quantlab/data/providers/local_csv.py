"""Price provider backed by a directory of CSV files, one file per symbol."""

from __future__ import annotations

import datetime as dt
from collections.abc import Mapping
from pathlib import Path

import pandas as pd

from quantlab.data.processing.standardize import standardize_ohlcv
from quantlab.data.providers.base import SYMBOL_PATTERN, validate_date_range, validate_symbol
from quantlab.data.schema import Frequency, PriceHistory, PriceMetadata
from quantlab.exceptions import DataSourceError, SymbolNotFoundError

_SUFFIX = ".csv"
_ONE_DAY = pd.Timedelta(days=1)


class CsvPriceProvider:
    """Read price histories from ``<directory>/<SYMBOL>.csv`` files.

    Each file holds one symbol, with a date column and at least a closing price.
    Columns are mapped to the canonical schema by
    :func:`quantlab.data.standardize_ohlcv`.

    Parameters
    ----------
    directory
        Folder containing the CSV files.
    adjusted
        Whether the prices in these files are adjusted for corporate actions. There
        is no default: the caller must state it (RULE 040).
    frequency
        Sampling frequency of the files.
    currency
        ISO 4217 currency code of the prices, if known.
    date_column
        Name of the date column in the files.
    column_map
        Renames from file column names to canonical names, for example
        ``{"Adj Close": "close"}``.
    separator, decimal, encoding
        CSV format options, passed to :func:`pandas.read_csv`. Use
        ``separator=";"`` and ``decimal=","`` for files exported with Brazilian
        locale settings.
    source
        Name recorded in the metadata.

    Raises
    ------
    DataSourceError
        If ``directory`` does not exist or is not a directory.
    """

    def __init__(
        self,
        directory: str | Path,
        *,
        adjusted: bool,
        frequency: Frequency = Frequency.DAILY,
        currency: str | None = None,
        date_column: str = "date",
        column_map: Mapping[str, str] | None = None,
        separator: str = ",",
        decimal: str = ".",
        encoding: str = "utf-8",
        source: str = "local-csv",
    ) -> None:
        self._directory = Path(directory)
        if not self._directory.is_dir():
            raise DataSourceError(f"CSV directory not found: {self._directory}")
        self._adjusted = adjusted
        self._frequency = Frequency(frequency)
        self._currency = currency
        self._date_column = date_column
        self._column_map = dict(column_map or {})
        self._separator = separator
        self._decimal = decimal
        self._encoding = encoding
        self._source = source

    @property
    def source(self) -> str:
        """Name of the source, recorded in the metadata of every history."""
        return self._source

    def available_symbols(self) -> tuple[str, ...]:
        """Return the symbols with a CSV file in the directory, sorted."""
        return tuple(
            sorted(
                path.stem
                for path in self._directory.glob(f"*{_SUFFIX}")
                if path.is_file() and SYMBOL_PATTERN.fullmatch(path.stem)
            )
        )

    def _path_for(self, symbol: str) -> Path:
        validate_symbol(symbol)
        path = self._directory / f"{symbol}{_SUFFIX}"
        if not path.is_file():
            raise SymbolNotFoundError(f"symbol {symbol!r} not found in {self._directory}.")
        return path

    def fetch(
        self, symbol: str, *, start: dt.date | None = None, end: dt.date | None = None
    ) -> PriceHistory:
        """Read, standardize and filter the history of ``symbol``.

        Parameters
        ----------
        symbol
            File name without the ``.csv`` suffix.
        start, end
            Inclusive date bounds; ``None`` means unbounded. Observations with a time
            of day on the ``end`` date are included.

        Returns
        -------
        PriceHistory
            Canonical data and metadata. The data may be empty if no observation
            falls in the range. Duplicates and missing values are *not* removed: use
            :func:`quantlab.data.check_ohlcv_integrity` and
            :func:`quantlab.data.clean_ohlcv`.

        Raises
        ------
        InputValidationError
            If ``symbol`` has invalid characters, ``start > end``, or the file content
            cannot be mapped to the canonical schema.
        SymbolNotFoundError
            If there is no file for ``symbol``.
        DataSourceError
            If the file cannot be read or parsed as CSV.
        """
        validate_date_range(start, end)
        path = self._path_for(symbol)
        try:
            raw = pd.read_csv(
                path, sep=self._separator, decimal=self._decimal, encoding=self._encoding
            )
        except (OSError, UnicodeDecodeError, pd.errors.ParserError) as error:
            raise DataSourceError(f"could not read {path}: {error}") from error
        except pd.errors.EmptyDataError as error:
            raise DataSourceError(f"{path} is empty.") from error

        data = standardize_ohlcv(raw, date_column=self._date_column, column_map=self._column_map)
        if start is not None:
            data = data.loc[data.index >= pd.Timestamp(start)]
        if end is not None:
            data = data.loc[data.index < pd.Timestamp(end) + _ONE_DAY]

        metadata = PriceMetadata(
            symbol=symbol,
            source=self._source,
            frequency=self._frequency,
            adjusted=self._adjusted,
            currency=self._currency,
        )
        return PriceHistory(data=data, metadata=metadata)

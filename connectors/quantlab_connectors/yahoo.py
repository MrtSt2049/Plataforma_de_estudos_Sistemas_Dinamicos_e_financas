"""Price provider for Yahoo Finance, built on the ``yfinance`` client.

``yfinance`` is an unofficial client of Yahoo's public endpoints. It can break without
notice, and Yahoo's terms of use restrict commercial use and redistribution of the data
(see ``docs/adr/0002-camada-de-dados-de-mercado.md``). Use it for study and research, and
keep a copy of the data behind any result you want to reproduce: Yahoo revises past
prices, for example when it applies a new dividend adjustment.

The provider implements :class:`quantlab.data.PriceProvider`. Like every provider it
returns the data as delivered: it does not remove duplicates or missing values. Run
:func:`quantlab.data.check_ohlcv_integrity` and :func:`quantlab.data.clean_ohlcv` next.
"""

from __future__ import annotations

import datetime as dt
import math
import re
import threading
from collections.abc import Iterator, Mapping
from contextlib import contextmanager

import numpy as np
import pandas as pd

from quantlab.data.processing.standardize import standardize_ohlcv
from quantlab.data.providers.base import validate_date_range, validate_symbol
from quantlab.data.schema import INDEX_NAME, OHLCV_COLUMNS, Frequency, PriceHistory, PriceMetadata
from quantlab.exceptions import (
    DataSourceError,
    InputValidationError,
    SymbolNotFoundError,
)

try:
    import yfinance as yf
    from yfinance.exceptions import (
        YFException,
        YFPricesMissingError,
        YFRateLimitError,
        YFTzMissingError,
    )
except ModuleNotFoundError as error:
    raise ModuleNotFoundError(
        "quantlab_connectors.yahoo needs the optional 'yfinance' package. "
        "Install it with `uv sync --extra yahoo` (or `pip install 'quantlab[yahoo]'`).",
        name=error.name,
    ) from error

DEFAULT_TIMEOUT_SECONDS = 30.0
"""Default limit, in seconds, for each request to Yahoo."""

_ONE_DAY = dt.timedelta(days=1)
_HTTP_NOT_FOUND = 404
_CURRENCY_PATTERN = re.compile(r"[A-Za-z]{3}")
_YFINANCE_CONFIG_LOCK = threading.Lock()


@contextmanager
def _yfinance_raises_errors() -> Iterator[None]:
    """Make ``yfinance`` raise its errors instead of logging them and returning nothing.

    By default ``yfinance`` swallows failures: a network error or an unknown ticker is
    only logged and an empty table comes back, which would look like "no data in the
    range". That is the silent failure RULE 010 forbids. The switch is a global setting
    of the library, so it is restored afterwards and guarded by a lock: concurrent
    fetches in one process are therefore serialized, which also keeps the request rate
    gentle.
    """
    with _YFINANCE_CONFIG_LOCK:
        debug = yf.config.debug
        previous = debug.hide_exceptions
        debug.hide_exceptions = False
        try:
            yield
        finally:
            debug.hide_exceptions = previous


def _http_status(error: BaseException) -> int | None:
    """Return the HTTP status carried by a client exception, if it has one."""
    status = getattr(getattr(error, "response", None), "status_code", None)
    return status if isinstance(status, int) else None


def _as_date(value: dt.date) -> dt.date:
    """Drop the time of day of a ``datetime`` so bounds always refer to whole days."""
    return value.date() if isinstance(value, dt.datetime) else value


def _empty_frame() -> pd.DataFrame:
    """Return an empty table in the canonical schema."""
    return pd.DataFrame(
        {column: np.array([], dtype=np.float64) for column in OHLCV_COLUMNS},
        index=pd.DatetimeIndex([], name=INDEX_NAME),
    )


def _currency_from(metadata: object) -> str | None:
    """Extract a three-letter currency code from Yahoo's history metadata, if present.

    ``yfinance`` returns a dict-like ``HistoryMetadata`` that is a ``Mapping`` but not a
    ``dict``, so the check is on ``Mapping``.
    """
    value = metadata.get("currency") if isinstance(metadata, Mapping) else None
    return value if isinstance(value, str) and _CURRENCY_PATTERN.fullmatch(value) else None


class YahooPriceProvider:
    """Download price histories from Yahoo Finance.

    Symbols follow Yahoo's convention: ``AAPL``, ``PETR4.SA`` (B3), ``^BVSP`` (index),
    ``BRL=X`` (exchange rate), ``BTC-USD`` (crypto).

    Parameters
    ----------
    adjusted
        ``True`` asks Yahoo for prices adjusted for splits and dividends (open, high, low
        and close); ``False`` asks for the unadjusted ones. There is no default: the
        caller must choose (RULE 040), because an adjusted series differs from the
        unadjusted one by a factor that changes over time. Yahoo decides which corporate
        actions count as splits, so ``False`` does not guarantee the price actually traded.
    frequency
        Sampling frequency of the bars.
    timeout
        Limit, in seconds, for each request.
    source
        Name recorded in the metadata.

    Raises
    ------
    InputValidationError
        If ``timeout`` is not a positive finite number.
    """

    def __init__(
        self,
        *,
        adjusted: bool,
        frequency: Frequency = Frequency.DAILY,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        source: str = "yahoo-finance",
    ) -> None:
        if not math.isfinite(timeout) or timeout <= 0:
            raise InputValidationError(f"timeout must be a positive finite number, got {timeout}.")
        self._adjusted = adjusted
        self._frequency = Frequency(frequency)
        self._timeout = float(timeout)
        self._source = source

    @property
    def source(self) -> str:
        """Name of the source, recorded in the metadata of every history."""
        return self._source

    def available_symbols(self) -> tuple[str, ...]:
        """Not supported: Yahoo Finance has no catalogue that can be listed.

        Raises
        ------
        NotImplementedError
            Always. Pass any Yahoo ticker to :meth:`fetch` instead.
        """
        raise NotImplementedError(
            "Yahoo Finance has no symbol catalogue to list; pass a ticker to fetch()."
        )

    def _request(self, start: dt.date | None, end: dt.date | None) -> dict[str, object]:
        """Build the ``yfinance`` arguments for an inclusive ``[start, end]`` range."""
        request: dict[str, object] = {
            "interval": self._frequency.value,
            "auto_adjust": self._adjusted,
            "actions": False,
            "timeout": self._timeout,
        }
        if start is None and end is None:
            # Without any date yfinance returns only the last month, not the full history.
            request["period"] = "max"
        if start is not None:
            request["start"] = start.isoformat()
        if end is not None:
            # yfinance treats `end` as exclusive; the provider contract is inclusive.
            request["end"] = (end + _ONE_DAY).isoformat()
        return request

    def fetch(
        self, symbol: str, *, start: dt.date | None = None, end: dt.date | None = None
    ) -> PriceHistory:
        """Download, standardize and filter the history of ``symbol``.

        Parameters
        ----------
        symbol
            Yahoo ticker, for example ``"PETR4.SA"``.
        start, end
            Inclusive date bounds; ``None`` means unbounded. Bars are kept by their own
            date, so a weekly or monthly bar stamped before ``start`` is left out even if
            it covers ``start``.

        Returns
        -------
        PriceHistory
            Canonical data and metadata. The currency comes from Yahoo and may carry a
            minor unit (``"GBp"`` is pence); it is ``None`` when Yahoo gives none or the
            range is empty. The data is empty when Yahoo has no bar in the range for a
            valid symbol. Duplicates and missing values are *not* removed. The most
            recent bar can still be forming while the market is open.

        Raises
        ------
        InputValidationError
            If ``symbol`` has invalid characters or ``start > end``.
        SymbolNotFoundError
            If Yahoo does not know the symbol.
        DataSourceError
            If the request fails (network, timeout, rate limit, server error) or Yahoo
            returns content that does not fit the canonical schema.
        """
        validate_date_range(start, end)
        validate_symbol(symbol)
        first = None if start is None else _as_date(start)
        last = None if end is None else _as_date(end)

        ticker = yf.Ticker(symbol)
        try:
            with _yfinance_raises_errors():
                raw = ticker.history(**self._request(first, last))
                metadata = ticker.get_history_metadata()
        except YFTzMissingError as error:
            raise SymbolNotFoundError(f"symbol {symbol!r} not found on Yahoo Finance.") from error
        except YFPricesMissingError:
            # Yahoo knows the symbol but has no bar in this range (weekend, holiday, before
            # the listing): an empty history, as the PriceProvider contract allows.
            return self._history(symbol, _empty_frame(), currency=None)
        except YFRateLimitError as error:
            raise DataSourceError("Yahoo Finance rate limit reached; try again later.") from error
        except YFException as error:
            raise DataSourceError(
                f"Yahoo Finance request for {symbol!r} failed: {error}"
            ) from error
        except OSError as error:
            if _http_status(error) == _HTTP_NOT_FOUND:
                raise SymbolNotFoundError(
                    f"symbol {symbol!r} not found on Yahoo Finance."
                ) from error
            raise DataSourceError(
                f"Yahoo Finance request for {symbol!r} failed: {error}"
            ) from error

        if not isinstance(raw, pd.DataFrame):
            raise DataSourceError(
                f"Yahoo Finance returned {type(raw).__name__} for {symbol!r}, expected a table."
            )
        try:
            data = _empty_frame() if raw.empty else standardize_ohlcv(raw)
        except InputValidationError as error:
            raise DataSourceError(
                f"Yahoo Finance data for {symbol!r} does not fit the canonical schema: {error}"
            ) from error
        if first is not None:
            data = data.loc[data.index >= pd.Timestamp(first)]
        if last is not None:
            data = data.loc[data.index < pd.Timestamp(last) + _ONE_DAY]
        return self._history(symbol, data, currency=_currency_from(metadata))

    def _history(self, symbol: str, data: pd.DataFrame, *, currency: str | None) -> PriceHistory:
        return PriceHistory(
            data=data,
            metadata=PriceMetadata(
                symbol=symbol,
                source=self._source,
                frequency=self._frequency,
                adjusted=self._adjusted,
                currency=currency,
            ),
        )

"""Tests of the Yahoo Finance provider. None of them touches the network.

``yfinance.Ticker`` is replaced by a fake that returns, or raises, what Yahoo was seen to
do in real calls (see docs/adr/0005): a timezone-aware ``Date`` index at local midnight,
capitalized columns, ``Volume`` as integers, an ``HTTPError`` 404 for an unknown ticker and
``YFPricesMissingError`` for a valid ticker without bars in the range.
"""

from __future__ import annotations

import datetime as dt
import importlib
import sys
from types import MappingProxyType, SimpleNamespace

import numpy as np
import pandas as pd
import pytest
import yfinance as yf
from yfinance.exceptions import (
    YFDataException,
    YFPricesMissingError,
    YFRateLimitError,
    YFTzMissingError,
)

from quantlab.analysis import simple_returns
from quantlab.data import (
    Frequency,
    PriceProvider,
    check_ohlcv_integrity,
    clean_ohlcv,
)
from quantlab.exceptions import DataSourceError, InputValidationError, SymbolNotFoundError
from quantlab_connectors import yahoo
from quantlab_connectors.yahoo import YahooPriceProvider

OPEN_PRICES = [25.0, 26.0, 26.9, 26.7, 26.4, 26.6]
CLOSE_PRICES = [26.0, 26.8, 26.6, 26.7, 26.5, 26.3]
DAYS = ["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05", "2024-01-08", "2024-01-09"]


def yahoo_frame(days: list[str] = DAYS, *, with_adj_close: bool = False) -> pd.DataFrame:
    """Synthetic table shaped like what ``Ticker.history`` returns for a B3 stock."""
    index = pd.DatetimeIndex(pd.to_datetime(days)).tz_localize("America/Sao_Paulo")
    index.name = "Date"
    n = len(days)
    opens, closes = OPEN_PRICES[:n], CLOSE_PRICES[:n]
    columns: dict[str, object] = {
        "Open": opens,
        "High": [max(o, c) + 0.4 for o, c in zip(opens, closes, strict=True)],
        "Low": [min(o, c) - 0.4 for o, c in zip(opens, closes, strict=True)],
        "Close": closes,
    }
    if with_adj_close:
        columns["Adj Close"] = [price * 0.7 for price in CLOSE_PRICES[:n]]
    columns["Volume"] = np.arange(1, n + 1, dtype="int64") * 1_000_000
    return pd.DataFrame(columns, index=index)


class FakeTicker:
    """Stands in for the ``yfinance.Ticker`` class and for the instance it creates."""

    def __init__(self) -> None:
        self.frame: object = yahoo_frame()
        self.error: BaseException | None = None
        self.metadata: object = {"currency": "BRL"}
        self.constructed: list[str] = []
        self.requests: list[dict[str, object]] = []
        self.hide_exceptions_during_call: list[bool] = []

    def __call__(self, symbol: str) -> FakeTicker:
        self.constructed.append(symbol)
        return self

    def history(self, **kwargs: object) -> object:
        self.requests.append(kwargs)
        self.hide_exceptions_during_call.append(yf.config.debug.hide_exceptions)
        if self.error is not None:
            raise self.error
        return self.frame

    def get_history_metadata(self) -> object:
        return self.metadata


class HttpStatusError(OSError):
    """Mimics the HTTP errors of curl_cffi and requests: an OSError carrying a response."""

    def __init__(self, status_code: int) -> None:
        super().__init__(f"HTTP Error {status_code}: ")
        self.response = SimpleNamespace(status_code=status_code)


@pytest.fixture
def ticker(monkeypatch: pytest.MonkeyPatch) -> FakeTicker:
    fake = FakeTicker()
    monkeypatch.setattr(yf, "Ticker", fake)
    return fake


@pytest.fixture
def provider() -> YahooPriceProvider:
    return YahooPriceProvider(adjusted=True)


def test_implements_the_provider_interface(provider: YahooPriceProvider) -> None:
    assert isinstance(provider, PriceProvider)
    assert provider.source == "yahoo-finance"
    assert YahooPriceProvider(adjusted=True, source="custom").source == "custom"


def test_has_no_symbol_catalogue(provider: YahooPriceProvider) -> None:
    with pytest.raises(NotImplementedError, match="no symbol catalogue"):
        provider.available_symbols()


def test_fetch_returns_canonical_data_with_metadata(
    provider: YahooPriceProvider, ticker: FakeTicker
) -> None:
    history = provider.fetch("PETR4.SA", start=dt.date(2024, 1, 2), end=dt.date(2024, 1, 9))
    data = history.data
    assert list(data.columns) == ["open", "high", "low", "close", "volume"]
    assert isinstance(data.index, pd.DatetimeIndex)
    assert data.index.name == "date"
    assert data.index.tz is None
    assert [str(day.date()) for day in data.index] == DAYS
    assert (data.dtypes == np.float64).all()
    assert history.close.tolist() == CLOSE_PRICES
    assert history.close.name == "PETR4.SA"
    assert data["volume"].tolist() == [1e6, 2e6, 3e6, 4e6, 5e6, 6e6]
    assert history.metadata.symbol == "PETR4.SA"
    assert history.metadata.source == "yahoo-finance"
    assert history.metadata.adjusted is True
    assert history.metadata.currency == "BRL"
    assert history.metadata.frequency is Frequency.DAILY
    assert ticker.constructed == ["PETR4.SA"]


def test_daily_bars_keep_their_local_date(provider: YahooPriceProvider, ticker: FakeTicker) -> None:
    """Midnight in Tokyo is 15:00 UTC of the previous day: converting to UTC would move every
    bar one day back. The wall-clock date of the exchange must be kept."""
    index = pd.DatetimeIndex(["2024-01-02", "2024-01-03"]).tz_localize("Asia/Tokyo")
    ticker.frame = pd.DataFrame({"Close": [1.0, 2.0]}, index=index.rename("Date"))
    history = provider.fetch("7203.T")
    assert [str(day.date()) for day in history.data.index] == ["2024-01-02", "2024-01-03"]


@pytest.mark.parametrize("adjusted", [True, False])
def test_adjusted_flag_selects_yahoo_adjustment(ticker: FakeTicker, adjusted: bool) -> None:
    history = YahooPriceProvider(adjusted=adjusted).fetch("PETR4.SA")
    assert ticker.requests[0]["auto_adjust"] is adjusted
    assert history.metadata.adjusted is adjusted


def test_adjusted_flag_has_no_default() -> None:
    with pytest.raises(TypeError, match="adjusted"):
        YahooPriceProvider()  # type: ignore[call-arg]


def test_unadjusted_table_keeps_close_and_drops_adj_close(
    ticker: FakeTicker,
) -> None:
    ticker.frame = yahoo_frame(with_adj_close=True)
    history = YahooPriceProvider(adjusted=False).fetch("PETR4.SA")
    assert list(history.data.columns) == ["open", "high", "low", "close", "volume"]
    assert history.close.tolist() == CLOSE_PRICES


def test_request_parameters_for_a_bounded_range(
    provider: YahooPriceProvider, ticker: FakeTicker
) -> None:
    provider.fetch("PETR4.SA", start=dt.date(2024, 1, 2), end=dt.date(2024, 1, 9))
    request = ticker.requests[0]
    assert request["start"] == "2024-01-02"
    assert request["end"] == "2024-01-10"  # yfinance's end is exclusive, ours is inclusive
    assert request["interval"] == "1d"
    assert request["actions"] is False
    assert request["timeout"] == yahoo.DEFAULT_TIMEOUT_SECONDS
    assert "period" not in request


def test_unbounded_request_asks_for_the_full_history(
    provider: YahooPriceProvider, ticker: FakeTicker
) -> None:
    """Without dates yfinance returns only the last month, so the provider must say 'max'."""
    provider.fetch("PETR4.SA")
    request = ticker.requests[0]
    assert request["period"] == "max"
    assert "start" not in request
    assert "end" not in request


@pytest.mark.parametrize(
    ("start", "end", "expected"),
    [
        (dt.date(2024, 1, 2), None, {"start": "2024-01-02"}),
        (None, dt.date(2024, 1, 9), {"end": "2024-01-10"}),
    ],
)
def test_one_sided_ranges_do_not_use_period(
    provider: YahooPriceProvider,
    ticker: FakeTicker,
    start: dt.date | None,
    end: dt.date | None,
    expected: dict[str, str],
) -> None:
    provider.fetch("PETR4.SA", start=start, end=end)
    request = ticker.requests[0]
    assert "period" not in request
    assert {key: request[key] for key in expected} == expected
    assert request.keys() & {"start", "end"} == expected.keys()


def test_datetime_bounds_are_reduced_to_whole_days(
    provider: YahooPriceProvider, ticker: FakeTicker
) -> None:
    provider.fetch(
        "PETR4.SA",
        start=dt.datetime(2024, 1, 2, 15, 30),
        end=dt.datetime(2024, 1, 9, 9, 0),
    )
    request = ticker.requests[0]
    assert request["start"] == "2024-01-02"
    assert request["end"] == "2024-01-10"


def test_bars_outside_the_requested_range_are_dropped(
    provider: YahooPriceProvider, ticker: FakeTicker
) -> None:
    """Yahoo may return a bar outside the range (for instance a weekly bar that covers the
    start). The provider contract is by the bar's own date, inclusive on both ends."""
    history = provider.fetch("PETR4.SA", start=dt.date(2024, 1, 3), end=dt.date(2024, 1, 8))
    assert [str(day.date()) for day in history.data.index] == [
        "2024-01-03",
        "2024-01-04",
        "2024-01-05",
        "2024-01-08",
    ]


@pytest.mark.parametrize(
    ("frequency", "interval"),
    [(Frequency.DAILY, "1d"), (Frequency.WEEKLY, "1wk"), (Frequency.MONTHLY, "1mo")],
)
def test_frequency_maps_to_yahoo_interval(
    ticker: FakeTicker, frequency: Frequency, interval: str
) -> None:
    history = YahooPriceProvider(adjusted=True, frequency=frequency).fetch("AAPL")
    assert ticker.requests[0]["interval"] == interval
    assert history.metadata.frequency is frequency


def test_custom_timeout_is_forwarded(ticker: FakeTicker) -> None:
    YahooPriceProvider(adjusted=True, timeout=5).fetch("AAPL")
    assert ticker.requests[0]["timeout"] == 5.0


@pytest.mark.parametrize("timeout", [0, -1, float("nan"), float("inf")])
def test_rejects_invalid_timeout(timeout: float) -> None:
    with pytest.raises(InputValidationError, match="timeout"):
        YahooPriceProvider(adjusted=True, timeout=timeout)


# --- input validation happens before any request ---------------------------------------


@pytest.mark.parametrize("symbol", ["../secret", "a/b", "", ".hidden", "AAPL MSFT", "A&b=c"])
def test_rejects_unsafe_symbols_without_calling_yahoo(
    provider: YahooPriceProvider, ticker: FakeTicker, symbol: str
) -> None:
    with pytest.raises(InputValidationError, match="invalid symbol"):
        provider.fetch(symbol)
    assert ticker.constructed == []


@pytest.mark.parametrize("symbol", ["PETR4.SA", "^BVSP", "BRL=X", "BTC-USD", "BRK-B", "AAPL"])
def test_accepts_yahoo_symbol_conventions(
    provider: YahooPriceProvider, ticker: FakeTicker, symbol: str
) -> None:
    assert provider.fetch(symbol).metadata.symbol == symbol


def test_rejects_inverted_range_without_calling_yahoo(
    provider: YahooPriceProvider, ticker: FakeTicker
) -> None:
    with pytest.raises(InputValidationError, match="must not be after"):
        provider.fetch("AAPL", start=dt.date(2024, 2, 1), end=dt.date(2024, 1, 1))
    assert ticker.constructed == []


def test_rejects_non_date_bounds(provider: YahooPriceProvider, ticker: FakeTicker) -> None:
    with pytest.raises(TypeError, match="start"):
        provider.fetch("AAPL", start="2024-01-01")  # type: ignore[arg-type]
    assert ticker.constructed == []


# --- error contract --------------------------------------------------------------------


def test_missing_timezone_means_unknown_symbol(
    provider: YahooPriceProvider, ticker: FakeTicker
) -> None:
    ticker.error = YFTzMissingError("LEHMQ")
    with pytest.raises(SymbolNotFoundError, match="'LEHMQ'") as info:
        provider.fetch("LEHMQ")
    assert isinstance(info.value.__cause__, YFTzMissingError)


def test_http_404_means_unknown_symbol(provider: YahooPriceProvider, ticker: FakeTicker) -> None:
    """Observed for a ticker that does not exist: curl_cffi raises HTTPError 404."""
    ticker.error = HttpStatusError(404)
    with pytest.raises(SymbolNotFoundError, match=r"'XXXX3\.SA'"):
        provider.fetch("XXXX3.SA")


def test_valid_symbol_without_bars_gives_an_empty_history(
    provider: YahooPriceProvider, ticker: FakeTicker
) -> None:
    """Observed for a weekend range: YFPricesMissingError, not an unknown symbol."""
    ticker.error = YFPricesMissingError("PETR4.SA", "(1d 2024-01-06 -> 2024-01-07)")
    history = provider.fetch("PETR4.SA", start=dt.date(2024, 1, 6), end=dt.date(2024, 1, 7))
    assert history.data.empty
    assert list(history.data.columns) == ["open", "high", "low", "close", "volume"]
    assert history.data.index.name == "date"
    assert (history.data.dtypes == np.float64).all()
    assert history.metadata.currency is None
    assert history.metadata.symbol == "PETR4.SA"


def test_empty_table_gives_an_empty_history(
    provider: YahooPriceProvider, ticker: FakeTicker
) -> None:
    ticker.frame = pd.DataFrame()
    assert provider.fetch("PETR4.SA").data.empty


def test_rate_limit_is_a_source_error(provider: YahooPriceProvider, ticker: FakeTicker) -> None:
    ticker.error = YFRateLimitError()
    with pytest.raises(DataSourceError, match="rate limit") as info:
        provider.fetch("AAPL")
    assert not isinstance(info.value, SymbolNotFoundError)


def test_other_yfinance_errors_are_source_errors(
    provider: YahooPriceProvider, ticker: FakeTicker
) -> None:
    ticker.error = YFDataException("*** YAHOO! FINANCE IS CURRENTLY DOWN! ***")
    with pytest.raises(DataSourceError, match="CURRENTLY DOWN") as info:
        provider.fetch("AAPL")
    assert not isinstance(info.value, SymbolNotFoundError)


@pytest.mark.parametrize(
    "error",
    [HttpStatusError(500), HttpStatusError(429), TimeoutError("timed out"), OSError("no route")],
    ids=["http-500", "http-429", "timeout", "network"],
)
def test_network_and_http_failures_are_source_errors(
    provider: YahooPriceProvider, ticker: FakeTicker, error: OSError
) -> None:
    ticker.error = error
    with pytest.raises(DataSourceError, match="'AAPL'") as info:
        provider.fetch("AAPL")
    assert not isinstance(info.value, SymbolNotFoundError)
    assert info.value.__cause__ is error


def test_unexpected_errors_are_not_hidden(provider: YahooPriceProvider, ticker: FakeTicker) -> None:
    """Only the failure kinds seen in practice are translated; anything else propagates."""
    ticker.error = KeyError("chart")
    with pytest.raises(KeyError):
        provider.fetch("AAPL")


def test_non_table_response_is_a_source_error(
    provider: YahooPriceProvider, ticker: FakeTicker
) -> None:
    ticker.frame = None
    with pytest.raises(DataSourceError, match="expected a table"):
        provider.fetch("AAPL")


@pytest.mark.parametrize(
    "frame",
    [
        pd.DataFrame({"Open": [1.0]}, index=pd.DatetimeIndex(["2024-01-02"], name="Date")),
        pd.DataFrame({"Close": ["n/a"]}, index=pd.DatetimeIndex(["2024-01-02"], name="Date")),
    ],
    ids=["no-close-column", "non-numeric-close"],
)
def test_malformed_content_is_a_source_error(
    provider: YahooPriceProvider, ticker: FakeTicker, frame: pd.DataFrame
) -> None:
    ticker.frame = frame
    with pytest.raises(DataSourceError, match="canonical schema") as info:
        provider.fetch("AAPL")
    assert isinstance(info.value.__cause__, InputValidationError)


# --- currency metadata -----------------------------------------------------------------


@pytest.mark.parametrize(
    ("metadata", "expected"),
    [
        ({"currency": "USD"}, "USD"),
        ({"currency": "GBp"}, "GBp"),
        ({"currency": "BRL", "symbol": "PETR4.SA"}, "BRL"),
        # yfinance returns a Mapping that is not a dict (found with a real call).
        (MappingProxyType({"currency": "BRL"}), "BRL"),
        ({}, None),
        ({"currency": ""}, None),
        ({"currency": "REAL"}, None),
        ({"currency": 986}, None),
        (None, None),
        ("BRL", None),
    ],
)
def test_currency_comes_from_yahoo_metadata_when_valid(
    provider: YahooPriceProvider, ticker: FakeTicker, metadata: object, expected: str | None
) -> None:
    ticker.metadata = metadata
    assert provider.fetch("PETR4.SA").metadata.currency == expected


# --- yfinance global setting -----------------------------------------------------------


def test_yfinance_is_set_to_raise_only_during_the_call(
    provider: YahooPriceProvider, ticker: FakeTicker
) -> None:
    assert yf.config.debug.hide_exceptions is True
    provider.fetch("AAPL")
    assert ticker.hide_exceptions_during_call == [False]
    assert yf.config.debug.hide_exceptions is True


def test_yfinance_setting_is_restored_after_a_failure(
    provider: YahooPriceProvider, ticker: FakeTicker
) -> None:
    ticker.error = HttpStatusError(500)
    with pytest.raises(DataSourceError):
        provider.fetch("AAPL")
    assert yf.config.debug.hide_exceptions is True


def test_yfinance_setting_chosen_by_the_user_is_preserved(
    provider: YahooPriceProvider, ticker: FakeTicker
) -> None:
    # Set by hand: yfinance keeps its options in a dict that monkeypatch cannot restore.
    yf.config.debug.hide_exceptions = False
    try:
        provider.fetch("AAPL")
        assert yf.config.debug.hide_exceptions is False
    finally:
        yf.config.debug.hide_exceptions = True


# --- integration with the rest of the data pipeline ------------------------------------


def test_full_pipeline_to_returns(provider: YahooPriceProvider, ticker: FakeTicker) -> None:
    history = provider.fetch("PETR4.SA")
    report = check_ohlcv_integrity(history.data)
    assert report.is_valid
    cleaned = clean_ohlcv(history.data, duplicates="last", missing="drop")
    returns = simple_returns(cleaned.data["close"])
    assert returns.iloc[0] == pytest.approx(26.8 / 26.0 - 1.0, rel=1e-14)


# --- optional dependency ---------------------------------------------------------------


def test_missing_yfinance_explains_how_to_install_it(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "yfinance", None)
    monkeypatch.delitem(sys.modules, "quantlab_connectors.yahoo")
    with pytest.raises(ModuleNotFoundError, match=r"uv sync --extra yahoo") as info:
        importlib.import_module("quantlab_connectors.yahoo")
    assert info.value.name == "yfinance"

"""Contract tests against the real Yahoo Finance. Off by default: run with ``-m network``.

They check shape and behaviour, never price values, because Yahoo revises history.
"""

from __future__ import annotations

import datetime as dt

import pandas as pd
import pytest

from quantlab.data import Frequency
from quantlab.exceptions import SymbolNotFoundError
from quantlab_connectors.yahoo import YahooPriceProvider

pytestmark = pytest.mark.network

JAN_2024 = {"start": dt.date(2024, 1, 2), "end": dt.date(2024, 1, 9)}
B3_TRADING_DAYS = [
    "2024-01-02",
    "2024-01-03",
    "2024-01-04",
    "2024-01-05",
    "2024-01-08",
    "2024-01-09",
]


def test_real_fetch_follows_the_canonical_schema() -> None:
    history = YahooPriceProvider(adjusted=True).fetch("PETR4.SA", **JAN_2024)
    assert [str(day.date()) for day in history.data.index] == B3_TRADING_DAYS
    assert list(history.data.columns) == ["open", "high", "low", "close", "volume"]
    assert isinstance(history.data.index, pd.DatetimeIndex)
    assert history.data.index.tz is None
    assert history.metadata.currency == "BRL"
    assert history.metadata.frequency is Frequency.DAILY
    assert (history.data[["open", "high", "low", "close"]] > 0).all().all()


def test_real_adjusted_and_unadjusted_series_have_the_same_dates() -> None:
    adjusted = YahooPriceProvider(adjusted=True).fetch("PETR4.SA", **JAN_2024)
    unadjusted = YahooPriceProvider(adjusted=False).fetch("PETR4.SA", **JAN_2024)
    assert adjusted.data.index.equals(unadjusted.data.index)
    # Dividends only ever lower earlier prices, so adjusted never exceeds unadjusted.
    assert (adjusted.close <= unadjusted.close + 1e-9).all()


def test_real_unknown_symbol() -> None:
    with pytest.raises(SymbolNotFoundError):
        YahooPriceProvider(adjusted=True).fetch("ZZZZNOPE123", **JAN_2024)


def test_real_weekend_range_is_empty_not_an_error() -> None:
    history = YahooPriceProvider(adjusted=True).fetch(
        "PETR4.SA", start=dt.date(2024, 1, 6), end=dt.date(2024, 1, 7)
    )
    assert history.data.empty

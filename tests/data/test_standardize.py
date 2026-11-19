from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from quantlab.data import OHLCV_COLUMNS, standardize_ohlcv
from quantlab.exceptions import InputValidationError


def raw_yahoo_like() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Date": ["2025-01-03", "2025-01-02", "2025-01-06"],
            "Open": ["10.1", "10.0", "10.4"],
            "High": [10.6, 10.3, 10.9],
            "Low": [9.9, 9.8, 10.2],
            "Close": [10.5, 10.1, 10.8],
            "Adj Close": [10.4, 10.0, 10.7],
            "Volume": [1000, 1500, 1200],
        }
    )


def test_maps_names_types_and_order() -> None:
    result = standardize_ohlcv(raw_yahoo_like(), date_column="Date")
    assert list(result.columns) == list(OHLCV_COLUMNS)
    assert isinstance(result.index, pd.DatetimeIndex)
    assert result.index.name == "date"
    assert result.index.is_monotonic_increasing
    assert (result.dtypes == np.float64).all()
    assert result.loc["2025-01-02", "open"] == 10.0  # parsed from text
    assert result.loc["2025-01-02", "close"] == 10.1  # unadjusted close by default


def test_column_map_selects_the_adjusted_close() -> None:
    raw = raw_yahoo_like().drop(columns="Close")
    result = standardize_ohlcv(raw, date_column="Date", column_map={"Adj Close": "close"})
    assert result.loc["2025-01-02", "close"] == 10.0


def test_extra_columns_are_dropped_and_input_is_untouched() -> None:
    raw = raw_yahoo_like()
    original = raw.copy()
    result = standardize_ohlcv(raw, date_column="Date")
    assert "adj_close" not in result.columns
    pd.testing.assert_frame_equal(raw, original)


def test_close_only_table_is_valid() -> None:
    raw = pd.DataFrame({"close": [1.0, 2.0]}, index=["2025-01-02", "2025-01-03"])
    result = standardize_ohlcv(raw)
    assert list(result.columns) == ["close"]


def test_timezone_aware_dates_keep_their_local_calendar_day() -> None:
    index = pd.DatetimeIndex(["2025-01-02 00:00", "2025-01-03 00:00"], tz="America/Sao_Paulo")
    result = standardize_ohlcv(pd.DataFrame({"close": [1.0, 2.0]}, index=index))
    assert pd.DatetimeIndex(result.index).tz is None
    assert [str(date.date()) for date in result.index] == ["2025-01-02", "2025-01-03"]


def test_stable_sort_preserves_order_of_duplicated_dates() -> None:
    raw = pd.DataFrame(
        {"date": ["2025-01-03", "2025-01-02", "2025-01-02"], "close": [3.0, 1.0, 2.0]}
    )
    result = standardize_ohlcv(raw, date_column="date")
    assert result["close"].tolist() == [1.0, 2.0, 3.0]


def test_missing_values_are_kept_for_later_cleaning() -> None:
    raw = pd.DataFrame({"date": ["2025-01-02", "2025-01-03"], "close": [1.0, None]})
    assert standardize_ohlcv(raw, date_column="date")["close"].isna().sum() == 1


@pytest.mark.parametrize(
    ("raw", "kwargs", "message"),
    [
        (pd.DataFrame({"close": [1.0]}), {"date_column": "Date"}, "date column 'Date'"),
        (pd.DataFrame({"date": ["2025-01-02"], "price": [1.0]}), {"date_column": "date"}, "close"),
        (
            pd.DataFrame({"date": ["2025-01-02"], "Close": [1.0], "Adj Close": [1.0]}),
            {"date_column": "date", "column_map": {"Adj Close": "close"}},
            "same canonical column",
        ),
        (pd.DataFrame({"date": ["not a date"], "close": [1.0]}), {"date_column": "date"}, "dates"),
        (pd.DataFrame({"date": [None], "close": [1.0]}), {"date_column": "date"}, "missing"),
        (
            pd.DataFrame({"date": ["2025-01-02"], "close": ["1,5"]}),
            {"date_column": "date"},
            "non-numeric",
        ),
    ],
    ids=["no-date-column", "no-close", "duplicate-target", "bad-date", "nat", "bad-number"],
)
def test_rejects_unmappable_tables(
    raw: pd.DataFrame, kwargs: dict[str, object], message: str
) -> None:
    with pytest.raises(InputValidationError, match=message):
        standardize_ohlcv(raw, **kwargs)  # type: ignore[arg-type]


def test_rejects_non_frames() -> None:
    with pytest.raises(TypeError, match="DataFrame"):
        standardize_ohlcv([1, 2, 3])  # type: ignore[arg-type]

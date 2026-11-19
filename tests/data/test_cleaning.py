from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from quantlab.data import check_ohlcv_integrity, clean_ohlcv
from quantlab.exceptions import InputValidationError


def with_duplicate(ohlcv: pd.DataFrame) -> pd.DataFrame:
    """Repeat the second bar with a corrected close, as a vendor correction would."""
    correction = ohlcv.iloc[[1]].copy()
    correction["close"] = 10.6
    return pd.concat([ohlcv.iloc[:2], correction, ohlcv.iloc[2:]])


@pytest.mark.parametrize(("policy", "kept_close"), [("first", 10.5), ("last", 10.6)])
def test_duplicate_policy_chooses_which_row_survives(
    ohlcv: pd.DataFrame, policy: str, kept_close: float
) -> None:
    result = clean_ohlcv(with_duplicate(ohlcv), duplicates=policy, missing="drop")  # type: ignore[arg-type]
    assert result.data.index.is_unique
    assert result.data.loc[ohlcv.index[1], "close"] == kept_close
    assert result.report.duplicate_dates_removed == (ohlcv.index[1],)
    assert (result.report.rows_in, result.report.rows_out) == (6, 5)


def test_drop_policy_removes_incomplete_rows(ohlcv: pd.DataFrame) -> None:
    ohlcv.loc[ohlcv.index[2], "close"] = np.nan
    ohlcv.loc[ohlcv.index[4], "volume"] = np.nan
    result = clean_ohlcv(ohlcv, duplicates="last", missing="drop")
    assert list(result.data.index) == list(ohlcv.index[[0, 1, 3]])
    assert result.report.rows_dropped == (ohlcv.index[2], ohlcv.index[4])
    assert result.report.prices_forward_filled == 0
    assert result.report.volumes_set_to_zero == 0
    assert result.report.max_fill is None


def test_forward_fill_carries_prices_and_zeroes_volume(ohlcv: pd.DataFrame) -> None:
    ohlcv.iloc[2, :] = np.nan  # a whole missing session
    result = clean_ohlcv(ohlcv, duplicates="last", missing="ffill")
    row = result.data.loc[ohlcv.index[2]]
    np.testing.assert_array_equal(row[["open", "high", "low", "close"]], ohlcv.iloc[1, :4])
    assert row["volume"] == 0.0
    assert result.report.prices_forward_filled == 4
    assert result.report.volumes_set_to_zero == 1
    assert result.report.rows_dropped == ()
    assert check_ohlcv_integrity(result.data).is_valid


def test_leading_gaps_cannot_be_filled_and_are_dropped(ohlcv: pd.DataFrame) -> None:
    ohlcv.loc[ohlcv.index[0], "close"] = np.nan
    result = clean_ohlcv(ohlcv, duplicates="first", missing="ffill")
    assert result.report.rows_dropped == (ohlcv.index[0],)
    assert result.report.prices_forward_filled == 0
    assert len(result.data) == 4


def test_max_fill_limits_consecutive_fills(ohlcv: pd.DataFrame) -> None:
    ohlcv.loc[ohlcv.index[1:4], "close"] = np.nan  # three consecutive gaps
    result = clean_ohlcv(ohlcv, duplicates="first", missing="ffill", max_fill=2)
    assert result.report.prices_forward_filled == 2
    assert result.report.rows_dropped == (ohlcv.index[3],)
    assert result.report.max_fill == 2


def test_input_is_not_modified(ohlcv: pd.DataFrame) -> None:
    ohlcv.iloc[2, :] = np.nan
    original = ohlcv.copy()
    clean_ohlcv(ohlcv, duplicates="last", missing="ffill")
    pd.testing.assert_frame_equal(ohlcv, original)


def test_clean_data_passes_through_unchanged(ohlcv: pd.DataFrame) -> None:
    result = clean_ohlcv(ohlcv, duplicates="last", missing="drop")
    pd.testing.assert_frame_equal(result.data, ohlcv)
    assert result.report.duplicate_dates_removed == ()
    assert result.report.rows_dropped == ()


def test_rejects_unknown_policies_and_unsorted_data(ohlcv: pd.DataFrame) -> None:
    with pytest.raises(InputValidationError, match="duplicates"):
        clean_ohlcv(ohlcv, duplicates="newest", missing="drop")  # type: ignore[arg-type]
    with pytest.raises(InputValidationError, match="missing"):
        clean_ohlcv(ohlcv, duplicates="last", missing="interpolate")  # type: ignore[arg-type]
    with pytest.raises(InputValidationError, match="max_fill"):
        clean_ohlcv(ohlcv, duplicates="last", missing="ffill", max_fill=0)
    with pytest.raises(InputValidationError, match="sorted"):
        clean_ohlcv(ohlcv.iloc[::-1], duplicates="last", missing="drop")


def test_forward_fill_without_volume_column(ohlcv: pd.DataFrame) -> None:
    prices = ohlcv.drop(columns="volume")
    prices.loc[prices.index[2], "close"] = np.nan
    result = clean_ohlcv(prices, duplicates="first", missing="ffill")
    assert result.report.prices_forward_filled == 1
    assert result.report.volumes_set_to_zero == 0
    assert list(result.data.columns) == ["open", "high", "low", "close"]

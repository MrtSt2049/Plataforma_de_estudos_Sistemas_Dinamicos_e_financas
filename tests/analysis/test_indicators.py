from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from quantlab.analysis import exponential_moving_average, simple_moving_average
from quantlab.exceptions import InputValidationError, InsufficientDataError


def test_sma_known_values() -> None:
    series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0], index=pd.bdate_range("2025-01-01", periods=5))
    result = simple_moving_average(series, 3)
    np.testing.assert_allclose(result.to_numpy(), [2.0, 3.0, 4.0], rtol=1e-15)
    assert result.index.equals(series.index[2:])


def test_sma_window_one_is_identity(daily_prices: pd.Series[float]) -> None:
    pd.testing.assert_series_equal(simple_moving_average(daily_prices, 1), daily_prices)


def test_sma_matches_pandas_rolling_mean(daily_prices: pd.Series[float]) -> None:
    expected = daily_prices.rolling(20).mean().dropna()
    np.testing.assert_allclose(
        simple_moving_average(daily_prices, 20).to_numpy(), expected.to_numpy(), rtol=1e-12
    )


def test_ema_matches_explicit_recursion(daily_prices: pd.Series[float]) -> None:
    span = 10
    weight = 2.0 / (span + 1.0)
    values = daily_prices.to_numpy()
    expected = np.empty_like(values)
    expected[0] = values[0]
    for t in range(1, values.size):
        expected[t] = weight * values[t] + (1.0 - weight) * expected[t - 1]
    np.testing.assert_allclose(
        exponential_moving_average(daily_prices, span).to_numpy(), expected, rtol=1e-13
    )


def test_ema_span_one_is_identity(daily_prices: pd.Series[float]) -> None:
    np.testing.assert_allclose(
        exponential_moving_average(daily_prices, 1).to_numpy(), daily_prices.to_numpy()
    )


def test_ema_of_constant_series_is_constant() -> None:
    result = exponential_moving_average(pd.Series([7.5] * 30), 5)
    np.testing.assert_allclose(result.to_numpy(), 7.5, rtol=1e-15)


def test_ema_keeps_index_and_name(daily_prices: pd.Series[float]) -> None:
    result = exponential_moving_average(daily_prices, 12)
    assert result.index.equals(daily_prices.index)
    assert result.name == daily_prices.name


@pytest.mark.parametrize("func", [simple_moving_average, exponential_moving_average])
def test_rejects_invalid_window(func: object) -> None:
    assert callable(func)
    with pytest.raises(InputValidationError):
        func(pd.Series([1.0, 2.0]), 0)
    with pytest.raises(TypeError):
        func(pd.Series([1.0, 2.0]), 2.5)


def test_sma_rejects_window_longer_than_data() -> None:
    with pytest.raises(InsufficientDataError, match="window=5"):
        simple_moving_average(pd.Series([1.0, 2.0, 3.0]), 5)


def test_rejects_missing_values() -> None:
    with pytest.raises(InputValidationError, match="missing"):
        exponential_moving_average(pd.Series([1.0, np.nan, 3.0]), 2)

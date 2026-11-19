from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from quantlab.analysis import cumulative_returns, drawdowns, max_drawdown, simple_returns
from quantlab.exceptions import DomainError, InputValidationError, InsufficientDataError

DATES = pd.bdate_range("2025-01-01", periods=7)


def test_drawdown_series_known_values() -> None:
    prices = pd.Series([100.0, 120.0, 90.0, 110.0, 130.0, 65.0, 70.0], index=DATES)
    expected = [0.0, 0.0, -0.25, -1.0 / 12.0, 0.0, -0.5, -60.0 / 130.0]
    np.testing.assert_allclose(drawdowns(prices).to_numpy(), expected, rtol=1e-15)


def test_max_drawdown_without_recovery() -> None:
    prices = pd.Series([100.0, 120.0, 90.0, 110.0, 130.0, 65.0, 70.0], index=DATES)
    result = max_drawdown(prices)
    assert result.value == pytest.approx(-0.5, rel=1e-15)
    assert result.peak == DATES[4]
    assert result.trough == DATES[5]
    assert result.recovery is None


def test_max_drawdown_with_recovery_uses_latest_peak() -> None:
    prices = pd.Series([100.0, 80.0, 100.0, 50.0, 90.0, 100.0, 120.0], index=DATES)
    result = max_drawdown(prices)
    assert result.value == pytest.approx(-0.5)
    assert result.peak == DATES[2]  # 100 is reached at positions 0 and 2; the latest counts
    assert result.trough == DATES[3]
    assert result.recovery == DATES[5]  # first return to the peak level (equality counts)


def test_first_of_tied_worst_declines_is_reported() -> None:
    prices = pd.Series([100.0, 50.0, 100.0, 50.0, 100.0, 101.0, 102.0], index=DATES)
    result = max_drawdown(prices)
    assert result.trough == DATES[1]
    assert result.recovery == DATES[2]


def test_increasing_prices_have_no_drawdown() -> None:
    prices = pd.Series(np.linspace(10.0, 20.0, 7), index=DATES)
    assert (drawdowns(prices).to_numpy() == 0.0).all()
    result = max_drawdown(prices)
    assert result.value == 0.0
    assert (result.peak, result.trough, result.recovery) == (None, None, None)


def test_drawdowns_are_non_positive_and_zero_at_new_highs(
    daily_prices: pd.Series[float],
) -> None:
    drawdown = drawdowns(daily_prices)
    assert (drawdown.to_numpy() <= 0.0).all()
    at_new_high = daily_prices.to_numpy() == daily_prices.cummax().to_numpy()
    assert (drawdown.to_numpy()[at_new_high] == 0.0).all()
    assert drawdown.index.equals(daily_prices.index)
    assert drawdown.name == daily_prices.name


def test_drawdowns_are_scale_invariant(daily_prices: pd.Series[float]) -> None:
    np.testing.assert_allclose(
        drawdowns(daily_prices * 37.5).to_numpy(), drawdowns(daily_prices).to_numpy(), atol=1e-15
    )


def test_wealth_index_from_returns_gives_the_same_drawdown(
    daily_prices: pd.Series[float],
) -> None:
    returns = simple_returns(daily_prices)
    wealth = pd.concat(
        [pd.Series([1.0], index=daily_prices.index[:1]), 1.0 + cumulative_returns(returns)]
    )
    assert max_drawdown(wealth).value == pytest.approx(max_drawdown(daily_prices).value, rel=1e-10)


def test_rejects_invalid_prices() -> None:
    with pytest.raises(InsufficientDataError):
        drawdowns(pd.Series([100.0]))
    with pytest.raises(DomainError, match="strictly positive"):
        max_drawdown(pd.Series([100.0, -1.0, 50.0]))
    with pytest.raises(InputValidationError, match="missing"):
        max_drawdown(pd.Series([100.0, np.nan, 50.0]))

from __future__ import annotations

import math
import statistics

import numpy as np
import pandas as pd
import pytest

from quantlab.analysis import (
    TRADING_DAYS_PER_YEAR,
    annualized_volatility,
    historical_volatility,
)
from quantlab.exceptions import DomainError, InputValidationError, InsufficientDataError

SAMPLE = [0.01, -0.02, 0.015, 0.003, -0.007, 0.012]


# --- agreement with an independent implementation ------------------------------------------------


def test_sample_volatility_matches_statistics_stdev() -> None:
    assert historical_volatility(pd.Series(SAMPLE)) == pytest.approx(
        statistics.stdev(SAMPLE), rel=1e-14
    )


def test_population_volatility_matches_statistics_pstdev() -> None:
    assert historical_volatility(pd.Series(SAMPLE), ddof=0) == pytest.approx(
        statistics.pstdev(SAMPLE), rel=1e-14
    )


def test_hand_computed_value() -> None:
    # mean 0, squared deviations sum to 1e-3, divisor n - 1 = 3
    returns = pd.Series([0.01, -0.01, 0.02, -0.02])
    assert historical_volatility(returns) == pytest.approx(math.sqrt(1e-3 / 3), rel=1e-14)


# --- properties ----------------------------------------------------------------------------------


def test_constant_returns_have_zero_volatility() -> None:
    # The floating-point mean of twenty 0.004 values is not exactly 0.004, so the result is
    # zero only up to rounding: about eps * |x| ~ 1e-18. A larger value would be a real error.
    assert historical_volatility(pd.Series([0.004] * 20)) == pytest.approx(0.0, abs=1e-16)
    # When the mean is exactly representable the result is exactly zero.
    assert historical_volatility(pd.Series([0.5] * 20)) == 0.0


def test_volatility_is_shift_invariant(rng: np.random.Generator) -> None:
    returns = pd.Series(rng.normal(0.0, 0.01, size=1_000))
    assert historical_volatility(returns + 0.05) == pytest.approx(
        historical_volatility(returns), rel=1e-12
    )


@pytest.mark.parametrize("factor", [-3.0, 0.5, 10.0])
def test_volatility_scales_with_absolute_factor(rng: np.random.Generator, factor: float) -> None:
    returns = pd.Series(rng.normal(0.0, 0.01, size=1_000))
    assert historical_volatility(returns * factor) == pytest.approx(
        abs(factor) * historical_volatility(returns), rel=1e-12
    )


def test_large_mean_does_not_cause_cancellation() -> None:
    """The two-pass algorithm keeps precision when the mean dwarfs the dispersion."""
    returns = pd.Series([1e6 + 0.01, 1e6 - 0.01, 1e6 + 0.02, 1e6 - 0.02])
    assert historical_volatility(returns) == pytest.approx(math.sqrt(1e-3 / 3), rel=1e-8)


def test_recovers_known_sigma_of_simulated_iid_returns(rng: np.random.Generator) -> None:
    """Sampling error of the estimate is about sigma / sqrt(2n), i.e. 0.22% here."""
    true_sigma = 0.01
    returns = pd.Series(rng.normal(0.0, true_sigma, size=100_000))
    assert historical_volatility(returns) == pytest.approx(true_sigma, rel=0.01)


def test_annualization_uses_square_root_of_time(daily_prices: pd.Series[float]) -> None:
    returns = daily_prices.pct_change().dropna()
    daily = historical_volatility(returns)
    assert annualized_volatility(returns) == pytest.approx(
        daily * math.sqrt(TRADING_DAYS_PER_YEAR), rel=1e-15
    )
    assert annualized_volatility(returns, periods_per_year=12) == pytest.approx(
        daily * math.sqrt(12), rel=1e-15
    )


def test_trading_days_constant() -> None:
    assert TRADING_DAYS_PER_YEAR == 252


# --- invalid input -------------------------------------------------------------------------------


def test_rejects_single_observation() -> None:
    with pytest.raises(InsufficientDataError, match="at least 2"):
        historical_volatility(pd.Series([0.01]))


def test_ddof_raises_minimum_sample_size() -> None:
    with pytest.raises(InsufficientDataError, match="at least 3"):
        historical_volatility(pd.Series([0.01, 0.02]), ddof=2)


def test_rejects_negative_ddof() -> None:
    with pytest.raises(InputValidationError, match="ddof"):
        historical_volatility(pd.Series(SAMPLE), ddof=-1)


@pytest.mark.parametrize("ddof", [1.0, True])
def test_rejects_non_integer_ddof(ddof: object) -> None:
    with pytest.raises(TypeError, match="ddof"):
        historical_volatility(pd.Series(SAMPLE), ddof=ddof)  # type: ignore[arg-type]


def test_rejects_missing_values() -> None:
    with pytest.raises(InputValidationError, match="missing"):
        historical_volatility(pd.Series([0.01, np.nan, 0.02]))


def test_rejects_infinite_values() -> None:
    with pytest.raises(InputValidationError, match="non-finite"):
        historical_volatility(pd.Series([0.01, np.inf, 0.02]))


def test_rejects_non_series() -> None:
    with pytest.raises(TypeError, match="pandas Series"):
        historical_volatility(np.array(SAMPLE))  # type: ignore[arg-type]


@pytest.mark.parametrize("periods", [0.0, -252.0])
def test_rejects_non_positive_periods_per_year(periods: float) -> None:
    with pytest.raises(DomainError, match="periods_per_year"):
        annualized_volatility(pd.Series(SAMPLE), periods_per_year=periods)


@pytest.mark.parametrize("periods", [math.nan, math.inf])
def test_rejects_non_finite_periods_per_year(periods: float) -> None:
    with pytest.raises(InputValidationError, match="periods_per_year"):
        annualized_volatility(pd.Series(SAMPLE), periods_per_year=periods)

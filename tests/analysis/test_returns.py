from __future__ import annotations

import math
from collections.abc import Callable
from fractions import Fraction

import numpy as np
import pandas as pd
import pytest

from quantlab.analysis import cumulative_returns, log_returns, simple_returns
from quantlab.exceptions import DomainError, InputValidationError, InsufficientDataError
from quantlab.types import NumericSeries

type ReturnFunction = Callable[[NumericSeries], pd.Series[float]]

RETURN_FUNCTIONS: list[ReturnFunction] = [simple_returns, log_returns]


# --- known values --------------------------------------------------------------------------------


def test_simple_returns_known_values() -> None:
    prices = pd.Series([100.0, 110.0, 99.0])
    np.testing.assert_allclose(simple_returns(prices).to_numpy(), [0.1, -0.1], rtol=1e-15)


def test_log_returns_known_values() -> None:
    prices = pd.Series([100.0, 110.0, 99.0])
    expected = [math.log(1.1), math.log(0.9)]
    np.testing.assert_allclose(log_returns(prices).to_numpy(), expected, rtol=1e-15)


def test_cumulative_returns_known_values() -> None:
    returns = pd.Series([0.1, -0.1])
    np.testing.assert_allclose(cumulative_returns(returns).to_numpy(), [0.1, -0.01], rtol=1e-14)


@pytest.mark.parametrize("func", RETURN_FUNCTIONS)
def test_constant_prices_give_zero_returns(func: ReturnFunction) -> None:
    returns = func(pd.Series([42.0] * 10))
    assert (returns.to_numpy() == 0.0).all()


# --- shape, index and metadata -------------------------------------------------------------------


@pytest.mark.parametrize("func", RETURN_FUNCTIONS)
def test_returns_are_labelled_by_the_later_observation(
    func: ReturnFunction, daily_prices: pd.Series[float]
) -> None:
    returns = func(daily_prices)
    assert len(returns) == len(daily_prices) - 1
    assert returns.index.equals(daily_prices.index[1:])
    assert returns.name == "ASSET"
    assert returns.dtype == np.float64


@pytest.mark.parametrize("func", RETURN_FUNCTIONS)
def test_input_is_not_modified(func: ReturnFunction, daily_prices: pd.Series[float]) -> None:
    original = daily_prices.copy()
    func(daily_prices)
    pd.testing.assert_series_equal(daily_prices, original)


def test_integer_prices_are_accepted() -> None:
    returns = simple_returns(pd.Series([100, 125, 100]))
    assert returns.dtype == np.float64
    np.testing.assert_allclose(returns.to_numpy(), [0.25, -0.2], rtol=1e-15)


def test_minimum_input_gives_one_return() -> None:
    assert len(simple_returns(pd.Series([1.0, 2.0]))) == 1


# --- mathematical invariants ---------------------------------------------------------------------


def test_log_returns_add_up_to_total_log_growth(daily_prices: pd.Series[float]) -> None:
    total = log_returns(daily_prices).sum()
    expected = math.log(daily_prices.iloc[-1] / daily_prices.iloc[0])
    assert total == pytest.approx(expected, rel=1e-12)


def test_log_and_simple_returns_are_consistent(daily_prices: pd.Series[float]) -> None:
    np.testing.assert_allclose(
        np.expm1(log_returns(daily_prices).to_numpy()),
        simple_returns(daily_prices).to_numpy(),
        rtol=1e-12,
    )


def test_cumulative_returns_reproduce_price_relatives(daily_prices: pd.Series[float]) -> None:
    cumulative = cumulative_returns(simple_returns(daily_prices))
    expected = daily_prices.iloc[1:] / daily_prices.iloc[0] - 1.0
    np.testing.assert_allclose(cumulative.to_numpy(), expected.to_numpy(), rtol=1e-10)
    assert cumulative.index.equals(daily_prices.index[1:])


def test_log_returns_are_scale_invariant(daily_prices: pd.Series[float]) -> None:
    np.testing.assert_allclose(
        log_returns(daily_prices * 1000.0).to_numpy(),
        log_returns(daily_prices).to_numpy(),
        rtol=1e-12,
        atol=1e-15,
    )


# --- numerical accuracy and extremes -------------------------------------------------------------


def test_tiny_moves_keep_relative_accuracy() -> None:
    """A move of ~1e-14 must not lose its digits to cancellation."""
    previous, current = 1.0, 1.0 + 2.0**-46
    exact = (Fraction(current) - Fraction(previous)) / Fraction(previous)

    result = simple_returns(pd.Series([previous, current])).iloc[0]
    assert result == pytest.approx(float(exact), rel=1e-15)

    log_result = log_returns(pd.Series([previous, current])).iloc[0]
    assert log_result == pytest.approx(math.log1p(float(exact)), rel=1e-15)


@pytest.mark.parametrize("scale", [1e-300, 1e300])
def test_extreme_price_magnitudes(scale: float) -> None:
    returns = simple_returns(pd.Series([1.0, 2.0, 1.0]) * scale)
    np.testing.assert_allclose(returns.to_numpy(), [1.0, -0.5], rtol=1e-15)


def test_total_loss_is_absorbing() -> None:
    cumulative = cumulative_returns(pd.Series([0.5, -1.0, 0.2, 3.0]))
    np.testing.assert_array_equal(cumulative.to_numpy(), [0.5, -1.0, -1.0, -1.0])


# --- invalid input -------------------------------------------------------------------------------


@pytest.mark.parametrize("func", RETURN_FUNCTIONS)
def test_rejects_non_series(func: ReturnFunction) -> None:
    with pytest.raises(TypeError, match="pandas Series"):
        func([100.0, 101.0])  # type: ignore[arg-type]


@pytest.mark.parametrize("func", RETURN_FUNCTIONS)
@pytest.mark.parametrize(
    "series",
    [pd.Series(["100", "101"]), pd.Series([True, False])],
    ids=["strings", "booleans"],
)
def test_rejects_non_numeric_dtype(func: ReturnFunction, series: pd.Series[float]) -> None:
    with pytest.raises(TypeError, match="numeric dtype"):
        func(series)


@pytest.mark.parametrize("func", RETURN_FUNCTIONS)
@pytest.mark.parametrize("values", [[], [100.0]], ids=["empty", "single"])
def test_rejects_too_few_prices(func: ReturnFunction, values: list[float]) -> None:
    with pytest.raises(InsufficientDataError, match="at least 2"):
        func(pd.Series(values, dtype=np.float64))


@pytest.mark.parametrize("func", RETURN_FUNCTIONS)
def test_rejects_missing_values(func: ReturnFunction) -> None:
    with pytest.raises(InputValidationError, match="1 missing value"):
        func(pd.Series([100.0, np.nan, 102.0]))


def test_error_message_lists_a_bounded_number_of_labels() -> None:
    prices = pd.Series([100.0] + [np.nan] * 8 + [101.0])
    with pytest.raises(InputValidationError, match=r"8 missing value.*\(3 more\)"):
        simple_returns(prices)


def test_rejects_nullable_missing_values() -> None:
    with pytest.raises(InputValidationError, match="missing value"):
        simple_returns(pd.Series([100, pd.NA, 102], dtype="Int64"))


@pytest.mark.parametrize("func", RETURN_FUNCTIONS)
@pytest.mark.parametrize("bad", [np.inf, -np.inf])
def test_rejects_infinite_values(func: ReturnFunction, bad: float) -> None:
    with pytest.raises(InputValidationError, match="non-finite"):
        func(pd.Series([100.0, bad, 102.0]))


@pytest.mark.parametrize("func", RETURN_FUNCTIONS)
@pytest.mark.parametrize("bad", [0.0, -5.0])
def test_rejects_non_positive_prices(func: ReturnFunction, bad: float) -> None:
    with pytest.raises(DomainError, match="strictly positive"):
        func(pd.Series([100.0, bad, 102.0]))


@pytest.mark.parametrize("func", RETURN_FUNCTIONS)
def test_rejects_unsorted_index(func: ReturnFunction) -> None:
    index = pd.to_datetime(["2024-01-03", "2024-01-02", "2024-01-04"])
    with pytest.raises(InputValidationError, match="increasing"):
        func(pd.Series([100.0, 101.0, 102.0], index=index))


@pytest.mark.parametrize("func", RETURN_FUNCTIONS)
def test_rejects_duplicated_index(func: ReturnFunction) -> None:
    index = pd.to_datetime(["2024-01-02", "2024-01-02", "2024-01-03"])
    with pytest.raises(InputValidationError, match="duplicated"):
        func(pd.Series([100.0, 101.0, 102.0], index=index))


def test_cumulative_returns_rejects_returns_below_total_loss() -> None:
    with pytest.raises(DomainError, match=">= -1"):
        cumulative_returns(pd.Series([0.1, -1.5]))


def test_cumulative_returns_rejects_empty_input() -> None:
    with pytest.raises(InsufficientDataError):
        cumulative_returns(pd.Series(np.empty(0)))


def test_cumulative_returns_rejects_missing_values() -> None:
    with pytest.raises(InputValidationError, match="missing"):
        cumulative_returns(pd.Series([0.1, np.nan]))

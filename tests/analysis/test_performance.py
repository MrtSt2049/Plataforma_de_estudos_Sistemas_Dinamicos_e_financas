from __future__ import annotations

import math
import statistics

import numpy as np
import pandas as pd
import pytest

from quantlab.analysis import periodic_rate_from_annual, sharpe_ratio
from quantlab.exceptions import ComputationError, DomainError, InputValidationError

SAMPLE = [0.01, -0.02, 0.015, 0.003, -0.007, 0.012, 0.004]


# --- periodic_rate_from_annual -------------------------------------------------------------------


def test_compounding_the_periodic_rate_recovers_the_annual_rate() -> None:
    periodic = periodic_rate_from_annual(0.1065, periods_per_year=252)
    assert (1.0 + periodic) ** 252 - 1.0 == pytest.approx(0.1065, rel=1e-12)


def test_monthly_rate_is_correctly_rounded() -> None:
    # (1.12)^(1/12) - 1 = 0.00948879293458297412635506919... (50-digit Decimal computation).
    # The naive float expression (1.12)**(1/12) - 1 is off by 7.5e-15 relative.
    assert periodic_rate_from_annual(0.12, periods_per_year=12) == pytest.approx(
        0.009488792934582974126, rel=1e-15
    )


def test_zero_rate_is_zero() -> None:
    assert periodic_rate_from_annual(0.0) == 0.0


def test_tiny_rate_keeps_precision() -> None:
    # For tiny r, (1 + r)^(1/N) - 1 ~ r / N; naive pow(1 + r, 1/N) - 1 would lose digits.
    assert periodic_rate_from_annual(1e-12, periods_per_year=252) == pytest.approx(
        1e-12 / 252, rel=1e-9
    )


@pytest.mark.parametrize("rate", [-1.0, -2.0])
def test_rejects_rates_at_or_below_total_loss(rate: float) -> None:
    with pytest.raises(DomainError, match="annual_rate"):
        periodic_rate_from_annual(rate)


def test_rejects_non_positive_periods() -> None:
    with pytest.raises(DomainError, match="periods_per_year"):
        periodic_rate_from_annual(0.1, periods_per_year=0)


# --- sharpe_ratio --------------------------------------------------------------------------------


def test_matches_definition_with_independent_statistics() -> None:
    rf = 0.0004
    excess = [x - rf for x in SAMPLE]
    expected = statistics.mean(excess) / statistics.stdev(excess) * math.sqrt(252)
    assert sharpe_ratio(pd.Series(SAMPLE), risk_free_rate=rf) == pytest.approx(expected, rel=1e-12)


def test_per_period_ratio_when_periods_per_year_is_one() -> None:
    expected = statistics.mean(SAMPLE) / statistics.stdev(SAMPLE)
    assert sharpe_ratio(pd.Series(SAMPLE), periods_per_year=1) == pytest.approx(expected, rel=1e-12)


def test_hand_computed_value() -> None:
    # mean 0.01, sample std of [0, 0.02] is sqrt(2e-4)
    returns = pd.Series([0.0, 0.02])
    assert sharpe_ratio(returns, periods_per_year=1) == pytest.approx(
        0.01 / math.sqrt(2e-4), rel=1e-14
    )


@pytest.mark.parametrize("factor", [0.5, 3.0])
def test_is_invariant_to_positive_leverage_without_risk_free_rate(factor: float) -> None:
    returns = pd.Series(SAMPLE)
    assert sharpe_ratio(returns * factor) == pytest.approx(sharpe_ratio(returns), rel=1e-12)


def test_changes_sign_with_negated_returns() -> None:
    returns = pd.Series(SAMPLE)
    assert sharpe_ratio(-returns) == pytest.approx(-sharpe_ratio(returns), rel=1e-12)


def test_risk_free_rate_only_shifts_the_mean() -> None:
    returns = pd.Series(SAMPLE)
    rf = 0.001
    shifted = sharpe_ratio(returns - rf, periods_per_year=1)
    assert sharpe_ratio(returns, risk_free_rate=rf, periods_per_year=1) == pytest.approx(
        shifted, rel=1e-12
    )


def test_recovers_true_ratio_of_simulated_iid_returns(rng: np.random.Generator) -> None:
    """Per-period SR 0.05 with n = 200 000: standard error ~ sqrt(1.00125 / n) ~ 0.0022."""
    mu, sigma = 0.0005, 0.01
    returns = pd.Series(rng.normal(mu, sigma, size=200_000))
    assert sharpe_ratio(returns, periods_per_year=1) == pytest.approx(mu / sigma, abs=0.01)


@pytest.mark.parametrize("value", [0.004, 0.0, -0.01])
def test_constant_returns_raise_instead_of_returning_a_huge_number(value: float) -> None:
    with pytest.raises(ComputationError, match="zero dispersion"):
        sharpe_ratio(pd.Series([value] * 20))


def test_tiny_but_real_dispersion_is_accepted() -> None:
    returns = pd.Series([0.004, 0.004 + 1e-10] * 10)
    assert math.isfinite(sharpe_ratio(returns))


def test_rejects_invalid_input() -> None:
    with pytest.raises(InputValidationError, match="missing"):
        sharpe_ratio(pd.Series([0.01, np.nan, 0.02]))
    with pytest.raises(InputValidationError, match="risk_free_rate"):
        sharpe_ratio(pd.Series(SAMPLE), risk_free_rate=math.nan)
    with pytest.raises(DomainError, match="periods_per_year"):
        sharpe_ratio(pd.Series(SAMPLE), periods_per_year=-1)

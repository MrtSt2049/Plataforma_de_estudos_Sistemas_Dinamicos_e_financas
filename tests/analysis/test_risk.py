from __future__ import annotations

from statistics import NormalDist

import numpy as np
import pandas as pd
import pytest

from quantlab.analysis import historical_cvar, historical_var
from quantlab.exceptions import DomainError, InputValidationError, InsufficientDataError


def losses_one_to_n(n: int, rng: np.random.Generator) -> pd.Series[float]:
    """Returns whose losses are exactly 1, 2, ..., n thousandths, in random order."""
    return pd.Series(-rng.permutation(np.arange(1, n + 1)) / 1000.0)


# --- hand-computed values ------------------------------------------------------------------------


def test_var_and_cvar_with_integer_tail(rng: np.random.Generator) -> None:
    returns = losses_one_to_n(100, rng)
    # 95% VaR is the 95th smallest loss; CVaR averages the 5 largest: (96 + ... + 100) / 5.
    assert historical_var(returns, confidence=0.95) == pytest.approx(0.095, rel=1e-15)
    assert historical_cvar(returns, confidence=0.95) == pytest.approx(0.098, rel=1e-12)
    assert historical_var(returns, confidence=0.99) == pytest.approx(0.099, rel=1e-15)
    assert historical_cvar(returns, confidence=0.99) == pytest.approx(0.100, rel=1e-12)


def test_cvar_weights_the_boundary_observation_fractionally(rng: np.random.Generator) -> None:
    returns = losses_one_to_n(30, rng)
    # n(1 - a) = 1.5: the largest loss counts fully, the second with weight 0.5.
    assert historical_cvar(returns, confidence=0.95) == pytest.approx(
        (0.030 + 0.5 * 0.029) / 1.5, rel=1e-12
    )
    # ceil(30 * 0.95) = 29th smallest loss
    assert historical_var(returns, confidence=0.95) == pytest.approx(0.029, rel=1e-15)


def test_order_of_observations_does_not_matter(rng: np.random.Generator) -> None:
    returns = pd.Series(rng.normal(0.0, 0.01, size=500))
    shuffled = pd.Series(rng.permutation(returns.to_numpy()))
    assert historical_var(returns) == historical_var(shuffled)
    assert historical_cvar(returns) == pytest.approx(historical_cvar(shuffled), rel=1e-12)


# --- independent definitions ---------------------------------------------------------------------


@pytest.mark.parametrize("confidence", [0.9, 0.95, 0.975, 0.99])
def test_cvar_equals_the_average_var_beyond_the_confidence_level(
    rng: np.random.Generator, confidence: float
) -> None:
    """CVaR_a = (1 / (1 - a)) * integral of VaR_u for u in (a, 1)."""
    returns = pd.Series(rng.standard_t(df=4, size=1_000) * 0.01)
    losses = -returns.to_numpy()
    grid = np.linspace(confidence, 1.0, 400_001)[1:-1]
    average_var = np.quantile(losses, grid, method="inverted_cdf").mean()
    assert historical_cvar(returns, confidence=confidence) == pytest.approx(average_var, rel=1e-4)


def test_matches_normal_distribution_for_a_large_gaussian_sample(
    rng: np.random.Generator,
) -> None:
    sigma, confidence = 0.01, 0.99
    returns = pd.Series(rng.normal(0.0, sigma, size=1_000_000))
    standard = NormalDist()
    z = standard.inv_cdf(confidence)
    assert historical_var(returns, confidence=confidence) == pytest.approx(sigma * z, rel=0.01)
    expected_cvar = sigma * standard.pdf(z) / (1.0 - confidence)
    assert historical_cvar(returns, confidence=confidence) == pytest.approx(expected_cvar, rel=0.01)


# --- coherence properties ------------------------------------------------------------------------


@pytest.mark.parametrize("confidence", [0.9, 0.95, 0.99])
def test_cvar_is_never_below_var(rng: np.random.Generator, confidence: float) -> None:
    returns = pd.Series(rng.standard_t(df=3, size=2_000) * 0.01)
    assert historical_cvar(returns, confidence=confidence) >= historical_var(
        returns, confidence=confidence
    )


def test_measures_grow_with_the_confidence_level(rng: np.random.Generator) -> None:
    returns = pd.Series(rng.normal(0.0, 0.01, size=5_000))
    levels = [0.9, 0.95, 0.99]
    var = [historical_var(returns, confidence=level) for level in levels]
    cvar = [historical_cvar(returns, confidence=level) for level in levels]
    assert var == sorted(var)
    assert cvar == sorted(cvar)


def test_translation_and_positive_homogeneity(rng: np.random.Generator) -> None:
    returns = pd.Series(rng.normal(0.0, 0.01, size=1_000))
    shift, scale = 0.002, 3.0
    for measure in (historical_var, historical_cvar):
        base = measure(returns)
        assert measure(returns + shift) == pytest.approx(base - shift, rel=1e-12)
        assert measure(returns * scale) == pytest.approx(base * scale, rel=1e-12)


def test_var_is_negative_when_even_the_tail_is_a_gain() -> None:
    returns = pd.Series(np.linspace(0.01, 0.05, 40))
    assert historical_var(returns) < 0.0
    assert historical_cvar(returns) < 0.0


# --- invalid input -------------------------------------------------------------------------------


@pytest.mark.parametrize(("confidence", "minimum"), [(0.95, 20), (0.99, 100), (0.5, 2)])
def test_requires_at_least_one_observation_in_the_tail(confidence: float, minimum: int) -> None:
    with pytest.raises(InsufficientDataError, match=f"at least {minimum}"):
        historical_var(pd.Series(np.zeros(minimum - 1)), confidence=confidence)
    historical_var(pd.Series(np.zeros(minimum)), confidence=confidence)


@pytest.mark.parametrize("confidence", [0.0, 1.0, -0.5, 95.0])
def test_rejects_confidence_outside_the_open_unit_interval(confidence: float) -> None:
    with pytest.raises(DomainError, match="confidence"):
        historical_cvar(pd.Series(np.zeros(200)), confidence=confidence)


def test_rejects_missing_values() -> None:
    returns = pd.Series(np.zeros(50))
    returns.iloc[10] = np.nan
    with pytest.raises(InputValidationError, match="missing"):
        historical_var(returns)

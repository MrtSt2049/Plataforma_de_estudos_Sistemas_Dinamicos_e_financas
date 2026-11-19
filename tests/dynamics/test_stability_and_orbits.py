from __future__ import annotations

import math

import numpy as np
import pytest

from quantlab.dynamics import FixedPointStability, classify_map_fixed_point, detect_period
from quantlab.exceptions import InputValidationError, InsufficientDataError

# --- classify_map_fixed_point --------------------------------------------------------------------


@pytest.mark.parametrize(
    ("multiplier", "expected"),
    [
        (0.0, FixedPointStability.STABLE),
        (0.5, FixedPointStability.STABLE),
        (-0.999, FixedPointStability.STABLE),
        (1.0, FixedPointStability.NON_HYPERBOLIC),
        (-1.0, FixedPointStability.NON_HYPERBOLIC),
        (-1.0000000000000004, FixedPointStability.NON_HYPERBOLIC),
        (1.001, FixedPointStability.UNSTABLE),
        (-3.0, FixedPointStability.UNSTABLE),
    ],
)
def test_classification(multiplier: float, expected: FixedPointStability) -> None:
    assert classify_map_fixed_point(multiplier) is expected


def test_zero_tolerance_makes_classification_exact() -> None:
    assert classify_map_fixed_point(1.0 + 1e-15, atol=0.0) is FixedPointStability.UNSTABLE
    assert classify_map_fixed_point(1.0, atol=0.0) is FixedPointStability.NON_HYPERBOLIC


def test_rejects_negative_tolerance() -> None:
    with pytest.raises(InputValidationError, match="atol"):
        classify_map_fixed_point(0.5, atol=-1e-9)


@pytest.mark.parametrize("bad", [math.nan, math.inf])
def test_rejects_non_finite_multiplier(bad: float) -> None:
    with pytest.raises(InputValidationError, match="multiplier"):
        classify_map_fixed_point(bad)


# --- detect_period -------------------------------------------------------------------------------


@pytest.mark.parametrize("cycle", [[0.3], [0.2, 0.8], [0.1, 0.5, 0.9], [0.1, 0.4, 0.6, 0.9]])
def test_detects_exact_cycles(cycle: list[float]) -> None:
    orbit = np.tile(cycle, 50)
    assert detect_period(orbit, max_period=16) == len(cycle)


def test_returns_smallest_period() -> None:
    # A 2-cycle is also 4-periodic and 6-periodic; only 2 must be reported.
    assert detect_period(np.tile([0.2, 0.8], 50), max_period=8) == 2


def test_tolerance_absorbs_small_noise(rng: np.random.Generator) -> None:
    orbit = np.tile([0.2, 0.8], 100) + rng.uniform(-1e-12, 1e-12, size=200)
    assert detect_period(orbit, max_period=8, atol=1e-9) == 2
    assert detect_period(orbit, max_period=8, atol=1e-14) is None


def test_random_sequence_is_not_periodic(rng: np.random.Generator) -> None:
    assert detect_period(rng.uniform(size=500), max_period=64) is None


def test_requires_twice_max_period_points() -> None:
    with pytest.raises(InsufficientDataError, match="at least 20"):
        detect_period(np.zeros(19), max_period=10)


def test_rejects_multidimensional_orbit() -> None:
    with pytest.raises(InputValidationError, match="one-dimensional"):
        detect_period(np.zeros((10, 2)), max_period=2)


def test_rejects_non_finite_orbit() -> None:
    with pytest.raises(InputValidationError, match="NaN or infinite"):
        detect_period([0.1, np.nan, 0.1, 0.2], max_period=2)


def test_rejects_invalid_parameters() -> None:
    with pytest.raises(InputValidationError, match="max_period"):
        detect_period(np.zeros(10), max_period=0)
    with pytest.raises(InputValidationError, match="atol"):
        detect_period(np.zeros(10), max_period=2, atol=-1.0)

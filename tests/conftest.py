"""Shared fixtures. Every random input uses a fixed seed so that runs are reproducible."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

TEST_SEED = 20261119


@pytest.fixture
def rng() -> np.random.Generator:
    return np.random.default_rng(TEST_SEED)


@pytest.fixture
def daily_prices(rng: np.random.Generator) -> pd.Series[float]:
    """A geometric random walk of 500 business days starting at 100."""
    log_steps = rng.normal(loc=0.0003, scale=0.015, size=499)
    values = 100.0 * np.exp(np.concatenate([[0.0], np.cumsum(log_steps)]))
    index = pd.bdate_range("2024-01-01", periods=values.size)
    return pd.Series(values, index=index, name="ASSET")


@pytest.fixture
def ohlcv() -> pd.DataFrame:
    """Five consistent daily bars in the canonical OHLCV schema."""
    index = pd.DatetimeIndex(pd.bdate_range("2025-03-03", periods=5), name="date")
    close = np.array([10.0, 10.5, 10.2, 10.8, 11.0])
    return pd.DataFrame(
        {
            "open": close - 0.1,
            "high": close + 0.3,
            "low": close - 0.4,
            "close": close,
            "volume": [1_000.0, 1_500.0, 900.0, 2_000.0, 1_200.0],
        },
        index=index,
    )

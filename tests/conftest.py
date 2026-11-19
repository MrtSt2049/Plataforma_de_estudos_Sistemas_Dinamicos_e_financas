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

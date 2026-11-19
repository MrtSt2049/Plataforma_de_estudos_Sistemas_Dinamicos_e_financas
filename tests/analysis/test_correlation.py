from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from quantlab.analysis import correlation_matrix, covariance_matrix, historical_volatility
from quantlab.exceptions import ComputationError, InputValidationError, InsufficientDataError


@pytest.fixture
def asset_returns(rng: np.random.Generator) -> pd.DataFrame:
    """Three correlated assets: B follows A, C moves against A."""
    common = rng.normal(0.0, 0.01, size=750)
    frame = pd.DataFrame(
        {
            "A": common + rng.normal(0.0, 0.004, size=750),
            "B": 0.8 * common + rng.normal(0.0, 0.006, size=750),
            "C": -0.5 * common + rng.normal(0.0, 0.01, size=750),
        },
        index=pd.bdate_range("2023-01-02", periods=750),
    )
    return frame


# --- agreement with independent implementations --------------------------------------------------


def test_covariance_matches_numpy(asset_returns: pd.DataFrame) -> None:
    np.testing.assert_allclose(
        covariance_matrix(asset_returns).to_numpy(),
        np.cov(asset_returns.to_numpy(), rowvar=False),
        rtol=1e-12,
    )


def test_correlation_matches_numpy(asset_returns: pd.DataFrame) -> None:
    np.testing.assert_allclose(
        correlation_matrix(asset_returns).to_numpy(),
        np.corrcoef(asset_returns.to_numpy(), rowvar=False),
        rtol=1e-12,
        atol=1e-15,
    )


def test_diagonal_holds_the_variances(asset_returns: pd.DataFrame) -> None:
    covariance = covariance_matrix(asset_returns)
    for column in asset_returns.columns:
        assert covariance.loc[column, column] == pytest.approx(
            historical_volatility(asset_returns[column]) ** 2, rel=1e-12
        )


# --- structural properties -----------------------------------------------------------------------


def test_matrices_are_labelled_and_symmetric(asset_returns: pd.DataFrame) -> None:
    for matrix in (covariance_matrix(asset_returns), correlation_matrix(asset_returns)):
        assert list(matrix.index) == list(asset_returns.columns)
        assert list(matrix.columns) == list(asset_returns.columns)
        np.testing.assert_array_equal(matrix.to_numpy(), matrix.to_numpy().T)


def test_covariance_is_positive_semidefinite(asset_returns: pd.DataFrame) -> None:
    eigenvalues = np.linalg.eigvalsh(covariance_matrix(asset_returns).to_numpy())
    assert eigenvalues.min() > -1e-15


def test_correlation_bounds_and_signs(asset_returns: pd.DataFrame) -> None:
    correlation = correlation_matrix(asset_returns)
    np.testing.assert_array_equal(np.diag(correlation.to_numpy()), [1.0, 1.0, 1.0])
    assert (np.abs(correlation.to_numpy()) <= 1.0).all()
    values = correlation.to_numpy()  # rows and columns in the order A, B, C
    assert values[0, 1] > 0.7
    assert values[0, 2] < -0.3


def test_perfectly_dependent_series_are_clipped_to_the_bounds() -> None:
    base = pd.Series(np.linspace(-0.02, 0.03, 40) ** 3)
    frame = pd.DataFrame({"x": base, "twice": 2.0 * base + 0.001, "mirror": -3.0 * base})
    correlation = correlation_matrix(frame)
    assert correlation.loc["x", "twice"] == pytest.approx(1.0, abs=1e-14)
    assert correlation.loc["x", "mirror"] == pytest.approx(-1.0, abs=1e-14)
    assert (np.abs(correlation.to_numpy()) <= 1.0).all()


def test_annualized_covariance_scales_linearly(asset_returns: pd.DataFrame) -> None:
    np.testing.assert_allclose(
        covariance_matrix(asset_returns, periods_per_year=252).to_numpy(),
        covariance_matrix(asset_returns).to_numpy() * 252,
        rtol=1e-15,
    )


def test_correlation_is_invariant_to_scale_and_shift(asset_returns: pd.DataFrame) -> None:
    transformed = asset_returns * [2.0, 0.5, 10.0] + [0.01, -0.02, 0.0]
    np.testing.assert_allclose(
        correlation_matrix(transformed).to_numpy(),
        correlation_matrix(asset_returns).to_numpy(),
        atol=1e-12,
    )


def test_single_column_is_supported(asset_returns: pd.DataFrame) -> None:
    assert correlation_matrix(asset_returns[["A"]]).to_numpy().tolist() == [[1.0]]


# --- invalid input -------------------------------------------------------------------------------


def test_constant_column_has_undefined_correlation(asset_returns: pd.DataFrame) -> None:
    frame = asset_returns.assign(FLAT=0.004)
    with pytest.raises(ComputationError, match="'FLAT'"):
        correlation_matrix(frame)


def test_rejects_unaligned_data_with_missing_values(asset_returns: pd.DataFrame) -> None:
    frame = asset_returns.copy()
    frame.iloc[5, 1] = np.nan
    with pytest.raises(InputValidationError, match="column 'B' contains 1 missing"):
        covariance_matrix(frame)


def test_rejects_infinite_values(asset_returns: pd.DataFrame) -> None:
    frame = asset_returns.copy()
    frame.iloc[3, 2] = np.inf
    with pytest.raises(InputValidationError, match="column 'C' contains non-finite"):
        correlation_matrix(frame)


def test_rejects_non_numeric_columns(asset_returns: pd.DataFrame) -> None:
    with pytest.raises(TypeError, match="'label'"):
        correlation_matrix(asset_returns.assign(label="x"))


def test_rejects_duplicated_columns(asset_returns: pd.DataFrame) -> None:
    frame = asset_returns.copy()
    frame.columns = pd.Index(["A", "A", "C"])
    with pytest.raises(InputValidationError, match="duplicated column"):
        covariance_matrix(frame)


def test_rejects_series_and_empty_frames(asset_returns: pd.DataFrame) -> None:
    with pytest.raises(TypeError, match="DataFrame"):
        covariance_matrix(asset_returns["A"])  # type: ignore[arg-type]
    with pytest.raises(InputValidationError, match="at least one column"):
        covariance_matrix(pd.DataFrame(index=asset_returns.index))
    with pytest.raises(InsufficientDataError):
        covariance_matrix(asset_returns.iloc[:1])


def test_rejects_unsorted_index(asset_returns: pd.DataFrame) -> None:
    with pytest.raises(InputValidationError, match="increasing"):
        correlation_matrix(asset_returns.iloc[::-1])

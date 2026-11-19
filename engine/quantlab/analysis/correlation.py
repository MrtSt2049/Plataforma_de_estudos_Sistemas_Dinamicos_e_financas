r"""Sample covariance and Pearson correlation matrices of several return series.

For returns :math:`X \in \mathbb{R}^{n \times k}` (rows are times, columns are
assets) with column means :math:`\bar X`:

.. math::

    \Sigma = \frac{(X - \bar X)^\top (X - \bar X)}{n - \delta},
    \qquad
    \rho_{ij} = \frac{\Sigma_{ij}}{\sqrt{\Sigma_{ii} \Sigma_{jj}}}

Correlation measures *linear* co-movement only. It says nothing about causality,
and a correlation estimated over one period can change sharply in another,
typically rising in crises, when diversification is most needed.
"""

from __future__ import annotations

import numpy as np
import numpy.typing as npt
import pandas as pd

from quantlab._numerics import dispersion_is_negligible
from quantlab._validation import validate_frame, validate_int, validate_positive_real
from quantlab.exceptions import ComputationError

_MIN_OBSERVATIONS = 2
_CORRELATION_BOUND = 1.0


def _sample_covariance(values: npt.NDArray[np.float64], ddof: int) -> npt.NDArray[np.float64]:
    """Two-pass covariance, symmetrized to remove rounding asymmetry."""
    centered = values - values.mean(axis=0)
    covariance: npt.NDArray[np.float64] = centered.T @ centered / (values.shape[0] - ddof)
    return (covariance + covariance.T) / 2.0


def covariance_matrix(
    returns: pd.DataFrame,
    *,
    ddof: int = 1,
    periods_per_year: float | None = None,
) -> pd.DataFrame:
    r"""Compute the sample covariance matrix of the columns of ``returns``.

    Parameters
    ----------
    returns
        One column of returns per asset, aligned on a common, unique, increasing
        index, with no missing or infinite values and at least ``max(2, ddof + 1)``
        rows. Align series of different calendars *before* calling, for example with
        an inner join on dates; this function does not drop or fill values.
    ddof
        Delta degrees of freedom. The divisor is ``n - ddof``.
    periods_per_year
        If given, annualize by multiplying every entry by :math:`N` (variances
        scale linearly with time under i.i.d. returns).

    Returns
    -------
    pandas.DataFrame
        Symmetric ``k x k`` matrix indexed and labelled by the columns of ``returns``.

    Raises
    ------
    TypeError
        If ``returns`` is not a DataFrame of numeric columns, or a parameter has the
        wrong type.
    InputValidationError
        If the data contain missing or infinite values, labels are duplicated, the
        index is not strictly increasing, or ``ddof`` is negative.
    DomainError
        If ``periods_per_year`` is not strictly positive.
    InsufficientDataError
        If there are fewer than ``max(2, ddof + 1)`` rows.

    Notes
    -----
    The result is positive semidefinite up to rounding. With fewer observations
    than assets (``n <= k``) it is singular, so it cannot be inverted, for example
    for portfolio optimization.
    """
    checked_ddof = validate_int(ddof, name="ddof", minimum=0)
    validated = validate_frame(
        returns, name="returns", min_rows=max(_MIN_OBSERVATIONS, checked_ddof + 1)
    )
    covariance = _sample_covariance(validated.to_numpy(), checked_ddof)
    if periods_per_year is not None:
        covariance = covariance * validate_positive_real(periods_per_year, name="periods_per_year")
    return pd.DataFrame(covariance, index=validated.columns, columns=validated.columns)


def correlation_matrix(returns: pd.DataFrame) -> pd.DataFrame:
    """Compute the Pearson correlation matrix of the columns of ``returns``.

    Parameters
    ----------
    returns
        Same requirements as in :func:`covariance_matrix`.

    Returns
    -------
    pandas.DataFrame
        Symmetric ``k x k`` matrix with ones on the diagonal and entries in
        ``[-1, 1]``, indexed and labelled by the columns of ``returns``.

    Raises
    ------
    TypeError, InputValidationError, InsufficientDataError
        Same conditions as in :func:`covariance_matrix`.
    ComputationError
        If a column has zero dispersion (or dispersion at rounding level): its
        correlation with anything is undefined.

    Notes
    -----
    Rounding can push an off-diagonal entry slightly outside ``[-1, 1]``, for
    example to ``1.0000000000000002`` for two proportional series. Entries are
    clipped back to the interval and the diagonal is set to exactly 1.
    """
    validated = validate_frame(returns, name="returns", min_rows=_MIN_OBSERVATIONS)
    values = validated.to_numpy()
    covariance = _sample_covariance(values, ddof=1)
    deviations = np.sqrt(np.diag(covariance))
    for position, column in enumerate(validated.columns):
        if dispersion_is_negligible(values[:, position], float(deviations[position])):
            raise ComputationError(
                f"Correlation is undefined: column {column!r} has zero dispersion."
            )
    correlation = covariance / np.outer(deviations, deviations)
    correlation = np.clip(correlation, -_CORRELATION_BOUND, _CORRELATION_BOUND)
    np.fill_diagonal(correlation, _CORRELATION_BOUND)
    return pd.DataFrame(correlation, index=validated.columns, columns=validated.columns)

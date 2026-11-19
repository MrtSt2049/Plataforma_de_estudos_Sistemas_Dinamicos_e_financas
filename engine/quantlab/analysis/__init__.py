"""Quantitative analysis of financial time series: returns, volatility, performance and risk."""

from quantlab.analysis.correlation import correlation_matrix, covariance_matrix
from quantlab.analysis.drawdown import MaxDrawdown, drawdowns, max_drawdown
from quantlab.analysis.indicators import exponential_moving_average, simple_moving_average
from quantlab.analysis.performance import periodic_rate_from_annual, sharpe_ratio
from quantlab.analysis.returns import cumulative_returns, log_returns, simple_returns
from quantlab.analysis.risk import historical_cvar, historical_var
from quantlab.analysis.volatility import (
    TRADING_DAYS_PER_YEAR,
    annualized_volatility,
    historical_volatility,
    rolling_volatility,
)

__all__ = [
    "TRADING_DAYS_PER_YEAR",
    "MaxDrawdown",
    "annualized_volatility",
    "correlation_matrix",
    "covariance_matrix",
    "cumulative_returns",
    "drawdowns",
    "exponential_moving_average",
    "historical_cvar",
    "historical_var",
    "historical_volatility",
    "log_returns",
    "max_drawdown",
    "periodic_rate_from_annual",
    "rolling_volatility",
    "sharpe_ratio",
    "simple_moving_average",
    "simple_returns",
]

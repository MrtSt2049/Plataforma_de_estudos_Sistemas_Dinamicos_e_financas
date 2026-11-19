"""Charts in the QuantLab visual identity, built with Plotly: finance and dynamical systems.

Requires the optional ``plot`` extra: ``uv sync --extra plot`` or
``pip install "quantlab[plot]"``. The numerical core does not depend on it.
"""

try:
    import plotly  # noqa: F401
except ImportError as error:  # pragma: no cover - exercised only without the extra
    raise ImportError(
        "quantlab.visualization needs Plotly. Install the 'plot' extra: "
        'uv sync --extra plot  (or  pip install "quantlab[plot]").'
    ) from error

from quantlab.visualization.dynamics import plot_logistic_bifurcation, plot_lorenz_attractor
from quantlab.visualization.finance import (
    plot_correlation_heatmap,
    plot_equity_and_drawdown,
    plot_price_history,
    plot_return_distribution,
    plot_rolling_volatility,
)
from quantlab.visualization.theme import quantlab_template

__all__ = [
    "plot_correlation_heatmap",
    "plot_equity_and_drawdown",
    "plot_logistic_bifurcation",
    "plot_lorenz_attractor",
    "plot_price_history",
    "plot_return_distribution",
    "plot_rolling_volatility",
    "quantlab_template",
]

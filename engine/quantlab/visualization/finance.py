"""Charts of financial time series for notebooks and reports.

Every chart follows the same contract (RULE 037 and the interface design system):

* the title asks the question the chart answers; the subtitle states the method;
* axes carry names and units; hover shows exact values;
* the numbers come from the engine's own functions, never recomputed here
  (RULE 003), so a chart always agrees with the analysis;
* single-series charts have no legend box (the title names the series);
* ``demo=True`` adds the DEMO DATA badge required for synthetic data.

Each function returns a :class:`plotly.graph_objects.Figure`; call ``.show()`` in a
notebook or ``.write_html(path)`` to save it. The underlying values are always
available as a table from the corresponding analysis function.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from quantlab._validation import validate_int, validate_series
from quantlab.analysis.correlation import correlation_matrix
from quantlab.analysis.drawdown import drawdowns, max_drawdown
from quantlab.analysis.risk import historical_cvar, historical_var
from quantlab.analysis.volatility import TRADING_DAYS_PER_YEAR, rolling_volatility
from quantlab.exceptions import DomainError
from quantlab.types import NumericSeries
from quantlab.visualization.theme import (
    ANALYTIC,
    AREA_OPACITY,
    BACKGROUND,
    DIVERGING_SCALE,
    LINE_WIDTH,
    MINUS,
    NEGATIVE,
    PANEL,
    TEXT,
    TEXT_SECONDARY,
    WARN,
    quantlab_template,
    with_opacity,
)

_PERCENT = 100.0
_EQUITY_BASE = 100.0
_MARKER_SIZE = 9
_DEFAULT_BINS = 50
_MIN_BINS = 5
_LIGHT_FILL_LUMINANCE = 0.35
_HISTOGRAM_BAR_GAP = 0.3
_RIGHT_HALF = 0.5
# sRGB transfer curve and WCAG luminance weights.
_SRGB_LINEAR_LIMIT = 0.04045
_SRGB_LINEAR_SLOPE = 12.92
_SRGB_OFFSET = 0.055
_SRGB_GAMMA = 2.4
_LUMA_RED, _LUMA_GREEN, _LUMA_BLUE = 0.2126, 0.7152, 0.0722
_DEMO_BADGE_BACKGROUND = "#2a2112"
_DEMO_BADGE_BORDER = "#5a4318"


# --- shared helpers ------------------------------------------------------------------------------


def _signed(value: float, decimals: int = 2, suffix: str = "%") -> str:
    """Format with an explicit sign and a typographic minus: +1.25%, −1.25%."""
    sign = "+" if value > 0 else (MINUS if value < 0 else "")
    return f"{sign}{abs(value):,.{decimals}f}{suffix}"


def _figure(question: str, context: str, *, demo: bool) -> go.Figure:
    figure = go.Figure()
    figure.update_layout(
        template=quantlab_template(),
        title={"text": question, "subtitle": {"text": context}},
        showlegend=False,
    )
    if demo:
        _add_demo_badge(figure)
    return figure


def _add_demo_badge(figure: go.Figure) -> None:
    figure.add_annotation(
        text="DEMO DATA",
        xref="paper",
        yref="paper",
        x=1.0,
        y=1.0,
        yshift=64,
        xanchor="right",
        yanchor="bottom",
        showarrow=False,
        font={"color": WARN, "size": 10.5},
        bgcolor=_DEMO_BADGE_BACKGROUND,
        bordercolor=_DEMO_BADGE_BORDER,
        borderwidth=1,
        borderpad=3,
    )


def _label_last_point(figure: go.Figure, series: pd.Series[float], text: str) -> None:
    """Direct label at the last valid point of a line (lines carry their value at the end)."""
    valid = series.dropna()
    figure.add_annotation(
        x=valid.index[-1],
        y=float(valid.iloc[-1]),
        text=text,
        showarrow=False,
        xanchor="left",
        xshift=6,
        font={"color": TEXT, "size": 11.5},
    )


def _series_label(series: pd.Series[float], fallback: str) -> str:
    return str(series.name) if series.name is not None else fallback


# --- price history -------------------------------------------------------------------------------


def plot_price_history(
    prices: NumericSeries,
    *,
    currency: str | None = None,
    question: str = "How has the price moved over the period?",
    demo: bool = False,
) -> go.Figure:
    """Line chart of a price series, showing missing observations as gaps.

    Unlike the analysis functions, this chart accepts missing values on purpose:
    seeing where data is missing is part of checking it (RULE 037). Gaps are not
    bridged, and the subtitle counts them.

    Parameters
    ----------
    prices
        Strictly positive prices (NaN allowed), sorted by a unique, increasing index.
    currency
        ISO 4217 code shown in the axis title and hover, if known.
    question
        Chart title.
    demo
        Add the DEMO DATA badge.

    Returns
    -------
    plotly.graph_objects.Figure

    Raises
    ------
    TypeError, InputValidationError, InsufficientDataError
        If ``prices`` is not a valid series (see :func:`quantlab.analysis.simple_returns`).
    DomainError
        If a non-missing price is zero or negative.
    """
    validated = validate_series(prices, name="prices", min_length=2, allow_missing=True)
    values = validated.to_numpy()
    if (values[~np.isnan(values)] <= 0.0).any():
        raise DomainError("prices must be strictly positive.")
    missing = int(np.isnan(values).sum())
    unit = f" ({currency})" if currency else ""
    label = _series_label(validated, "Price")

    context = f"{label} · {len(validated):,} observations"
    if missing:
        context += f" · {missing} missing value(s) shown as gaps"
    figure = _figure(question, context, demo=demo)
    figure.add_trace(
        go.Scatter(
            x=validated.index,
            y=validated.to_numpy(),
            mode="lines",
            name=label,
            connectgaps=False,
            line={"color": ANALYTIC, "width": LINE_WIDTH},
            hovertemplate=f"close %{{y:,.2f}}{unit}<extra></extra>",
        )
    )
    figure.update_yaxes(title_text=f"Price{unit}")
    figure.update_xaxes(title_text="Date")
    _label_last_point(figure, validated, f"{validated.dropna().iloc[-1]:,.2f}")
    return figure


# --- equity and drawdown -------------------------------------------------------------------------


def plot_equity_and_drawdown(
    prices: NumericSeries,
    *,
    question: str = "How has the asset behaved, and what was the worst stretch?",
    demo: bool = False,
) -> go.Figure:
    """Two stacked panels: equity indexed to 100 and the drawdown below it.

    The panels share the time axis but not the vertical scale, so this is not a
    dual-axis chart. The deepest point of the drawdown is marked and labelled with
    the value of :func:`quantlab.analysis.max_drawdown`.

    Parameters
    ----------
    prices
        Strictly positive prices or wealth levels with no missing values, sorted by a
        unique, increasing index.
    question
        Chart title.
    demo
        Add the DEMO DATA badge.

    Returns
    -------
    plotly.graph_objects.Figure

    Raises
    ------
    TypeError, InputValidationError, InsufficientDataError, DomainError
        As in :func:`quantlab.analysis.drawdowns`.
    """
    drawdown = drawdowns(prices)
    worst = max_drawdown(prices)
    validated = validate_series(prices, name="prices", min_length=2)
    equity = validated / validated.iloc[0] * _EQUITY_BASE
    total_return = float(equity.iloc[-1]) - _EQUITY_BASE

    label = _series_label(validated, "Asset")
    context = (
        f"{label} · base 100 · total {_signed(total_return)} · "
        f"max drawdown {_signed(worst.value * _PERCENT, 1)}"
    )
    figure = make_subplots(
        rows=2, cols=1, shared_xaxes=True, row_heights=[0.65, 0.35], vertical_spacing=0.06
    )
    figure.update_layout(
        template=quantlab_template(),
        title={"text": question, "subtitle": {"text": context}},
        showlegend=False,
    )
    if demo:
        _add_demo_badge(figure)

    figure.add_trace(
        go.Scatter(
            x=equity.index,
            y=equity.to_numpy(),
            mode="lines",
            name="Equity",
            line={"color": ANALYTIC, "width": LINE_WIDTH},
            hovertemplate="equity %{y:,.1f}<extra></extra>",
        ),
        row=1,
        col=1,
    )
    figure.add_trace(
        go.Scatter(
            x=drawdown.index,
            y=drawdown.to_numpy() * _PERCENT,
            mode="lines",
            name="Drawdown",
            fill="tozeroy",
            fillcolor=with_opacity(NEGATIVE, AREA_OPACITY),
            line={"color": NEGATIVE, "width": LINE_WIDTH},
            hovertemplate="drawdown %{y:.2f}%<extra></extra>",
        ),
        row=2,
        col=1,
    )
    if worst.trough is not None:
        trough_value = worst.value * _PERCENT
        figure.add_trace(
            go.Scatter(
                x=[worst.trough],
                y=[trough_value],
                mode="markers",
                name="Max drawdown",
                marker={
                    "color": NEGATIVE,
                    "size": _MARKER_SIZE,
                    "line": {"color": PANEL, "width": 2},
                },
                hovertemplate="max drawdown %{y:.2f}%<extra></extra>",
            ),
            row=2,
            col=1,
        )
        # Anchor the label on the side with room, so it never runs off the plot.
        # max_drawdown reports the first minimum, which is exactly argmin's position.
        position = int(np.argmin(drawdown.to_numpy())) / max(len(drawdown) - 1, 1)
        figure.add_annotation(
            x=worst.trough,
            y=trough_value,
            text=f"Max drawdown {_signed(trough_value, 1)}",
            showarrow=False,
            xanchor="right" if position > _RIGHT_HALF else "left",
            yanchor="top",
            yshift=-8,
            font={"color": TEXT, "size": 11.5},
            row=2,
            col=1,
        )
    figure.update_yaxes(title_text="Equity (base 100)", row=1, col=1)
    figure.update_yaxes(title_text="Drawdown (%)", row=2, col=1)
    figure.update_xaxes(title_text="Date", row=2, col=1)
    return figure


# --- return distribution with VaR and CVaR -------------------------------------------------------


def plot_return_distribution(
    returns: NumericSeries,
    *,
    confidence: float = 0.95,
    bins: int = _DEFAULT_BINS,
    question: str = "How large are the bad days?",
    demo: bool = False,
) -> go.Figure:
    """Histogram of returns with the historical VaR and CVaR thresholds marked.

    The thresholds are drawn at ``-VaR`` and ``-CVaR`` on the return axis and
    labelled directly; their values come from :func:`quantlab.analysis.historical_var`
    and :func:`quantlab.analysis.historical_cvar`.

    Parameters
    ----------
    returns
        Simple returns of one period (same requirements as the VaR functions).
    confidence
        Confidence level of VaR and CVaR, strictly between 0 and 1.
    bins
        Approximate number of histogram bars, ``>= 5``.
    question
        Chart title.
    demo
        Add the DEMO DATA badge.

    Returns
    -------
    plotly.graph_objects.Figure

    Raises
    ------
    TypeError, InputValidationError, DomainError, InsufficientDataError
        As in :func:`quantlab.analysis.historical_var`, or if ``bins < 5``.
    """
    bar_count = validate_int(bins, name="bins", minimum=_MIN_BINS)
    var = historical_var(returns, confidence=confidence)
    cvar = historical_cvar(returns, confidence=confidence)
    validated = validate_series(returns, name="returns", min_length=2)
    level = f"{confidence * _PERCENT:g}%"

    context = (
        f"{_series_label(validated, 'Returns')} · {len(validated):,} returns · "
        f"historical method · VaR {level} = {var * _PERCENT:.2f}% loss, "
        f"CVaR {level} = {cvar * _PERCENT:.2f}% loss"
    )
    figure = _figure(question, context, demo=demo)
    figure.add_trace(
        go.Histogram(
            x=validated.to_numpy() * _PERCENT,
            nbinsx=bar_count,
            name="Returns",
            marker={"color": ANALYTIC},
            hovertemplate="%{x} %: %{y} observation(s)<extra></extra>",
        )
    )
    for name, value, dash, shift in (("VaR", var, "dash", 0), ("CVaR", cvar, "dot", 18)):
        threshold = -value * _PERCENT
        figure.add_vline(
            x=threshold,
            line={"color": TEXT_SECONDARY, "width": 1, "dash": dash},
            annotation={
                "text": f"{name} {level}: {_signed(threshold)}",
                "font": {"color": TEXT, "size": 11.5},
                "yshift": -shift,
            },
            annotation_position="top left",
        )
    # Thin bars with air between them: a histogram of saturated touching blocks reads loud.
    figure.update_layout(hovermode="closest", bargap=_HISTOGRAM_BAR_GAP)
    figure.update_xaxes(title_text="Return per period (%)")
    figure.update_yaxes(title_text="Observations")
    return figure


# --- correlation heatmap -------------------------------------------------------------------------


def _rgb(hex_color: str) -> tuple[float, float, float]:
    red, green, blue = (
        int(hex_color[position : position + 2], 16) / 255.0 for position in (1, 3, 5)
    )
    return red, green, blue


def _scale_color(position: float) -> tuple[float, float, float]:
    """Interpolate the diverging scale linearly in RGB at ``position`` in [0, 1].

    Plotly also interpolates colour scales in RGB, so this reproduces the drawn fill.
    """
    stops = [stop for stop, _ in DIVERGING_SCALE]
    channels = list(zip(*(_rgb(color) for _, color in DIVERGING_SCALE), strict=True))
    red, green, blue = (float(np.interp(position, stops, channel)) for channel in channels)
    return red, green, blue


def _linear_channel(channel: float) -> float:
    """Undo the sRGB transfer curve (IEC 61966-2-1)."""
    if channel <= _SRGB_LINEAR_LIMIT:
        return channel / _SRGB_LINEAR_SLOPE
    return float(((channel + _SRGB_OFFSET) / (1.0 + _SRGB_OFFSET)) ** _SRGB_GAMMA)


def _relative_luminance(rgb: tuple[float, float, float]) -> float:
    """WCAG relative luminance of an sRGB colour with channels in [0, 1]."""
    red, green, blue = (_linear_channel(channel) for channel in rgb)
    return _LUMA_RED * red + _LUMA_GREEN * green + _LUMA_BLUE * blue


def plot_correlation_heatmap(
    returns: pd.DataFrame,
    *,
    question: str = "Does diversification hold?",
    demo: bool = False,
) -> go.Figure:
    """Heatmap of the Pearson correlation matrix on a fixed [-1, 1] diverging scale.

    Blue marks co-movement, amber inverse movement and neutral gray no linear
    relation, so the chart does not read as profit or loss. The scale is fixed to
    [-1, 1] so that colours are comparable across charts. Each cell is labelled with
    its value in white or near-black, whichever contrasts with the cell colour.

    Parameters
    ----------
    returns
        One column of aligned returns per asset (see
        :func:`quantlab.analysis.correlation_matrix`).
    question
        Chart title.
    demo
        Add the DEMO DATA badge.

    Returns
    -------
    plotly.graph_objects.Figure

    Raises
    ------
    TypeError, InputValidationError, InsufficientDataError, ComputationError
        As in :func:`quantlab.analysis.correlation_matrix`.
    """
    correlation = correlation_matrix(returns)
    labels = [str(column) for column in correlation.columns]
    values = correlation.to_numpy()
    context = f"Pearson · {len(returns):,} observations · blue = co-movement, amber = inverse"
    figure = _figure(question, context, demo=demo)
    figure.add_trace(
        go.Heatmap(
            z=values,
            x=labels,
            y=labels,
            zmin=-1.0,
            zmax=1.0,
            colorscale=[list(stop) for stop in DIVERGING_SCALE],
            xgap=2,
            ygap=2,
            colorbar={
                "title": {"text": "ρ", "font": {"color": TEXT_SECONDARY}},
                "tickvals": [-1, 0, 1],
                "ticktext": [f"{MINUS}1", "0", "+1"],
                "tickfont": {"color": TEXT_SECONDARY},
                "outlinewidth": 0,
            },
            hovertemplate="%{y} × %{x}: ρ = %{z:.2f}<extra></extra>",
        )
    )
    for row, row_label in enumerate(labels):
        for column, column_label in enumerate(labels):
            value = float(values[row, column])
            fill = _scale_color((value + 1.0) / 2.0)
            ink = BACKGROUND if _relative_luminance(fill) > _LIGHT_FILL_LUMINANCE else TEXT
            figure.add_annotation(
                x=column_label,
                y=row_label,
                text=f"{value:.2f}".replace("-", MINUS),
                showarrow=False,
                font={"color": ink, "size": 11.5},
            )
    figure.update_layout(hovermode="closest")
    figure.update_xaxes(showgrid=False, side="top", showspikes=False)
    figure.update_yaxes(showgrid=False, autorange="reversed", showspikes=False)
    return figure


# --- rolling volatility --------------------------------------------------------------------------


def plot_rolling_volatility(
    returns: NumericSeries,
    window: int,
    *,
    periods_per_year: float | None = TRADING_DAYS_PER_YEAR,
    question: str = "Is volatility stable, or does it change regime?",
    demo: bool = False,
) -> go.Figure:
    """Line chart of the volatility over a moving window.

    Values come from :func:`quantlab.analysis.rolling_volatility`.

    Parameters
    ----------
    returns
        Returns of one period (same requirements as the volatility functions).
    window
        Number of returns in each window.
    periods_per_year
        Annualization factor; ``None`` keeps the volatility per period.
    question
        Chart title.
    demo
        Add the DEMO DATA badge.

    Returns
    -------
    plotly.graph_objects.Figure

    Raises
    ------
    TypeError, InputValidationError, DomainError, InsufficientDataError
        As in :func:`quantlab.analysis.rolling_volatility`.
    """
    volatility = rolling_volatility(returns, window, periods_per_year=periods_per_year) * _PERCENT
    basis = "annualized" if periods_per_year is not None else "per period"
    axis_title = "Annualized volatility (%)" if periods_per_year is not None else "Volatility (%)"
    context = f"{_series_label(volatility, 'Returns')} · {window}-period window · {basis}"
    figure = _figure(question, context, demo=demo)
    figure.add_trace(
        go.Scatter(
            x=volatility.index,
            y=volatility.to_numpy(),
            mode="lines",
            name="Volatility",
            line={"color": ANALYTIC, "width": LINE_WIDTH},
            hovertemplate="σ %{y:.2f}%<extra></extra>",
        )
    )
    figure.update_yaxes(title_text=axis_title, rangemode="tozero")
    figure.update_xaxes(title_text="Date")
    _label_last_point(figure, volatility, f"{volatility.iloc[-1]:.1f}%")
    return figure

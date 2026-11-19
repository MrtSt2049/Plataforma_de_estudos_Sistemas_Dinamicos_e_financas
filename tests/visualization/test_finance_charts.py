from __future__ import annotations

import json

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest

from quantlab.analysis import (
    correlation_matrix,
    drawdowns,
    historical_cvar,
    historical_var,
    max_drawdown,
    rolling_volatility,
    simple_returns,
)
from quantlab.exceptions import DomainError, InputValidationError
from quantlab.visualization import (
    plot_correlation_heatmap,
    plot_equity_and_drawdown,
    plot_price_history,
    plot_return_distribution,
    plot_rolling_volatility,
    quantlab_template,
)
from quantlab.visualization.finance import _relative_luminance, _scale_color
from quantlab.visualization.theme import (
    ANALYTIC,
    BACKGROUND,
    DIVERGING_MIDPOINT,
    LINE_WIDTH,
    NEGATIVE,
    TEXT,
    WARN,
)


@pytest.fixture
def returns(daily_prices: pd.Series[float]) -> pd.Series[float]:
    return simple_returns(daily_prices)


@pytest.fixture
def assets(rng: np.random.Generator) -> pd.DataFrame:
    common = rng.normal(0.0, 0.01, size=300)
    return pd.DataFrame(
        {
            "A": common + rng.normal(0.0, 0.004, size=300),
            "B": -common + rng.normal(0.0, 0.004, size=300),
            "C": rng.normal(0.0, 0.01, size=300),
        },
        index=pd.bdate_range("2024-01-01", periods=300),
    )


def annotation_texts(figure: go.Figure) -> list[str]:
    return [annotation.text for annotation in figure.layout.annotations]


def all_figures(
    daily_prices: pd.Series[float], returns: pd.Series[float], assets: pd.DataFrame, demo: bool
) -> list[go.Figure]:
    return [
        plot_price_history(daily_prices, demo=demo),
        plot_equity_and_drawdown(daily_prices, demo=demo),
        plot_return_distribution(returns, demo=demo),
        plot_correlation_heatmap(assets, demo=demo),
        plot_rolling_volatility(returns, 21, demo=demo),
    ]


# --- shared contract -----------------------------------------------------------------------------


def test_every_chart_asks_a_question_and_states_its_method(
    daily_prices: pd.Series[float], returns: pd.Series[float], assets: pd.DataFrame
) -> None:
    for figure in all_figures(daily_prices, returns, assets, demo=False):
        assert figure.layout.title.text.endswith("?")
        assert figure.layout.title.subtitle.text


def test_every_trace_has_a_hover_template(
    daily_prices: pd.Series[float], returns: pd.Series[float], assets: pd.DataFrame
) -> None:
    for figure in all_figures(daily_prices, returns, assets, demo=False):
        for trace in figure.data:
            assert trace.hovertemplate


def test_single_series_charts_have_no_legend(
    daily_prices: pd.Series[float], returns: pd.Series[float], assets: pd.DataFrame
) -> None:
    for figure in all_figures(daily_prices, returns, assets, demo=False):
        assert figure.layout.showlegend is False


def test_demo_badge_only_when_requested(
    daily_prices: pd.Series[float], returns: pd.Series[float], assets: pd.DataFrame
) -> None:
    for figure in all_figures(daily_prices, returns, assets, demo=True):
        assert "DEMO DATA" in annotation_texts(figure)
    for figure in all_figures(daily_prices, returns, assets, demo=False):
        assert "DEMO DATA" not in annotation_texts(figure)


def test_figures_serialize_to_json(
    daily_prices: pd.Series[float], returns: pd.Series[float], assets: pd.DataFrame
) -> None:
    for figure in all_figures(daily_prices, returns, assets, demo=True):
        assert json.loads(figure.to_json())["data"]


def test_template_uses_solid_hairline_grids_and_text_tokens() -> None:
    layout = quantlab_template().layout
    assert layout.xaxis.griddash == "solid"
    assert layout.xaxis.gridwidth == 1
    assert layout.font.color == TEXT
    assert layout.colorway[0] == ANALYTIC


# --- price history -------------------------------------------------------------------------------


def test_price_history_shows_missing_values_as_gaps(daily_prices: pd.Series[float]) -> None:
    prices = daily_prices.copy()
    prices.iloc[10:13] = np.nan
    figure = plot_price_history(prices, currency="BRL")
    (trace,) = figure.data
    assert trace.connectgaps is False
    assert np.isnan(np.asarray(trace.y, dtype=float)).sum() == 3
    assert "3 missing value(s) shown as gaps" in figure.layout.title.subtitle.text
    assert figure.layout.yaxis.title.text == "Price (BRL)"
    assert trace.line.width == LINE_WIDTH
    assert trace.line.color == ANALYTIC


def test_price_history_labels_the_last_value(daily_prices: pd.Series[float]) -> None:
    figure = plot_price_history(daily_prices)
    assert f"{daily_prices.iloc[-1]:,.2f}" in annotation_texts(figure)


def test_price_history_rejects_non_positive_prices(daily_prices: pd.Series[float]) -> None:
    prices = daily_prices.copy()
    prices.iloc[5] = 0.0
    with pytest.raises(DomainError, match="strictly positive"):
        plot_price_history(prices)


# --- equity and drawdown -------------------------------------------------------------------------


def test_equity_and_drawdown_values_come_from_the_engine(
    daily_prices: pd.Series[float],
) -> None:
    figure = plot_equity_and_drawdown(daily_prices)
    equity, drawdown, marker = figure.data
    assert equity.y[0] == pytest.approx(100.0)
    np.testing.assert_allclose(drawdown.y, drawdowns(daily_prices).to_numpy() * 100.0)
    worst = max_drawdown(daily_prices)
    assert marker.x[0] == worst.trough
    assert marker.y[0] == pytest.approx(worst.value * 100.0)
    assert drawdown.line.color == NEGATIVE
    assert any(text.startswith("Max drawdown −") for text in annotation_texts(figure))


def test_equity_and_drawdown_are_separate_panels_not_dual_axes(
    daily_prices: pd.Series[float],
) -> None:
    figure = plot_equity_and_drawdown(daily_prices)
    assert figure.layout.yaxis.title.text == "Equity (base 100)"
    assert figure.layout.yaxis2.title.text == "Drawdown (%)"
    assert figure.layout.yaxis2.overlaying is None


def test_rising_prices_have_no_drawdown_marker() -> None:
    prices = pd.Series(
        np.linspace(100.0, 120.0, 30), index=pd.bdate_range("2025-01-01", periods=30)
    )
    figure = plot_equity_and_drawdown(prices)
    assert len(figure.data) == 2


# --- return distribution -------------------------------------------------------------------------


def test_distribution_marks_var_and_cvar_from_the_engine(returns: pd.Series[float]) -> None:
    figure = plot_return_distribution(returns, confidence=0.95)
    var = historical_var(returns, confidence=0.95)
    cvar = historical_cvar(returns, confidence=0.95)
    thresholds = sorted(shape.x0 for shape in figure.layout.shapes)
    assert thresholds == pytest.approx(sorted([-var * 100.0, -cvar * 100.0]))
    texts = annotation_texts(figure)
    assert any(text.startswith("VaR 95%: −") for text in texts)
    assert any(text.startswith("CVaR 95%: −") for text in texts)
    assert f"VaR 95% = {var * 100:.2f}% loss" in figure.layout.title.subtitle.text


def test_distribution_rejects_too_few_bins(returns: pd.Series[float]) -> None:
    with pytest.raises(InputValidationError, match="bins"):
        plot_return_distribution(returns, bins=2)


# --- correlation heatmap -------------------------------------------------------------------------


def test_heatmap_values_scale_and_labels(assets: pd.DataFrame) -> None:
    figure = plot_correlation_heatmap(assets)
    (heatmap,) = figure.data
    np.testing.assert_allclose(np.asarray(heatmap.z), correlation_matrix(assets).to_numpy())
    assert (heatmap.zmin, heatmap.zmax) == (-1.0, 1.0)
    colors = [stop[1] for stop in heatmap.colorscale]
    assert colors == [WARN, DIVERGING_MIDPOINT, ANALYTIC]
    assert len(figure.layout.annotations) == 9  # one value per cell
    assert "−1.00" not in annotation_texts(figure)  # A and B are not perfectly opposite
    assert figure.layout.yaxis.autorange == "reversed"


def test_cell_text_contrasts_with_its_fill() -> None:
    amber = _scale_color(0.0)  # correlation -1
    gray = _scale_color(0.5)  # correlation 0
    assert _relative_luminance(amber) > 0.35  # light fill: near-black text
    assert _relative_luminance(gray) < 0.35  # dark fill: light text


def test_inverse_correlation_cell_uses_dark_text() -> None:
    base = np.linspace(-0.02, 0.02, 50) ** 3
    frame = pd.DataFrame({"x": base, "y": -base})
    figure = plot_correlation_heatmap(frame)
    inks = {annotation.text: annotation.font.color for annotation in figure.layout.annotations}
    assert inks["−1.00"] == BACKGROUND
    assert inks["1.00"] == TEXT


# --- rolling volatility --------------------------------------------------------------------------


def test_rolling_volatility_values_and_units(returns: pd.Series[float]) -> None:
    figure = plot_rolling_volatility(returns, 21)
    (trace,) = figure.data
    expected = rolling_volatility(returns, 21, periods_per_year=252).to_numpy() * 100.0
    np.testing.assert_allclose(trace.y, expected)
    assert figure.layout.yaxis.title.text == "Annualized volatility (%)"


def test_rolling_volatility_per_period(returns: pd.Series[float]) -> None:
    figure = plot_rolling_volatility(returns, 21, periods_per_year=None)
    assert figure.layout.yaxis.title.text == "Volatility (%)"
    assert "per period" in figure.layout.title.subtitle.text


def test_relative_luminance_matches_wcag_reference_values() -> None:
    assert _relative_luminance((0.0, 0.0, 0.0)) == 0.0
    assert _relative_luminance((1.0, 1.0, 1.0)) == pytest.approx(1.0)
    # sRGB 0x80 gray: ((128/255 + 0.055) / 1.055) ** 2.4 = 0.21586...
    assert _relative_luminance((128 / 255,) * 3) == pytest.approx(0.21586050011389926)
    # A very dark channel lies on the linear segment of the sRGB curve: c / 12.92.
    assert _relative_luminance((0.03, 0.03, 0.03)) == pytest.approx(0.03 / 12.92)

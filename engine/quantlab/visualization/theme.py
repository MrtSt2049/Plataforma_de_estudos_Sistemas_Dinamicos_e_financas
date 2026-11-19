"""QuantLab visual tokens and the Plotly template built from them.

Values come from the interface design system (``Assets/``). Colour roles:

* ``POSITIVE`` / ``NEGATIVE``: signed change only (gain / loss), always together
  with a sign, never alone;
* ``ANALYTIC``: analysis series (prices, volatility, distributions);
* ``SCIENCE``: dynamical systems;
* ``WARN``: warnings and the DEMO badge;
* correlation and other diverging scales: ``ANALYTIC`` <-> ``WARN`` around a neutral
  gray, so the heatmap does not read as profit/loss and stays distinguishable for
  red-green colour blindness.

Checked with the dataviz palette validator on the panel surface (``#111820``):
blue/amber (diverging poles) and blue/red pass every colour-vision check; blue and
purple are indistinguishable for deuteranopes (delta E 1.3), so ``ANALYTIC`` and
``SCIENCE`` must never identify two series in the same chart.
"""

from __future__ import annotations

from typing import Final

import plotly.graph_objects as go

BACKGROUND: Final = "#0B0F14"
PANEL: Final = "#111820"
SURFACE: Final = "#17212B"
BORDER: Final = "#263442"
TEXT: Final = "#E8EDF2"
TEXT_SECONDARY: Final = "#8997A5"

POSITIVE: Final = "#16C784"
NEGATIVE: Final = "#EA3943"
ANALYTIC: Final = "#3B82F6"
SCIENCE: Final = "#8B5CF6"
WARN: Final = "#F5A623"

DIVERGING_MIDPOINT: Final = "#30343A"
"""Neutral gray (OKLCH chroma 0.012) at the centre of diverging scales.

The border token ``#263442`` is not used here: its bluish tint (chroma 0.031)
would put a hue at the midpoint, which must read as "nothing".
"""
DIVERGING_SCALE: Final[tuple[tuple[float, str], ...]] = (
    (0.0, WARN),
    (0.5, DIVERGING_MIDPOINT),
    (1.0, ANALYTIC),
)
"""Amber for -1 (inverse movement), gray for 0, blue for +1 (co-movement)."""

FONT_SANS: Final = "Inter, system-ui, sans-serif"
FONT_MONO: Final = "IBM Plex Mono, JetBrains Mono, monospace"

LINE_WIDTH: Final = 2
"""Data lines are 2 px."""
AREA_OPACITY: Final = 0.10
"""Area fills are a wash of the series colour, never a saturated block."""
GRID_WIDTH: Final = 1
MINUS: Final = "−"
"""Typographic minus sign used in labels."""


def with_opacity(hex_color: str, opacity: float) -> str:
    """Return ``hex_color`` (``#RRGGBB``) as an ``rgba(...)`` string with ``opacity``."""
    red, green, blue = (int(hex_color[position : position + 2], 16) for position in (1, 3, 5))
    return f"rgba({red}, {green}, {blue}, {opacity})"


def _axis() -> dict[str, object]:
    return {
        "gridcolor": BORDER,
        "gridwidth": GRID_WIDTH,
        "griddash": "solid",
        "linecolor": BORDER,
        "zerolinecolor": BORDER,
        "tickfont": {"family": FONT_MONO, "color": TEXT_SECONDARY, "size": 11},
        "title": {"font": {"family": FONT_SANS, "color": TEXT_SECONDARY, "size": 11}},
        "showspikes": True,
        "spikecolor": TEXT_SECONDARY,
        "spikethickness": 1,
        "spikedash": "solid",
        "spikemode": "across",
    }


def quantlab_template() -> go.layout.Template:
    """Build the dark Plotly template of the QuantLab interface.

    Hairline solid grids one step off the surface, text in the text tokens, the
    interface fonts, a unified hover crosshair, and the analytic colour as the
    first series colour.
    """
    return go.layout.Template(
        layout={
            "paper_bgcolor": PANEL,
            "plot_bgcolor": PANEL,
            "font": {"family": FONT_SANS, "color": TEXT, "size": 12.5},
            "title": {
                "font": {"family": FONT_SANS, "color": TEXT, "size": 15},
                "xref": "container",
                "x": 0.0,
                "xanchor": "left",
                "pad": {"l": 16},
                "subtitle": {"font": {"family": FONT_SANS, "color": TEXT_SECONDARY, "size": 12}},
            },
            "colorway": [ANALYTIC],
            "xaxis": _axis(),
            "yaxis": _axis(),
            "hovermode": "x unified",
            "hoverlabel": {
                "bgcolor": SURFACE,
                "bordercolor": BORDER,
                "font": {"family": FONT_MONO, "color": TEXT, "size": 12},
            },
            "legend": {"font": {"color": TEXT_SECONDARY}, "bgcolor": "rgba(0,0,0,0)"},
            "margin": {"l": 64, "r": 32, "t": 96, "b": 56},
        }
    )

"""Layout helpers shared by every chart module (private).

They implement the parts of the chart contract that do not depend on the data:
the question as title, the method as subtitle, no legend box, and the DEMO DATA
badge for synthetic data.
"""

from __future__ import annotations

import plotly.graph_objects as go

from quantlab.visualization.theme import WARN, quantlab_template

_DEMO_BADGE_BACKGROUND = "#2a2112"
_DEMO_BADGE_BORDER = "#5a4318"


def titled_figure(question: str, context: str, *, demo: bool) -> go.Figure:
    """Return an empty themed figure titled with ``question`` and subtitled ``context``."""
    figure = go.Figure()
    figure.update_layout(
        template=quantlab_template(),
        title={"text": question, "subtitle": {"text": context}},
        showlegend=False,
    )
    if demo:
        add_demo_badge(figure)
    return figure


def add_demo_badge(figure: go.Figure) -> None:
    """Add the DEMO DATA badge to the top-right corner of ``figure``."""
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

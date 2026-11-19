"""Charts of dynamical systems: the Lorenz attractor and the logistic bifurcation diagram.

The charts follow the same contract as :mod:`quantlab.visualization.finance`: the
title asks a question, the subtitle states the method and its settings, axes are
named, every trace has hover, and the values come from the engine
(:func:`~quantlab.dynamics.simulate_lorenz`,
:func:`~quantlab.dynamics.lorenz_fixed_points`,
:func:`~quantlab.dynamics.logistic_bifurcation_diagram`) without being recomputed.

Series use the scientific colour ``SCIENCE``. ``ANALYTIC`` is never used next to it
in the same chart: the two are indistinguishable for deuteranopes (ADR 0003).
"""

from __future__ import annotations

import math
from typing import Final

import numpy as np
import numpy.typing as npt
import plotly.graph_objects as go

from quantlab._validation import validate_finite_real
from quantlab.dynamics.integration import Trajectory
from quantlab.dynamics.logistic import logistic_bifurcation_diagram
from quantlab.dynamics.lorenz import STATE_DIMENSION, LorenzParameters, lorenz_fixed_points
from quantlab.exceptions import InputValidationError, InsufficientDataError
from quantlab.visualization._layout import titled_figure
from quantlab.visualization.theme import (
    LINE_WIDTH,
    MINUS,
    PANEL,
    SCIENCE,
    TEXT,
    TEXT_SECONDARY,
)

_MIN_PLOTTED_POINTS: Final = 2
_EQUILIBRIUM_MARKER_SIZE: Final = 5
_BIFURCATION_MARKER_SIZE: Final = 2
_BIFURCATION_MARKER_OPACITY: Final = 0.35
"""Overlapping translucent points make the density of the chaotic bands visible."""
_EQUILIBRIUM_NAMES: Final = ("O", "C+", f"C{MINUS}")
_LORENZ_CAMERA_EYE: Final = {"x": 1.15, "y": -2.2, "z": 0.55}

_LOGISTIC_LANDMARKS: Final[tuple[tuple[float, str], ...]] = (
    (3.0, "period 2"),
    (1.0 + math.sqrt(6.0), "period 4"),
    (1.0 + math.sqrt(8.0), "period-3 window"),
)
"""Exact bifurcation values: the first two period doublings and the period-3 saddle-node."""


# --- Lorenz attractor ----------------------------------------------------------------------------


def _format_parameters(parameters: LorenzParameters) -> str:
    return f"σ = {parameters.sigma:g}, ρ = {parameters.rho:g}, β = {parameters.beta:.4g}"


def plot_lorenz_attractor(
    trajectory: Trajectory,
    *,
    parameters: LorenzParameters | None = None,
    transient_time: float = 0.0,
    question: str = "Where does the Lorenz flow spend its time?",
    demo: bool = False,
) -> go.Figure:
    """Draw a Lorenz trajectory in three dimensions, with the equilibria marked.

    The trajectory is drawn as computed by :func:`~quantlab.dynamics.simulate_lorenz`;
    nothing is integrated here. If ``parameters`` is given, the subtitle names them
    and the equilibria returned by :func:`~quantlab.dynamics.lorenz_fixed_points`
    are marked and labelled with their stability.

    Parameters
    ----------
    trajectory
        A three-dimensional trajectory.
    parameters
        The parameters the trajectory was computed with, if known. They must match:
        this function cannot check it.
    transient_time
        Points with ``time < transient_time`` are left out, so the chart shows the
        attractor rather than the approach to it. ``>= 0``.
    question
        Chart title.
    demo
        Add the DEMO DATA badge.

    Returns
    -------
    plotly.graph_objects.Figure

    Raises
    ------
    TypeError
        If ``trajectory`` is not a :class:`~quantlab.dynamics.Trajectory`,
        ``parameters`` is neither ``None`` nor :class:`~quantlab.dynamics.LorenzParameters`,
        or ``transient_time`` is not a real number.
    InputValidationError
        If the trajectory is not three-dimensional, or ``transient_time`` is
        negative or not finite.
    InsufficientDataError
        If fewer than two points remain after discarding the transient.
    """
    if not isinstance(trajectory, Trajectory):
        raise TypeError(f"trajectory must be a Trajectory, got {type(trajectory).__name__}.")
    if parameters is not None and not isinstance(parameters, LorenzParameters):
        raise TypeError(
            f"parameters must be LorenzParameters or None, got {type(parameters).__name__}."
        )
    if trajectory.states.shape[1] != STATE_DIMENSION:
        raise InputValidationError(
            f"trajectory must be three-dimensional, got {trajectory.states.shape[1]} dimension(s)."
        )
    cutoff = validate_finite_real(transient_time, name="transient_time")
    if cutoff < 0.0:
        raise InputValidationError(f"transient_time must be non-negative, got {cutoff}.")
    kept = trajectory.times >= cutoff
    if int(kept.sum()) < _MIN_PLOTTED_POINTS:
        raise InsufficientDataError(
            f"Fewer than {_MIN_PLOTTED_POINTS} points remain after discarding "
            f"t < {cutoff:g}; the trajectory ends at t = {trajectory.times[-1]:g}."
        )
    times = trajectory.times[kept]
    states = trajectory.states[kept]

    context = (
        f"{trajectory.method}, rtol {trajectory.rtol:.0e} · t from {times[0]:g} to "
        f"{times[-1]:g} · {times.size:,} points · dimensionless variables"
    )
    if cutoff > 0.0:
        context += f" · transient t < {cutoff:g} discarded"
    if parameters is not None:
        context = f"{_format_parameters(parameters)} · {context}"

    figure = titled_figure(question, context, demo=demo)
    figure.add_trace(
        go.Scatter3d(
            x=states[:, 0],
            y=states[:, 1],
            z=states[:, 2],
            mode="lines",
            name="Trajectory",
            line={"color": SCIENCE, "width": LINE_WIDTH},
            customdata=times,
            hovertemplate=(
                "t %{customdata:.2f}<br>x %{x:.3f}<br>y %{y:.3f}<br>z %{z:.3f}<extra></extra>"
            ),
        )
    )
    if parameters is not None:
        _add_equilibria(figure, parameters)
    figure.update_layout(
        hovermode="closest",
        scene={
            "xaxis": {"title": {"text": "x (dimensionless)"}},
            "yaxis": {"title": {"text": "y (dimensionless)"}},
            "zaxis": {"title": {"text": "z (dimensionless)"}},
            "aspectmode": "data",
            # Seen from the -y side, slightly above: the classic view in which both
            # wings and the equilibria C+ and C- at their centres are visible.
            "camera": {"eye": _LORENZ_CAMERA_EYE},
        },
    )
    return figure


def _add_equilibria(figure: go.Figure, parameters: LorenzParameters) -> None:
    equilibria = lorenz_fixed_points(parameters)
    names = _EQUILIBRIUM_NAMES[: len(equilibria)]
    locations = np.array([equilibrium.location for equilibrium in equilibria])
    figure.add_trace(
        go.Scatter3d(
            x=locations[:, 0],
            y=locations[:, 1],
            z=locations[:, 2],
            mode="markers+text",
            name="Equilibria",
            text=list(names),
            textposition="top center",
            textfont={"color": TEXT_SECONDARY, "size": 11},
            marker={
                "color": TEXT,
                "size": _EQUILIBRIUM_MARKER_SIZE,
                "symbol": "diamond",
                "line": {"color": PANEL, "width": 1},
            },
            customdata=[equilibrium.stability.value for equilibrium in equilibria],
            hovertemplate=(
                "%{text}: (%{x:.2f}, %{y:.2f}, %{z:.2f})<br>%{customdata}<extra></extra>"
            ),
        )
    )


# --- logistic bifurcation diagram ----------------------------------------------------------------


def plot_logistic_bifurcation(
    r_values: npt.ArrayLike,
    x0: float,
    *,
    n_transient: int = 1_000,
    n_samples: int = 200,
    question: str = "How does the long-run behaviour of the logistic map change with r?",
    demo: bool = False,
) -> go.Figure:
    """Bifurcation diagram of the logistic map: long-run states against ``r``.

    The samples come from :func:`~quantlab.dynamics.logistic_bifurcation_diagram`.
    Points are small and translucent, so the density of the chaotic bands shows.
    Dotted lines mark the exact bifurcation values inside the plotted range:
    ``r = 3`` (period 2), ``1 + sqrt(6)`` (period 4) and ``1 + sqrt(8)`` (the
    period-3 window).

    Parameters
    ----------
    r_values
        Growth parameters, each in ``[0, 4]``.
    x0
        Initial state shared by every ``r``, in ``[0, 1]``.
    n_transient
        Iterations discarded before sampling, ``>= 0``.
    n_samples
        States plotted per value of ``r``, ``>= 1``.
    question
        Chart title.
    demo
        Add the DEMO DATA badge.

    Returns
    -------
    plotly.graph_objects.Figure

    Raises
    ------
    TypeError, InputValidationError, DomainError
        As in :func:`~quantlab.dynamics.logistic_bifurcation_diagram`.
    """
    diagram = logistic_bifurcation_diagram(
        r_values, x0, n_transient=n_transient, n_samples=n_samples
    )
    growth = np.asarray(r_values, dtype=np.float64)
    low, high = float(growth.min()), float(growth.max())
    context = (
        f"{growth.size:,} values of r in [{low:g}, {high:g}] · x0 = {x0:g} · "
        f"first {n_transient:,} iterations discarded, next {n_samples:,} plotted"
    )
    figure = titled_figure(question, context, demo=demo)
    figure.add_trace(
        go.Scattergl(
            x=np.repeat(growth, diagram.shape[1]),
            y=diagram.ravel(),
            mode="markers",
            name="Long-run states",
            marker={
                "color": SCIENCE,
                "size": _BIFURCATION_MARKER_SIZE,
                "opacity": _BIFURCATION_MARKER_OPACITY,
            },
            hovertemplate="r %{x:.4f}<br>x %{y:.4f}<extra></extra>",
        )
    )
    for value, label in _LOGISTIC_LANDMARKS:
        if low <= value <= high:
            figure.add_vline(
                x=value,
                line={"color": TEXT_SECONDARY, "width": 1, "dash": "dot"},
                annotation={"text": label, "font": {"color": TEXT, "size": 11}},
                annotation_position="top left",
            )
    figure.update_layout(hovermode="closest")
    figure.update_xaxes(title_text="Growth parameter r (dimensionless)")
    figure.update_yaxes(title_text="Long-run state x (dimensionless)", range=[0.0, 1.0])
    return figure

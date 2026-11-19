"""Charts of dynamical systems: contract, values taken from the engine, validation."""

from __future__ import annotations

import json
import math

import numpy as np
import plotly.graph_objects as go
import pytest

from quantlab.dynamics import (
    CANONICAL_PARAMETERS,
    LorenzParameters,
    Trajectory,
    logistic_bifurcation_diagram,
    lorenz_fixed_points,
    simulate_lorenz,
)
from quantlab.dynamics.integration import integrate_autonomous
from quantlab.exceptions import DomainError, InputValidationError, InsufficientDataError
from quantlab.visualization import (
    plot_logistic_bifurcation,
    plot_lorenz_attractor,
    quantlab_template,
)
from quantlab.visualization.theme import ANALYTIC, LINE_WIDTH, PANEL, SCIENCE

R_GRID = np.linspace(2.8, 4.0, 60)


@pytest.fixture(scope="module")
def trajectory() -> Trajectory:
    return simulate_lorenz([1.0, 1.0, 1.0], n_steps=1_000, dt=0.01)


def annotation_texts(figure: go.Figure) -> list[str]:
    return [annotation.text for annotation in figure.layout.annotations]


def all_figures(trajectory: Trajectory, demo: bool) -> list[go.Figure]:
    return [
        plot_lorenz_attractor(trajectory, demo=demo),
        plot_lorenz_attractor(trajectory, parameters=CANONICAL_PARAMETERS, demo=demo),
        plot_logistic_bifurcation(R_GRID, 0.2, n_transient=200, n_samples=20, demo=demo),
    ]


# --- shared contract -----------------------------------------------------------------------------


def test_every_chart_asks_a_question_and_states_its_method(trajectory: Trajectory) -> None:
    for figure in all_figures(trajectory, demo=False):
        assert figure.layout.title.text.endswith("?")
        assert figure.layout.title.subtitle.text


def test_every_trace_has_hover_and_uses_the_scientific_colour(trajectory: Trajectory) -> None:
    for figure in all_figures(trajectory, demo=False):
        assert figure.layout.showlegend is False
        for trace in figure.data:
            assert trace.hovertemplate
        colours = {trace.line.color for trace in figure.data if trace.mode == "lines"}
        colours |= {trace.marker.color for trace in figure.data if trace.mode == "markers"}
        assert SCIENCE in colours
        assert ANALYTIC not in colours  # indistinguishable from SCIENCE for deuteranopes


def test_demo_badge_only_when_requested(trajectory: Trajectory) -> None:
    for figure in all_figures(trajectory, demo=True):
        assert "DEMO DATA" in annotation_texts(figure)
    for figure in all_figures(trajectory, demo=False):
        assert "DEMO DATA" not in annotation_texts(figure)


def test_figures_serialize_to_json(trajectory: Trajectory) -> None:
    for figure in all_figures(trajectory, demo=True):
        assert json.loads(figure.to_json())["data"]


def test_template_styles_3d_scenes_with_the_panel_and_border_tokens() -> None:
    scene = quantlab_template().layout.scene
    assert scene.bgcolor == PANEL
    for axis in (scene.xaxis, scene.yaxis, scene.zaxis):
        assert axis.backgroundcolor == PANEL
        assert axis.showspikes is False


# --- Lorenz attractor ----------------------------------------------------------------------------


def test_lorenz_draws_the_trajectory_exactly(trajectory: Trajectory) -> None:
    figure = plot_lorenz_attractor(trajectory)
    (line,) = figure.data
    assert isinstance(line, go.Scatter3d)
    np.testing.assert_array_equal(line.x, trajectory.states[:, 0])
    np.testing.assert_array_equal(line.y, trajectory.states[:, 1])
    np.testing.assert_array_equal(line.z, trajectory.states[:, 2])
    np.testing.assert_array_equal(line.customdata, trajectory.times)
    assert line.line.width == LINE_WIDTH


def test_lorenz_axes_are_named_with_units(trajectory: Trajectory) -> None:
    scene = plot_lorenz_attractor(trajectory).layout.scene
    assert scene.xaxis.title.text == "x (dimensionless)"
    assert scene.yaxis.title.text == "y (dimensionless)"
    assert scene.zaxis.title.text == "z (dimensionless)"
    assert scene.aspectmode == "data"


def test_lorenz_subtitle_records_the_solver_settings(trajectory: Trajectory) -> None:
    subtitle = plot_lorenz_attractor(trajectory).layout.title.subtitle.text
    assert "DOP853, rtol 1e-10" in subtitle
    assert "t from 0 to 10" in subtitle
    assert "1,001 points" in subtitle
    assert "σ" not in subtitle  # parameters unknown, so not claimed


def test_lorenz_with_parameters_names_them_and_marks_the_equilibria(
    trajectory: Trajectory,
) -> None:
    figure = plot_lorenz_attractor(trajectory, parameters=CANONICAL_PARAMETERS)
    assert figure.layout.title.subtitle.text.startswith("σ = 10, ρ = 28, β = 2.667 · ")
    _, markers = figure.data
    expected = lorenz_fixed_points(CANONICAL_PARAMETERS)
    np.testing.assert_array_equal(markers.x, [e.location[0] for e in expected])
    np.testing.assert_array_equal(markers.z, [e.location[2] for e in expected])
    assert list(markers.text) == ["O", "C+", "C−"]
    assert list(markers.customdata) == ["unstable", "unstable", "unstable"]


def test_lorenz_below_the_pitchfork_marks_only_the_origin() -> None:
    parameters = LorenzParameters(rho=0.5)
    decaying = simulate_lorenz([1.0, 1.0, 1.0], n_steps=50, dt=0.1, parameters=parameters)
    _, markers = plot_lorenz_attractor(decaying, parameters=parameters).data
    assert list(markers.text) == ["O"]
    assert list(markers.customdata) == ["stable"]


def test_lorenz_transient_is_discarded(trajectory: Trajectory) -> None:
    figure = plot_lorenz_attractor(trajectory, transient_time=2.5)
    (line,) = figure.data
    kept = trajectory.times >= 2.5
    np.testing.assert_array_equal(line.x, trajectory.states[kept, 0])
    np.testing.assert_array_equal(line.customdata, trajectory.times[kept])
    assert "transient t < 2.5 discarded" in figure.layout.title.subtitle.text


def test_lorenz_rejects_a_transient_that_leaves_too_few_points(trajectory: Trajectory) -> None:
    with pytest.raises(InsufficientDataError, match="t = 10"):
        plot_lorenz_attractor(trajectory, transient_time=10.0)


@pytest.mark.parametrize("transient_time", [-1.0, math.nan])
def test_lorenz_rejects_invalid_transient(trajectory: Trajectory, transient_time: float) -> None:
    with pytest.raises(InputValidationError, match="transient_time"):
        plot_lorenz_attractor(trajectory, transient_time=transient_time)


def test_lorenz_rejects_wrong_types_and_dimensions(trajectory: Trajectory) -> None:
    with pytest.raises(TypeError, match="Trajectory"):
        plot_lorenz_attractor(trajectory.states)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="LorenzParameters"):
        plot_lorenz_attractor(trajectory, parameters=(10.0, 28.0, 8.0 / 3.0))  # type: ignore[arg-type]
    planar = integrate_autonomous(lambda state: -state, [1.0, 2.0], n_steps=5, dt=0.1)
    with pytest.raises(InputValidationError, match="three-dimensional"):
        plot_lorenz_attractor(planar)


# --- logistic bifurcation diagram ----------------------------------------------------------------


def test_bifurcation_points_are_the_engine_samples() -> None:
    figure = plot_logistic_bifurcation(R_GRID, 0.2, n_transient=200, n_samples=20)
    (points,) = figure.data
    assert isinstance(points, go.Scattergl)
    diagram = logistic_bifurcation_diagram(R_GRID, 0.2, n_transient=200, n_samples=20)
    np.testing.assert_array_equal(points.x, np.repeat(R_GRID, 20))
    np.testing.assert_array_equal(points.y, diagram.ravel())


def test_bifurcation_axes_and_subtitle() -> None:
    figure = plot_logistic_bifurcation(R_GRID, 0.2, n_transient=200, n_samples=20)
    assert figure.layout.xaxis.title.text == "Growth parameter r (dimensionless)"
    assert figure.layout.yaxis.title.text == "Long-run state x (dimensionless)"
    assert tuple(figure.layout.yaxis.range) == (0.0, 1.0)
    subtitle = figure.layout.title.subtitle.text
    assert subtitle == (
        "60 values of r in [2.8, 4] · x0 = 0.2 · first 200 iterations discarded, next 20 plotted"
    )


def test_bifurcation_marks_only_the_landmarks_inside_the_range() -> None:
    full = plot_logistic_bifurcation(R_GRID, 0.2, n_transient=10, n_samples=2)
    assert {"period 2", "period 4", "period-3 window"} <= set(annotation_texts(full))
    lines = [shape.x0 for shape in full.layout.shapes]
    assert lines == pytest.approx([3.0, 1.0 + math.sqrt(6.0), 1.0 + math.sqrt(8.0)])

    narrow = plot_logistic_bifurcation(np.linspace(3.6, 3.7, 5), 0.2, n_transient=10, n_samples=2)
    assert not narrow.layout.shapes


def test_bifurcation_validation_comes_from_the_engine() -> None:
    with pytest.raises(DomainError, match="r_values"):
        plot_logistic_bifurcation([3.0, 4.5], 0.2)
    with pytest.raises(DomainError, match="x0"):
        plot_logistic_bifurcation([3.0], -0.1)

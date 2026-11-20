from __future__ import annotations

import dataclasses
import datetime as dt
import json
import time
from collections.abc import Mapping

import numpy as np
import pandas as pd
import pytest

import quantlab
from quantlab.dynamics import detect_period, simulate_logistic_map
from quantlab.exceptions import InputValidationError
from quantlab.research import (
    MAX_SEED,
    Experiment,
    ExperimentRun,
    JsonValue,
    SeedManager,
    capture_environment,
    hash_data,
    run_experiment,
)

HASH = "a" * 64
FIXED_TIME = dt.datetime(2026, 11, 20, 12, 0, tzinfo=dt.UTC)


def make_experiment(**overrides: object) -> Experiment:
    fields: dict[str, object] = {
        "name": "logistic map, period doubling",
        "hypothesis": "The orbit has period 4 at r = 3.5 for any initial condition.",
        "model": "logistic_map",
        "parameters": {"r": 3.5, "n_steps": 2_000},
        "seed": 7,
        "created_at": FIXED_TIME,
    }
    fields.update(overrides)
    return Experiment(**fields)  # type: ignore[arg-type]


def make_run(experiment: Experiment | None = None, **overrides: object) -> ExperimentRun:
    fields: dict[str, object] = {
        "experiment": experiment or make_experiment(),
        "metrics": {"period": 4.0, "mean": 0.5},
        "environment": {"python": "3.13.0"},
        "started_at": FIXED_TIME,
        "execution_time_ms": 12.5,
    }
    fields.update(overrides)
    return ExperimentRun(**fields)  # type: ignore[arg-type]


# --- Experiment: construction ----------------------------------------------------------


def test_experiment_records_its_definition() -> None:
    experiment = make_experiment(data_hash=HASH, engine_version="9.9.9")
    assert experiment.name == "logistic map, period doubling"
    assert experiment.model == "logistic_map"
    assert experiment.seed == 7
    assert experiment.data_hash == HASH
    assert experiment.engine_version == "9.9.9"
    assert experiment.created_at == FIXED_TIME
    assert experiment.parameters == {"r": 3.5, "n_steps": 2_000}


def test_defaults_are_the_running_engine_and_now() -> None:
    before = dt.datetime.now(dt.UTC)
    experiment = Experiment(name="n", hypothesis="h", model="m", parameters={}, seed=0)
    after = dt.datetime.now(dt.UTC)
    assert experiment.engine_version == quantlab.__version__
    assert experiment.data_hash is None
    assert before <= experiment.created_at <= after
    assert experiment.created_at.utcoffset() == dt.timedelta(0)


def test_texts_are_stripped() -> None:
    experiment = make_experiment(name="  title  ", hypothesis="\tclaim\n", model=" m ")
    assert (experiment.name, experiment.hypothesis, experiment.model) == ("title", "claim", "m")


def test_created_at_is_stored_in_utc() -> None:
    brasilia = dt.timezone(dt.timedelta(hours=-3))
    experiment = make_experiment(created_at=dt.datetime(2026, 11, 20, 9, 0, tzinfo=brasilia))
    assert experiment.created_at == FIXED_TIME
    assert experiment.created_at.utcoffset() == dt.timedelta(0)


@pytest.mark.parametrize("field", ["name", "hypothesis", "model", "engine_version"])
@pytest.mark.parametrize("value", ["", "   "])
def test_texts_must_not_be_empty(field: str, value: str) -> None:
    with pytest.raises(InputValidationError, match=field):
        make_experiment(**{field: value})


@pytest.mark.parametrize("field", ["name", "hypothesis", "model", "engine_version"])
def test_texts_must_be_strings(field: str) -> None:
    with pytest.raises(TypeError, match=field):
        make_experiment(**{field: 3})


@pytest.mark.parametrize("seed", [-1, MAX_SEED + 1])
def test_seed_range(seed: int) -> None:
    with pytest.raises(InputValidationError, match="seed"):
        make_experiment(seed=seed)


@pytest.mark.parametrize("seed", [1.5, True, "7", None])
def test_seed_must_be_an_integer(seed: object) -> None:
    with pytest.raises(TypeError, match="seed"):
        make_experiment(seed=seed)


def test_extreme_valid_seeds() -> None:
    assert make_experiment(seed=0).seed == 0
    assert make_experiment(seed=MAX_SEED).seed == MAX_SEED
    assert make_experiment(seed=np.int64(5)).seed == 5


@pytest.mark.parametrize("data_hash", ["abc", "A" * 64, "g" * 64, "a" * 63, "a" * 65, ""])
def test_data_hash_must_be_a_lowercase_sha256_digest(data_hash: str) -> None:
    with pytest.raises(InputValidationError, match="data_hash"):
        make_experiment(data_hash=data_hash)


def test_data_hash_must_be_a_string() -> None:
    with pytest.raises(TypeError, match="data_hash"):
        make_experiment(data_hash=123)


def test_created_at_must_be_a_timezone_aware_datetime() -> None:
    with pytest.raises(InputValidationError, match="timezone-aware"):
        make_experiment(created_at=dt.datetime(2026, 11, 20, 12, 0))
    with pytest.raises(TypeError, match="created_at"):
        make_experiment(created_at="2026-11-20")


# --- Experiment: parameters ------------------------------------------------------------


def test_parameters_are_copied_and_deeply_read_only() -> None:
    source: dict[str, JsonValue] = {"grid": [1.0, 2.0], "nested": {"a": [1, {"b": 2}]}}
    experiment = make_experiment(parameters=source)
    source["grid"] = [9.0]
    source["nested"] = {}  # changing the caller's dict must not change the experiment
    assert experiment.parameters == {"grid": (1.0, 2.0), "nested": {"a": (1, {"b": 2})}}
    with pytest.raises(TypeError):
        experiment.parameters["grid"] = (0.0,)  # type: ignore[index]
    nested = experiment.parameters["nested"]
    assert isinstance(nested, Mapping)
    with pytest.raises(TypeError):
        nested["a"] = 1  # type: ignore[index]
    grid = experiment.parameters["grid"]
    assert isinstance(grid, tuple)
    with pytest.raises(AttributeError):
        grid.append(3.0)  # type: ignore[attr-defined]


def test_the_experiment_itself_is_frozen() -> None:
    experiment = make_experiment()
    with pytest.raises(dataclasses.FrozenInstanceError):
        experiment.seed = 8  # type: ignore[misc]


def test_numpy_values_become_python_values() -> None:
    experiment = make_experiment(
        parameters={
            "r": np.float64(3.5),
            "n": np.int64(10),
            "flag": np.bool_(True),
            "x0": np.array([0.1, 0.2]),
            "grid": np.array([[1, 2], [3, 4]]),
            "tuple": (1, 2),
        }
    )
    assert experiment.parameters == {
        "r": 3.5,
        "n": 10,
        "flag": True,
        "x0": (0.1, 0.2),
        "grid": ((1, 2), (3, 4)),
        "tuple": (1, 2),
    }
    json.dumps(experiment.to_dict())  # would raise on a NumPy type


def test_empty_parameters_are_allowed() -> None:
    assert make_experiment(parameters={}).parameters == {}


@pytest.mark.parametrize(
    ("parameters", "path"),
    [
        ({"x": float("nan")}, "parameters.x"),
        ({"x": float("inf")}, "parameters.x"),
        ({"a": {"b": [1.0, float("-inf")]}}, r"parameters.a.b\[1\]"),
        ({"x": np.float64("nan")}, "parameters.x"),
    ],
)
def test_parameters_must_be_finite(parameters: dict[str, object], path: str) -> None:
    with pytest.raises(InputValidationError, match=f"{path} must be finite"):
        make_experiment(parameters=parameters)


@pytest.mark.parametrize(
    ("parameters", "path"),
    [
        ({"x": {1, 2}}, "parameters.x"),
        ({"x": b"bytes"}, "parameters.x"),
        ({"x": object()}, "parameters.x"),
        ({"x": 1 + 2j}, "parameters.x"),
        ({"a": [1, {2, 3}]}, r"parameters.a\[1\]"),
        ({"x": pd.Series([1.0])}, "parameters.x"),
    ],
)
def test_parameters_must_be_json_compatible(parameters: dict[str, object], path: str) -> None:
    with pytest.raises(TypeError, match=f"{path} has the unsupported type"):
        make_experiment(parameters=parameters)


def test_parameter_keys_must_be_strings() -> None:
    with pytest.raises(TypeError, match="use str"):
        make_experiment(parameters={1: "a"})


def test_parameters_must_be_a_mapping() -> None:
    with pytest.raises(TypeError, match="parameters must be a mapping"):
        make_experiment(parameters=[("r", 3.5)])


# --- Experiment: serialization ---------------------------------------------------------


def test_experiment_round_trips_through_json() -> None:
    experiment = make_experiment(
        data_hash=HASH, parameters={"r": 3.5, "grid": [1, 2], "meta": {"a": None, "b": True}}
    )
    text = json.dumps(experiment.to_dict())
    assert Experiment.from_dict(json.loads(text)) == experiment


def test_experiment_to_dict_uses_plain_containers_and_iso_dates() -> None:
    record = make_experiment(parameters={"grid": [1, 2], "n": {"a": 1}}).to_dict()
    assert record["parameters"] == {"grid": [1, 2], "n": {"a": 1}}
    assert type(record["parameters"]) is dict
    assert type(record["parameters"]["grid"]) is list
    assert record["created_at"] == "2026-11-20T12:00:00+00:00"


def test_experiment_from_dict_rejects_bad_records() -> None:
    good = make_experiment().to_dict()
    with pytest.raises(TypeError, match="mapping"):
        Experiment.from_dict([1, 2])  # type: ignore[arg-type]
    with pytest.raises(InputValidationError, match=r"missing keys \['seed'\]"):
        Experiment.from_dict({k: v for k, v in good.items() if k != "seed"})
    with pytest.raises(InputValidationError, match=r"unknown keys \['extra'\]"):
        Experiment.from_dict({**good, "extra": 1})
    with pytest.raises(TypeError, match="created_at"):
        Experiment.from_dict({**good, "created_at": 20261120})
    with pytest.raises(InputValidationError, match="ISO-8601"):
        Experiment.from_dict({**good, "created_at": "yesterday"})
    with pytest.raises(InputValidationError, match="timezone-aware"):
        Experiment.from_dict({**good, "created_at": "2026-11-20T12:00:00"})
    with pytest.raises(InputValidationError, match="seed"):
        Experiment.from_dict({**good, "seed": -3})


# --- ExperimentRun ---------------------------------------------------------------------


def test_run_records_its_outcome() -> None:
    run = make_run()
    assert run.metrics == {"period": 4.0, "mean": 0.5}
    assert run.environment == {"python": "3.13.0"}
    assert run.started_at == FIXED_TIME
    assert run.execution_time_ms == 12.5


def test_run_mappings_are_copied_and_read_only() -> None:
    metrics = {"a": 1.0}
    environment = {"python": "3.13"}
    run = make_run(metrics=metrics, environment=environment)
    metrics["a"] = 2.0
    environment["python"] = "2.7"
    assert run.metrics == {"a": 1.0}
    assert run.environment == {"python": "3.13"}
    with pytest.raises(TypeError):
        run.metrics["a"] = 3.0  # type: ignore[index]
    with pytest.raises(dataclasses.FrozenInstanceError):
        run.execution_time_ms = 1.0  # type: ignore[misc]


def test_metrics_become_floats() -> None:
    run = make_run(metrics={"n": 4, "x": np.float32(0.5), "y": np.int64(2)})
    assert run.metrics == {"n": 4.0, "x": 0.5, "y": 2.0}
    assert all(type(value) is float for value in run.metrics.values())


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_metrics_must_be_finite(value: float) -> None:
    with pytest.raises(InputValidationError, match="metric 'm'"):
        make_run(metrics={"m": value})


@pytest.mark.parametrize("value", [True, "1.0", None, 1 + 1j])
def test_metrics_must_be_real_numbers(value: object) -> None:
    with pytest.raises(TypeError, match="metric 'm'"):
        make_run(metrics={"m": value})


@pytest.mark.parametrize("name", ["", 3])
def test_metric_names_must_be_non_empty_strings(name: object) -> None:
    with pytest.raises(InputValidationError, match="metric names"):
        make_run(metrics={name: 1.0})


def test_metrics_must_be_a_mapping() -> None:
    with pytest.raises(TypeError, match="metrics must be a mapping"):
        make_run(metrics=[1.0, 2.0])


def test_empty_metrics_are_allowed() -> None:
    assert make_run(metrics={}).metrics == {}


def test_run_requires_an_experiment() -> None:
    with pytest.raises(TypeError, match="Experiment"):
        make_run(experiment={"name": "x"})  # type: ignore[arg-type]
    # The helper replaces a falsy experiment by the default one, so build the run directly.
    with pytest.raises(TypeError, match="Experiment"):
        ExperimentRun(
            experiment=None,  # type: ignore[arg-type]
            metrics={},
            environment={},
            started_at=FIXED_TIME,
            execution_time_ms=0.0,
        )


@pytest.mark.parametrize("environment", [{"python": 3}, {1: "a"}, ["python"]])
def test_environment_must_map_strings_to_strings(environment: object) -> None:
    with pytest.raises(TypeError, match="environment"):
        make_run(environment=environment)


def test_run_time_fields_are_validated() -> None:
    with pytest.raises(InputValidationError, match="timezone-aware"):
        make_run(started_at=dt.datetime(2026, 11, 20, 12, 0))
    with pytest.raises(TypeError, match="started_at"):
        make_run(started_at="now")
    with pytest.raises(InputValidationError, match="must not be negative"):
        make_run(execution_time_ms=-0.1)
    with pytest.raises(InputValidationError, match="execution_time_ms"):
        make_run(execution_time_ms=float("nan"))
    assert make_run(execution_time_ms=0).execution_time_ms == 0.0


def test_run_round_trips_through_json() -> None:
    run = make_run(make_experiment(data_hash=HASH))
    text = json.dumps(run.to_dict())
    assert ExperimentRun.from_dict(json.loads(text)) == run


def test_run_from_dict_rejects_bad_records() -> None:
    good = make_run().to_dict()
    with pytest.raises(TypeError, match="mapping"):
        ExperimentRun.from_dict("text")  # type: ignore[arg-type]
    with pytest.raises(InputValidationError, match=r"missing keys \['metrics'\]"):
        ExperimentRun.from_dict({k: v for k, v in good.items() if k != "metrics"})
    with pytest.raises(InputValidationError, match="unknown keys"):
        ExperimentRun.from_dict({**good, "status": "ok"})
    with pytest.raises(TypeError, match="started_at"):
        ExperimentRun.from_dict({**good, "started_at": 5})
    with pytest.raises(InputValidationError, match="ISO-8601"):
        ExperimentRun.from_dict({**good, "started_at": "soon"})
    with pytest.raises(TypeError, match="experiment must be a mapping"):
        ExperimentRun.from_dict({**good, "experiment": "x"})
    with pytest.raises(InputValidationError, match="metric 'period'"):
        ExperimentRun.from_dict({**good, "metrics": {"period": float("nan")}})


# --- capture_environment ---------------------------------------------------------------


def test_capture_environment_names_what_the_numbers_depend_on() -> None:
    environment = capture_environment()
    assert set(environment) == {"python", "platform", "numpy", "scipy", "pandas", "quantlab"}
    assert environment["numpy"] == np.__version__
    assert environment["pandas"] == pd.__version__
    assert environment["quantlab"] == quantlab.__version__
    assert all(isinstance(value, str) and value for value in environment.values())


# --- run_experiment --------------------------------------------------------------------


def test_run_experiment_passes_parameters_and_seeds_and_records_the_outcome() -> None:
    received: dict[str, object] = {}

    def function(parameters: Mapping[str, JsonValue], seeds: SeedManager) -> dict[str, float]:
        received["parameters"] = parameters
        received["seed"] = seeds.seed
        return {"answer": 42}

    experiment = make_experiment()
    before = dt.datetime.now(dt.UTC)
    clock_before = time.perf_counter()
    run = run_experiment(experiment, function)
    clock_after = time.perf_counter()
    after = dt.datetime.now(dt.UTC)

    assert received == {"parameters": experiment.parameters, "seed": 7}
    assert run.experiment is experiment
    assert run.metrics == {"answer": 42.0}
    assert run.environment == capture_environment()
    assert before <= run.started_at <= after
    # The duration is measured with perf_counter, so it is bounded by the same clock. (The
    # wall clock is too coarse on some systems: its difference can be exactly zero.)
    assert 0.0 <= run.execution_time_ms <= (clock_after - clock_before) * 1000.0


def test_function_errors_propagate_unchanged() -> None:
    def failing(parameters: Mapping[str, JsonValue], seeds: SeedManager) -> dict[str, float]:
        raise ZeroDivisionError("boom")

    with pytest.raises(ZeroDivisionError, match="boom"):
        run_experiment(make_experiment(), failing)


def test_run_experiment_checks_its_arguments() -> None:
    with pytest.raises(TypeError, match="experiment must be an Experiment"):
        run_experiment({"name": "x"}, lambda p, s: {})  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="callable"):
        run_experiment(make_experiment(), "not a function")  # type: ignore[arg-type]


def test_run_experiment_validates_the_returned_metrics() -> None:
    with pytest.raises(InputValidationError, match="metric 'bad'"):
        run_experiment(make_experiment(), lambda p, s: {"bad": float("nan")})
    with pytest.raises(TypeError, match="metrics must be a mapping"):
        run_experiment(make_experiment(), lambda p, s: [1.0])  # type: ignore[arg-type, return-value]


# --- reproducibility -------------------------------------------------------------------


def noisy_mean(parameters: Mapping[str, JsonValue], seeds: SeedManager) -> dict[str, float]:
    """A stochastic computation that draws only from the seed manager."""
    n = parameters["n"]
    assert isinstance(n, int)
    sample = seeds.generator("noise").normal(loc=0.0, scale=1.0, size=n)
    return {"mean": float(sample.mean()), "std": float(sample.std(ddof=1))}


def test_rerunning_with_the_same_seed_reproduces_the_metrics_exactly() -> None:
    experiment = make_experiment(parameters={"n": 5_000})
    first = run_experiment(experiment, noisy_mean)
    second = run_experiment(first.experiment, noisy_mean)
    assert second.metric_differences(first) == {}
    assert second.reproduces(first)
    assert first.reproduces(second)


def test_a_different_seed_gives_different_metrics_and_cannot_be_compared() -> None:
    first = run_experiment(make_experiment(parameters={"n": 5_000}, seed=1), noisy_mean)
    second = run_experiment(make_experiment(parameters={"n": 5_000}, seed=2), noisy_mean)
    assert first.metrics != second.metrics
    with pytest.raises(InputValidationError, match="different model, parameters, seed"):
        first.reproduces(second)


def test_a_computation_that_ignores_the_seed_does_not_reproduce() -> None:
    def unseeded(parameters: Mapping[str, JsonValue], seeds: SeedManager) -> dict[str, float]:
        return {"draw": float(np.random.default_rng().random())}  # the mistake being detected

    experiment = make_experiment()
    first = run_experiment(experiment, unseeded)
    second = run_experiment(experiment, unseeded)
    assert not second.reproduces(first)
    assert set(second.metric_differences(first)) == {"draw"}


def test_differences_report_both_values_and_missing_metrics() -> None:
    experiment = make_experiment()
    first = make_run(experiment, metrics={"a": 1.0, "b": 2.0, "only_first": 5.0})
    second = make_run(experiment, metrics={"a": 1.0, "b": 2.5, "only_second": 6.0})
    assert first.metric_differences(second) == {
        "b": (2.0, 2.5),
        "only_first": (5.0, None),
        "only_second": (None, 6.0),
    }


def test_tolerances_accept_rounding_but_not_real_differences() -> None:
    experiment = make_experiment()
    first = make_run(experiment, metrics={"x": 1.0, "y": 1e-12})
    second = make_run(experiment, metrics={"x": 1.0 + 1e-13, "y": 3e-12})
    assert not first.reproduces(second)  # exact by default
    assert not first.reproduces(second, rtol=1e-9)  # y is off by a factor of three
    assert first.reproduces(second, rtol=1e-9, atol=1e-11)
    assert first.reproduces(second, atol=1e-11, rtol=1e-12)
    assert not first.reproduces(second, atol=1e-14)


def test_comparison_ignores_the_title_hypothesis_date_and_engine_version() -> None:
    """Reproducing a result with a newer engine is exactly what the comparison is for."""
    first = make_run(make_experiment(engine_version="0.1.0"))
    second = make_run(
        make_experiment(
            name="rerun",
            hypothesis="same setup, other words",
            engine_version="0.2.0",
            created_at=FIXED_TIME + dt.timedelta(days=90),
        )
    )
    assert first.reproduces(second)


@pytest.mark.parametrize(
    "other",
    [
        {"model": "lorenz"},
        {"parameters": {"r": 3.6, "n_steps": 2_000}},
        {"seed": 8},
        {"data_hash": HASH},
    ],
    ids=["model", "parameters", "seed", "data"],
)
def test_comparison_requires_the_same_setup(other: dict[str, object]) -> None:
    first = make_run(make_experiment())
    second = make_run(make_experiment(**other))
    with pytest.raises(InputValidationError, match="different model, parameters, seed"):
        first.metric_differences(second)


def test_comparison_validates_its_arguments() -> None:
    run = make_run()
    with pytest.raises(TypeError, match="ExperimentRun"):
        run.reproduces(run.experiment)  # type: ignore[arg-type]
    with pytest.raises(InputValidationError, match="must not be negative"):
        run.reproduces(run, rtol=-1e-9)
    with pytest.raises(InputValidationError, match="must not be negative"):
        run.reproduces(run, atol=-1.0)
    with pytest.raises(InputValidationError, match="rtol"):
        run.reproduces(run, rtol=float("nan"))
    with pytest.raises(TypeError, match="atol"):
        run.reproduces(run, atol="0")  # type: ignore[arg-type]


def test_changed_data_changes_the_setup() -> None:
    """The data fingerprint ties a result to the exact data it was computed from."""
    prices = pd.Series([10.0, 10.5, 10.2], index=pd.bdate_range("2025-01-02", periods=3))
    revised = prices.copy()
    revised.iloc[1] = 10.51  # the source revised a past price
    first = make_run(make_experiment(data_hash=hash_data(prices)))
    again = make_run(make_experiment(data_hash=hash_data(revised)))
    with pytest.raises(InputValidationError, match="data fingerprint"):
        first.reproduces(again)


# --- a real study, end to end ----------------------------------------------------------


def period_of_logistic_orbit(
    parameters: Mapping[str, JsonValue], seeds: SeedManager
) -> dict[str, float]:
    r = parameters["r"]
    n_steps = parameters["n_steps"]
    n_starts = parameters["n_starts"]
    assert isinstance(r, float)
    assert isinstance(n_steps, int)
    assert isinstance(n_starts, int)
    starts = seeds.generator("initial_conditions").uniform(0.05, 0.95, size=n_starts)
    periods = []
    for x0 in starts:
        orbit = simulate_logistic_map(r=r, x0=float(x0), n_steps=n_steps)[n_steps // 2 :]
        period = detect_period(orbit, atol=1e-6)
        periods.append(-1 if period is None else period)
    return {
        "fraction_with_period_4": float(np.mean(np.array(periods) == 4)),
        "max_period_found": float(max(periods)),
    }


def test_logistic_map_hypothesis_is_tested_and_reproduced() -> None:
    """At r = 3.5 the logistic map has an attracting 4-cycle (docs/math/mapa-logistico.md)."""
    experiment = make_experiment(parameters={"r": 3.5, "n_steps": 4_000, "n_starts": 25})
    run = run_experiment(experiment, period_of_logistic_orbit)
    assert run.metrics["fraction_with_period_4"] == 1.0
    assert run.metrics["max_period_found"] == 4.0

    stored = json.loads(json.dumps(run.to_dict()))  # what the layers above would persist
    restored = ExperimentRun.from_dict(stored)
    again = run_experiment(restored.experiment, period_of_logistic_orbit)
    assert again.reproduces(restored)

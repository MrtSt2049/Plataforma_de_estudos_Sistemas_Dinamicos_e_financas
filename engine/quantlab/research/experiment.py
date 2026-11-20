"""Registry of experiments and of their runs (RULE 017).

An :class:`Experiment` is the immutable *definition* of a study: the question asked (the
hypothesis), the model, its parameters, the random seed, a fingerprint of the input data
and the engine version. An :class:`ExperimentRun` is one *execution* of it: the metrics it
produced, when it ran, how long it took and the versions of the libraries involved.

The workflow that makes a result reproducible::

    experiment = Experiment(
        name="logistic map, period doubling",
        hypothesis="The orbit has period 4 at r = 3.5 for any initial condition.",
        model="logistic_map",
        parameters={"r": 3.5, "n_steps": 5_000},
        seed=7,
    )
    run = run_experiment(experiment, my_function)       # my_function(parameters, seeds)
    # ... months later, possibly on another machine:
    again = run_experiment(run.experiment, my_function)
    assert again.reproduces(run)

The module only *records and compares*. It does not store anything: persisting records is
the job of the layers above the engine, which receive them through ``to_dict`` as plain
JSON-compatible data.
"""

from __future__ import annotations

import datetime as dt
import math
import platform
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from numbers import Integral, Real
from types import MappingProxyType

import numpy as np
import pandas as pd
import scipy

from quantlab import __version__
from quantlab._validation import validate_finite_real, validate_int
from quantlab.exceptions import InputValidationError
from quantlab.research.seeds import MAX_SEED, SeedManager

type JsonValue = bool | int | float | str | Sequence[JsonValue] | Mapping[str, JsonValue] | None
"""A value that survives a round trip through JSON (the shape of experiment parameters)."""

_SHA256_HEX_LENGTH = 64
_HEX_DIGITS = frozenset("0123456789abcdef")
_EXPERIMENT_KEYS = frozenset(
    {
        "name",
        "hypothesis",
        "model",
        "parameters",
        "seed",
        "data_hash",
        "engine_version",
        "created_at",
    }
)
_RUN_KEYS = frozenset({"experiment", "metrics", "environment", "started_at", "execution_time_ms"})


def _freeze(value: object, *, path: str) -> JsonValue:
    """Return a deeply immutable copy of a JSON-compatible ``value``.

    Mappings become read-only mappings and sequences become tuples. NumPy scalars and
    arrays are converted to Python numbers and lists, because parameters often come from
    NumPy computations.
    """
    if value is None or isinstance(value, str):
        return value
    if isinstance(value, bool | np.bool_):
        return bool(value)
    if isinstance(value, Integral):
        return int(value)
    if isinstance(value, Real):
        as_float = float(value)
        if not math.isfinite(as_float):
            raise InputValidationError(f"{path} must be finite, got {as_float}.")
        return as_float
    if isinstance(value, np.ndarray):
        return _freeze(value.tolist(), path=path)
    if isinstance(value, Mapping):
        frozen: dict[str, JsonValue] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"{path} has a key {key!r} of type {type(key).__name__}; use str.")
            frozen[key] = _freeze(item, path=f"{path}.{key}")
        return MappingProxyType(frozen)
    if isinstance(value, list | tuple):
        return tuple(_freeze(item, path=f"{path}[{index}]") for index, item in enumerate(value))
    raise TypeError(
        f"{path} has the unsupported type {type(value).__name__}; "
        "use None, bool, int, float, str, lists or dicts."
    )


def _thaw(value: JsonValue) -> JsonValue:
    """Return plain ``dict``/``list`` containers, ready for :func:`json.dumps`."""
    if isinstance(value, str) or value is None or isinstance(value, bool | int | float):
        return value
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    return [_thaw(item) for item in value]


def _require_text(value: object, *, name: str) -> str:
    """Return ``value`` stripped of surrounding blanks, after checking it is not empty."""
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string, got {type(value).__name__}.")
    text = value.strip()
    if not text:
        raise InputValidationError(f"{name} must not be empty.")
    return text


def _require_utc(value: object, *, name: str) -> dt.datetime:
    """Return ``value`` converted to UTC, after checking it is a timezone-aware datetime."""
    if not isinstance(value, dt.datetime):
        raise TypeError(f"{name} must be a datetime, got {type(value).__name__}.")
    if value.tzinfo is None:
        raise InputValidationError(f"{name} must be timezone-aware (use UTC).")
    return value.astimezone(dt.UTC)


def _require_keys(record: object, *, expected: frozenset[str], name: str) -> Mapping[str, object]:
    """Check that ``record`` is a mapping with exactly the ``expected`` keys."""
    if not isinstance(record, Mapping):
        raise TypeError(f"{name} must be a mapping, got {type(record).__name__}.")
    missing = sorted(expected - record.keys())
    unknown = sorted(set(record.keys()) - expected)
    if missing or unknown:
        raise InputValidationError(f"{name} has missing keys {missing} and unknown keys {unknown}.")
    return record


def capture_environment() -> dict[str, str]:
    """Return the versions of what the numbers depend on: Python, platform and libraries.

    Floating-point results can differ in the last digits between library versions and
    between processors, so a run records where it happened.
    """
    return {
        "python": platform.python_version(),
        "platform": f"{platform.system()}-{platform.machine()}",
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "pandas": pd.__version__,
        "quantlab": __version__,
    }


@dataclass(frozen=True, slots=True, kw_only=True)
class Experiment:
    """The immutable definition of a study.

    Attributes
    ----------
    name
        Short title.
    hypothesis
        The question or claim being tested, in words. Required: a result without its
        hypothesis cannot be interpreted later.
    model
        Identifier of the model or method (for example ``"logistic_map"``).
    parameters
        Model parameters, as JSON-compatible values (``None``, ``bool``, ``int``,
        ``float``, ``str``, lists and dicts with ``str`` keys). The experiment keeps a
        deeply read-only copy; NumPy scalars and arrays are converted to Python values.
    seed
        Root random seed, in ``[0, MAX_SEED]``. Use :class:`SeedManager` to draw from it.
    data_hash
        Fingerprint of the input data (see :func:`quantlab.research.hash_data`), or ``None``
        when the study uses no external data.
    engine_version
        Version of the engine that defined the experiment. Defaults to the running one.
    created_at
        When the experiment was defined, timezone-aware (stored in UTC). Defaults to now.

    Raises
    ------
    TypeError
        If a field has the wrong type or a parameter is not JSON-compatible.
    InputValidationError
        If a text is empty, the seed is out of range, ``data_hash`` is not a SHA-256 hex
        digest, a number is not finite, or ``created_at`` is not timezone-aware.

    Notes
    -----
    Instances are not hashable (they hold mappings); compare them with ``==``.
    """

    name: str
    hypothesis: str
    model: str
    parameters: Mapping[str, JsonValue]
    seed: int
    data_hash: str | None = None
    engine_version: str = __version__
    created_at: dt.datetime = field(default_factory=lambda: dt.datetime.now(dt.UTC))

    def __post_init__(self) -> None:
        """Validate every field and freeze the parameters."""
        set_field = object.__setattr__  # the dataclass is frozen
        set_field(self, "name", _require_text(self.name, name="name"))
        set_field(self, "hypothesis", _require_text(self.hypothesis, name="hypothesis"))
        set_field(self, "model", _require_text(self.model, name="model"))
        set_field(self, "engine_version", _require_text(self.engine_version, name="engine_version"))
        set_field(self, "created_at", _require_utc(self.created_at, name="created_at"))

        seed = validate_int(self.seed, name="seed", minimum=0)
        if seed > MAX_SEED:
            raise InputValidationError(f"seed must be <= {MAX_SEED}, got {seed}.")
        set_field(self, "seed", seed)

        if self.data_hash is not None:
            if not isinstance(self.data_hash, str):
                raise TypeError(f"data_hash must be a string, got {type(self.data_hash).__name__}.")
            if len(self.data_hash) != _SHA256_HEX_LENGTH or not _HEX_DIGITS.issuperset(
                self.data_hash
            ):
                raise InputValidationError(
                    f"data_hash must be {_SHA256_HEX_LENGTH} lowercase hexadecimal characters "
                    "(use quantlab.research.hash_data)."
                )

        if not isinstance(self.parameters, Mapping):
            raise TypeError(f"parameters must be a mapping, got {type(self.parameters).__name__}.")
        frozen = _freeze(self.parameters, path="parameters")
        set_field(self, "parameters", frozen)

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a JSON-compatible dictionary (plain dicts, lists and ISO-8601 dates)."""
        return {
            "name": self.name,
            "hypothesis": self.hypothesis,
            "model": self.model,
            "parameters": _thaw(self.parameters),
            "seed": self.seed,
            "data_hash": self.data_hash,
            "engine_version": self.engine_version,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, record: Mapping[str, object]) -> Experiment:
        """Rebuild an experiment from :meth:`to_dict` output, validating it again.

        Raises
        ------
        TypeError
            If ``record`` is not a mapping or a field has the wrong type.
        InputValidationError
            If keys are missing or unknown, or a value is invalid.
        """
        fields = _require_keys(record, expected=_EXPERIMENT_KEYS, name="experiment record")
        created_at = fields["created_at"]
        if not isinstance(created_at, str):
            raise TypeError(
                f"created_at must be an ISO-8601 string, got {type(created_at).__name__}."
            )
        try:
            parsed = dt.datetime.fromisoformat(created_at)
        except ValueError as error:
            raise InputValidationError(f"created_at is not an ISO-8601 date: {error}") from error
        return cls(
            name=fields["name"],  # type: ignore[arg-type]
            hypothesis=fields["hypothesis"],  # type: ignore[arg-type]
            model=fields["model"],  # type: ignore[arg-type]
            parameters=fields["parameters"],  # type: ignore[arg-type]
            seed=fields["seed"],  # type: ignore[arg-type]
            data_hash=fields["data_hash"],  # type: ignore[arg-type]
            engine_version=fields["engine_version"],  # type: ignore[arg-type]
            created_at=parsed,
        )


def _freeze_metrics(metrics: object) -> Mapping[str, float]:
    """Check that ``metrics`` maps names to finite real numbers and return a read-only copy."""
    if not isinstance(metrics, Mapping):
        raise TypeError(f"metrics must be a mapping, got {type(metrics).__name__}.")
    checked: dict[str, float] = {}
    for key, value in metrics.items():
        if not isinstance(key, str) or not key:
            raise InputValidationError(f"metric names must be non-empty strings, got {key!r}.")
        checked[key] = validate_finite_real(value, name=f"metric {key!r}")
    return MappingProxyType(checked)


def _same_setup(first: Experiment, second: Experiment) -> bool:
    """Tell whether two experiments should give the same numbers.

    The title, the hypothesis, the date and the engine version are not part of the setup:
    reproducing a result with a newer engine is precisely what a comparison is for.
    """
    return (
        first.model == second.model
        and first.parameters == second.parameters
        and first.seed == second.seed
        and first.data_hash == second.data_hash
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class ExperimentRun:
    """One execution of an :class:`Experiment`.

    Attributes
    ----------
    experiment
        The experiment that was executed.
    metrics
        Consolidated results: names mapped to finite real numbers (read-only copy).
    environment
        Versions of Python, the platform and the libraries (see :func:`capture_environment`).
    started_at
        When the run started, timezone-aware (stored in UTC).
    execution_time_ms
        Wall-clock duration in milliseconds, finite and not negative.

    Raises
    ------
    TypeError
        If a field has the wrong type.
    InputValidationError
        If a metric name is empty, a metric or the duration is not finite, the duration is
        negative, or ``started_at`` is not timezone-aware.
    """

    experiment: Experiment
    metrics: Mapping[str, float]
    environment: Mapping[str, str]
    started_at: dt.datetime
    execution_time_ms: float

    def __post_init__(self) -> None:
        """Validate every field and freeze the mappings."""
        set_field = object.__setattr__  # the dataclass is frozen
        if not isinstance(self.experiment, Experiment):
            raise TypeError(
                f"experiment must be an Experiment, got {type(self.experiment).__name__}."
            )
        set_field(self, "metrics", _freeze_metrics(self.metrics))
        if not isinstance(self.environment, Mapping) or not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in self.environment.items()
        ):
            raise TypeError("environment must be a mapping from str to str.")
        set_field(self, "environment", MappingProxyType(dict(self.environment)))
        set_field(self, "started_at", _require_utc(self.started_at, name="started_at"))
        duration = validate_finite_real(self.execution_time_ms, name="execution_time_ms")
        if duration < 0:
            raise InputValidationError(f"execution_time_ms must not be negative, got {duration}.")
        set_field(self, "execution_time_ms", duration)

    def metric_differences(
        self, other: ExperimentRun, *, rtol: float = 0.0, atol: float = 0.0
    ) -> dict[str, tuple[float | None, float | None]]:
        """Return the metrics that differ between this run and ``other``.

        Two values agree when ``|a - b| <= max(rtol * max(|a|, |b|), atol)`` (the rule of
        :func:`math.isclose`). The default tolerances are zero: bit-for-bit equality, which
        is expected on the same machine and library versions. Across platforms or library
        versions, floating-point results can differ in the last digits, so pass a small
        explicit tolerance and record why.

        Parameters
        ----------
        other
            Another run of an experiment with the same setup.
        rtol, atol
            Relative and absolute tolerances, finite and not negative.

        Returns
        -------
        dict
            ``{metric: (value here, value there)}`` for every metric that differs or exists
            in only one run (the missing side is ``None``). Empty when the runs agree.

        Raises
        ------
        TypeError
            If ``other`` is not an :class:`ExperimentRun`.
        InputValidationError
            If a tolerance is negative or not finite, or if the two experiments do not
            have the same model, parameters, seed and data fingerprint: comparing their
            metrics would say nothing about reproducibility.
        """
        if not isinstance(other, ExperimentRun):
            raise TypeError(f"other must be an ExperimentRun, got {type(other).__name__}.")
        relative = validate_finite_real(rtol, name="rtol")
        absolute = validate_finite_real(atol, name="atol")
        if relative < 0 or absolute < 0:
            raise InputValidationError("rtol and atol must not be negative.")
        if not _same_setup(self.experiment, other.experiment):
            raise InputValidationError(
                "the runs belong to experiments with a different model, parameters, seed or "
                "data fingerprint, so their metrics are not expected to agree."
            )
        differences: dict[str, tuple[float | None, float | None]] = {}
        for name in sorted(self.metrics.keys() | other.metrics.keys()):
            here = self.metrics.get(name)
            there = other.metrics.get(name)
            if (
                here is None
                or there is None
                or not math.isclose(here, there, rel_tol=relative, abs_tol=absolute)
            ):
                differences[name] = (here, there)
        return differences

    def reproduces(self, other: ExperimentRun, *, rtol: float = 0.0, atol: float = 0.0) -> bool:
        """Tell whether this run gives the same metrics as ``other``.

        See :meth:`metric_differences` for the tolerance rule and the exceptions.
        """
        return not self.metric_differences(other, rtol=rtol, atol=atol)

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a JSON-compatible dictionary (plain dicts, lists and ISO-8601 dates)."""
        return {
            "experiment": self.experiment.to_dict(),
            "metrics": dict(self.metrics),
            "environment": dict(self.environment),
            "started_at": self.started_at.isoformat(),
            "execution_time_ms": self.execution_time_ms,
        }

    @classmethod
    def from_dict(cls, record: Mapping[str, object]) -> ExperimentRun:
        """Rebuild a run from :meth:`to_dict` output, validating it again.

        Raises
        ------
        TypeError
            If ``record`` is not a mapping or a field has the wrong type.
        InputValidationError
            If keys are missing or unknown, or a value is invalid.
        """
        fields = _require_keys(record, expected=_RUN_KEYS, name="run record")
        started_at = fields["started_at"]
        if not isinstance(started_at, str):
            raise TypeError(
                f"started_at must be an ISO-8601 string, got {type(started_at).__name__}."
            )
        try:
            parsed = dt.datetime.fromisoformat(started_at)
        except ValueError as error:
            raise InputValidationError(f"started_at is not an ISO-8601 date: {error}") from error
        experiment = fields["experiment"]
        if not isinstance(experiment, Mapping):
            raise TypeError(f"experiment must be a mapping, got {type(experiment).__name__}.")
        return cls(
            experiment=Experiment.from_dict(experiment),
            metrics=fields["metrics"],  # type: ignore[arg-type]
            environment=fields["environment"],  # type: ignore[arg-type]
            started_at=parsed,
            execution_time_ms=fields["execution_time_ms"],  # type: ignore[arg-type]
        )


type ExperimentFunction = Callable[[Mapping[str, JsonValue], SeedManager], Mapping[str, float]]
"""``function(parameters, seeds) -> metrics``: the computation an experiment runs."""


def run_experiment(experiment: Experiment, function: ExperimentFunction) -> ExperimentRun:
    """Execute ``function`` for ``experiment`` and record the outcome.

    The function receives the experiment's parameters and a :class:`SeedManager` built from
    its seed, and returns the metrics. Any randomness inside it must be drawn from that
    manager; otherwise the run is not reproducible. Data the function needs (a price
    series, say) is captured by closure, and its fingerprint belongs in
    ``experiment.data_hash``.

    Parameters
    ----------
    experiment
        What to run.
    function
        The computation, returning a mapping from metric names to finite real numbers.

    Returns
    -------
    ExperimentRun
        The metrics with the start time, duration and library versions.

    Raises
    ------
    TypeError
        If ``experiment`` is not an :class:`Experiment` or ``function`` is not callable, or
        the function returns something that is not a mapping of numbers.
    InputValidationError
        If a returned metric is not finite or has an empty name.

    Notes
    -----
    Errors raised by ``function`` propagate unchanged: a failed run is not recorded as a
    result, and a failure is never hidden.
    """
    if not isinstance(experiment, Experiment):
        raise TypeError(f"experiment must be an Experiment, got {type(experiment).__name__}.")
    if not callable(function):
        raise TypeError(f"function must be callable, got {type(function).__name__}.")
    seeds = SeedManager(experiment.seed)
    started_at = dt.datetime.now(dt.UTC)
    started = time.perf_counter()
    metrics = function(experiment.parameters, seeds)
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    return ExperimentRun(
        experiment=experiment,
        metrics=metrics,
        environment=capture_environment(),
        started_at=started_at,
        execution_time_ms=elapsed_ms,
    )

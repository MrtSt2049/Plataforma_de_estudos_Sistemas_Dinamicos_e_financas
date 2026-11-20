"""Research Core: reproducible, documented experiments (RULE 017).

* :class:`SeedManager` turns one recorded seed into independent, named random streams;
* :func:`hash_data` fingerprints the exact data an experiment used;
* :class:`Experiment` records the hypothesis, model, parameters, seed, data fingerprint and
  engine version; :func:`run_experiment` executes it and returns an :class:`ExperimentRun`
  with the metrics, which can later be checked with :meth:`ExperimentRun.reproduces`.

The module only records and compares; storing records is left to the layers above the
engine, which receive them as JSON-compatible dictionaries (``to_dict``).
"""

from quantlab.research.experiment import (
    Experiment,
    ExperimentFunction,
    ExperimentRun,
    JsonValue,
    capture_environment,
    run_experiment,
)
from quantlab.research.hashing import hash_data
from quantlab.research.seeds import DEFAULT_STREAM, MAX_SEED, SeedManager

__all__ = [
    "DEFAULT_STREAM",
    "MAX_SEED",
    "Experiment",
    "ExperimentFunction",
    "ExperimentRun",
    "JsonValue",
    "SeedManager",
    "capture_environment",
    "hash_data",
    "run_experiment",
]

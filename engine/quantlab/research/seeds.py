"""Explicit, reproducible control of random number generation (RULE 017).

An experiment that uses randomness must record its seed and draw every random number
from generators built from it, never from global state or from an unseeded
``numpy.random.default_rng()``. :class:`SeedManager` turns one *root seed* into as many
independent, named random streams as the experiment needs.

Mathematical basis
------------------
NumPy's :class:`numpy.random.SeedSequence` mixes an integer ``entropy`` and a
``spawn_key`` (a tuple of integers) into the initial state of a bit generator through a
hash-based construction designed so that different ``(entropy, spawn_key)`` pairs give
statistically independent streams, even when the entropy values are close to each other
(for example seeds 1, 2, 3). Here ``entropy`` is the root seed and the ``spawn_key`` is
derived from the stream's *name*, so:

* the same ``(seed, name)`` always gives the same sequence;
* different names give independent sequences;
* adding a new stream to an experiment does not change the numbers of the existing ones,
  which would not hold if streams were numbered by creation order.

The key is derived with SHA-256, not with Python's built-in :func:`hash`: ``hash(str)`` is
randomized per process (``PYTHONHASHSEED``), which would make results differ between
runs.
"""

from __future__ import annotations

import hashlib
import struct

import numpy as np

from quantlab._validation import validate_int
from quantlab.exceptions import InputValidationError

MAX_SEED = 2**53 - 1
"""Largest accepted seed: the largest integer that JavaScript represents exactly.

Seeds are stored in JSON and shown in the web interface; a larger integer would silently
lose precision in a browser and no longer reproduce the experiment.
"""

DEFAULT_STREAM = "default"
"""Name of the stream used when none is given."""

_KEY_WORDS = 4
_KEY_BYTES = 4 * _KEY_WORDS


def _stream_key(name: str) -> tuple[int, ...]:
    """Return a ``spawn_key`` derived deterministically from ``name``."""
    digest = hashlib.sha256(name.encode("utf-8")).digest()
    return struct.unpack(f">{_KEY_WORDS}I", digest[:_KEY_BYTES])


class SeedManager:
    """Build independent, named random generators from one root seed.

    Parameters
    ----------
    seed
        Root seed, an integer in ``[0, MAX_SEED]``. Record it with the experiment.

    Raises
    ------
    TypeError
        If ``seed`` is not an integer (booleans and floats are rejected).
    InputValidationError
        If ``seed`` is negative or larger than :data:`MAX_SEED`.

    Examples
    --------
    >>> seeds = SeedManager(42)
    >>> noise = seeds.generator("noise")
    >>> initial_states = seeds.generator("initial_states")
    """

    def __init__(self, seed: int) -> None:
        value = validate_int(seed, name="seed", minimum=0)
        if value > MAX_SEED:
            raise InputValidationError(f"seed must be <= {MAX_SEED}, got {value}.")
        self._seed = value

    @property
    def seed(self) -> int:
        """The root seed."""
        return self._seed

    def generator(self, stream: str = DEFAULT_STREAM) -> np.random.Generator:
        """Return a new generator for the stream called ``stream``.

        Every call returns a generator positioned at the *start* of the stream, so the
        result depends only on ``(seed, stream)`` and never on how many numbers were
        drawn before. Keep the returned object while drawing from it; asking again for
        the same name restarts the sequence.

        Parameters
        ----------
        stream
            Non-empty name of the stream, for example ``"noise"``.

        Returns
        -------
        numpy.random.Generator
            A PCG64 generator.

        Raises
        ------
        TypeError
            If ``stream`` is not a string.
        InputValidationError
            If ``stream`` is empty.
        """
        if not isinstance(stream, str):
            raise TypeError(f"stream must be a string, got {type(stream).__name__}.")
        if not stream:
            raise InputValidationError("stream must be a non-empty string.")
        sequence = np.random.SeedSequence(self._seed, spawn_key=_stream_key(stream))
        return np.random.default_rng(sequence)

    def __repr__(self) -> str:
        """Return ``SeedManager(seed=...)``."""
        return f"SeedManager(seed={self._seed})"

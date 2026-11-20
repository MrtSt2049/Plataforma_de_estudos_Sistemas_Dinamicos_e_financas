from __future__ import annotations

import numpy as np
import pytest

from quantlab.exceptions import InputValidationError
from quantlab.research import DEFAULT_STREAM, MAX_SEED, SeedManager
from quantlab.research.seeds import _stream_key


def test_exposes_the_seed_and_a_readable_repr() -> None:
    seeds = SeedManager(42)
    assert seeds.seed == 42
    assert repr(seeds) == "SeedManager(seed=42)"


def test_same_seed_and_stream_give_the_same_numbers() -> None:
    first = SeedManager(7).generator("noise").normal(size=1_000)
    second = SeedManager(7).generator("noise").normal(size=1_000)
    np.testing.assert_array_equal(first, second)


def test_each_call_restarts_the_stream() -> None:
    """The result depends only on (seed, stream), never on earlier draws."""
    seeds = SeedManager(7)
    first = seeds.generator("noise")
    first.normal(size=500)  # advance this one
    again = seeds.generator("noise")
    np.testing.assert_array_equal(
        again.normal(size=10), SeedManager(7).generator("noise").normal(size=10)
    )


def test_default_stream_is_named() -> None:
    seeds = SeedManager(7)
    np.testing.assert_array_equal(
        seeds.generator().random(5), seeds.generator(DEFAULT_STREAM).random(5)
    )


def test_different_streams_and_different_seeds_give_different_numbers() -> None:
    base = SeedManager(7).generator("a").random(100)
    assert not np.array_equal(base, SeedManager(7).generator("b").random(100))
    assert not np.array_equal(base, SeedManager(8).generator("a").random(100))


def test_adding_a_stream_does_not_change_the_others() -> None:
    """Streams are keyed by name, not numbered by creation order."""
    alone = SeedManager(7).generator("noise").random(20)
    seeds = SeedManager(7)
    seeds.generator("something else").random(1_000)
    seeds.generator("another").random(1_000)
    np.testing.assert_array_equal(seeds.generator("noise").random(20), alone)


def test_streams_are_statistically_independent() -> None:
    """Close seeds and different names must not produce correlated sequences."""
    n = 100_000
    bound = 4.0 / np.sqrt(n)  # four standard errors of a sample correlation under independence
    samples = [
        SeedManager(1).generator("x").normal(size=n),
        SeedManager(1).generator("y").normal(size=n),
        SeedManager(2).generator("x").normal(size=n),
        SeedManager(3).generator("x").normal(size=n),
    ]
    correlations = np.asarray(np.corrcoef(samples))
    off_diagonal = correlations[~np.eye(len(samples), dtype=bool)]
    assert np.abs(off_diagonal).max() < bound


def test_stream_keys_are_stable_across_processes() -> None:
    """Pinned values: the key comes from SHA-256, not from the per-process ``hash()``.

    If this fails, previously recorded experiments no longer reproduce.
    """
    assert _stream_key("default") == (933818049, 3457771645, 321905296, 1373414953)
    assert _stream_key("noise") == (4024608192, 2657962455, 3950206104, 1979151364)


@pytest.mark.parametrize(
    ("seed", "stream", "expected"),
    [
        (42, "default", [7841882697464930404, 10504048823073718694]),
        (42, "noise", [13396151358101290455, 2748551180678586657]),
        (43, "noise", [18143945598544252510, 1670067955793851220]),
    ],
)
def test_bit_generator_output_is_pinned(seed: int, stream: str, expected: list[int]) -> None:
    """Raw PCG64 output, which NumPy keeps stable, for recorded (seed, stream) pairs."""
    raw = SeedManager(seed).generator(stream).bit_generator.random_raw(2)
    assert [int(value) for value in raw] == expected


@pytest.mark.parametrize("seed", [0, 1, 2**32, MAX_SEED, np.int64(5), np.uint32(9)])
def test_accepts_valid_seeds(seed: int) -> None:
    assert SeedManager(seed).seed == int(seed)


@pytest.mark.parametrize("seed", [-1, MAX_SEED + 1, 2**63])
def test_rejects_out_of_range_seeds(seed: int) -> None:
    with pytest.raises(InputValidationError, match="seed"):
        SeedManager(seed)


@pytest.mark.parametrize("seed", [3.0, True, "7", None])
def test_rejects_non_integer_seeds(seed: object) -> None:
    with pytest.raises(TypeError, match="seed"):
        SeedManager(seed)  # type: ignore[arg-type]


def test_rejects_invalid_stream_names() -> None:
    seeds = SeedManager(1)
    with pytest.raises(InputValidationError, match="non-empty"):
        seeds.generator("")
    with pytest.raises(TypeError, match="stream"):
        seeds.generator(3)  # type: ignore[arg-type]

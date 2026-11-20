from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd
import pytest

from quantlab.exceptions import InputValidationError
from quantlab.research import hash_data


@pytest.fixture
def frame() -> pd.DataFrame:
    return pd.DataFrame(
        {"close": [10.0, 10.5, np.nan], "volume": [100.0, 200.0, 300.0]},
        index=pd.DatetimeIndex(["2025-01-02", "2025-01-03", "2025-01-06"], name="date"),
    )


def test_pinned_fingerprints(frame: pd.DataFrame) -> None:
    """Regression pins: if these change, recorded ``data_hash`` values stop matching."""
    assert hash_data(frame) == "5bb8096b40f384c768ab7572c367649ab409b84e0609e05989515c6e36ca30e1"
    series = pd.Series([1.0, 2.0, 3.0], index=[0, 1, 2], name="x")
    assert hash_data(series) == "157fbaba8bc9f91e67115ccc141f14d33bd004cb810fa12424eef69fb8340047"
    array = np.array([[1.0, 2.0], [3.0, 4.0]])
    assert hash_data(array) == "afcdc0d174d933ee2545771302df41004a33b31228703a366554cf6cb23071d1"


def test_is_a_sha256_hex_digest(frame: pd.DataFrame) -> None:
    digest = hash_data(frame)
    assert len(digest) == 64
    assert set(digest) <= set("0123456789abcdef")


def test_equal_content_gives_equal_hashes(frame: pd.DataFrame) -> None:
    assert hash_data(frame) == hash_data(frame.copy())
    rebuilt = pd.DataFrame(
        {"close": [10.0, 10.5, np.nan], "volume": [100.0, 200.0, 300.0]}, index=frame.index.copy()
    )
    assert hash_data(rebuilt) == hash_data(frame)


def dates_of(frame: pd.DataFrame) -> pd.DatetimeIndex:
    assert isinstance(frame.index, pd.DatetimeIndex)
    return frame.index


@pytest.mark.parametrize("unit", ["s", "ms", "us", "ns"])
def test_datetime_resolution_does_not_matter(
    frame: pd.DataFrame, unit: Literal["s", "ms", "us", "ns"]
) -> None:
    """pandas versions pick different datetime resolutions for the same dates."""
    other = frame.copy()
    other.index = dates_of(frame).as_unit(unit)
    assert hash_data(other) == hash_data(frame)


def test_timezone_aware_utc_equals_naive_utc(frame: pd.DataFrame) -> None:
    aware = frame.copy()
    aware.index = dates_of(frame).tz_localize("UTC")
    assert hash_data(aware) == hash_data(frame)
    shifted = frame.copy()
    shifted.index = dates_of(frame).tz_localize("Asia/Tokyo")  # same wall time, other instant
    assert hash_data(shifted) != hash_data(frame)


def test_integer_and_float_values_are_the_same_data() -> None:
    assert hash_data(pd.Series([1, 2, 3])) == hash_data(pd.Series([1.0, 2.0, 3.0]))
    assert hash_data(np.array([1, 2, 3])) == hash_data(np.array([1.0, 2.0, 3.0]))
    assert hash_data(np.array([1, 2], dtype=np.float32)) == hash_data(np.array([1.0, 2.0]))


def test_negative_zero_and_nan_payloads_do_not_matter() -> None:
    odd_nan = np.frombuffer(np.uint64(0x7FF8000000000001).tobytes(), dtype=np.float64)[0]
    assert np.isnan(odd_nan)
    assert hash_data(np.array([0.0, np.nan])) == hash_data(np.array([-0.0, odd_nan]))


def test_one_ulp_of_difference_changes_the_hash() -> None:
    value = 1.0
    assert hash_data(np.array([value])) != hash_data(np.array([np.nextafter(value, 2.0)]))


def test_any_change_of_content_changes_the_hash(frame: pd.DataFrame) -> None:
    reference = hash_data(frame)
    changed_value = frame.copy()
    changed_value.iloc[0, 0] = 10.01
    renamed_column = frame.rename(columns={"close": "adj_close"})
    renamed_index = frame.rename_axis("day")
    reordered_columns = frame[["volume", "close"]]
    reordered_rows = frame.iloc[::-1]
    shifted_dates = frame.copy()
    shifted_dates.index = frame.index + pd.Timedelta(days=1)
    missing_row = frame.iloc[:2]
    for other in (
        changed_value,
        renamed_column,
        renamed_index,
        reordered_columns,
        reordered_rows,
        shifted_dates,
        missing_row,
    ):
        assert hash_data(other) != reference


def test_series_name_and_array_shape_matter() -> None:
    assert hash_data(pd.Series([1.0, 2.0], name="a")) != hash_data(pd.Series([1.0, 2.0], name="b"))
    assert hash_data(pd.Series([1.0, 2.0])) != hash_data(pd.Series([1.0, 2.0], name="a"))
    flat = np.arange(6.0)
    assert len({hash_data(flat), hash_data(flat.reshape(2, 3)), hash_data(flat.reshape(3, 2))}) == 3


def test_a_frame_and_a_series_with_the_same_numbers_differ() -> None:
    series = pd.Series([1.0, 2.0], name="a")
    assert hash_data(series) != hash_data(series.to_frame())


def test_index_kinds() -> None:
    assert hash_data(pd.Series([1.0, 2.0], index=pd.RangeIndex(2))) == hash_data(
        pd.Series([1.0, 2.0], index=pd.Index([0, 1], dtype="int64"))
    )
    by_label = pd.Series([1.0, 2.0], index=["PETR4", "VALE3"])
    assert hash_data(by_label) != hash_data(pd.Series([1.0, 2.0], index=["PETR4", "ITUB4"]))
    assert hash_data(pd.Series([1.0, 2.0], index=["é", "ñ"])) != hash_data(by_label)


def test_empty_data_has_a_hash() -> None:
    assert len(hash_data(pd.Series(np.empty(0)))) == 64
    assert len(hash_data(np.empty((0, 3)))) == 64
    assert hash_data(np.empty((0, 3))) != hash_data(np.empty((3, 0)))


def test_nullable_integers_with_missing_values() -> None:
    nullable = pd.Series([1, None, 3], dtype="Int64")
    assert hash_data(nullable) == hash_data(pd.Series([1.0, np.nan, 3.0]))


def test_rejects_unsupported_types() -> None:
    with pytest.raises(TypeError, match="DataFrame"):
        hash_data([1.0, 2.0])  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "data",
    [
        pd.DataFrame({"a": [1.0], "b": ["x"]}),
        pd.DataFrame({"a": [True]}),
        pd.Series(["x", "y"]),
        pd.Series([True, False]),
        np.array(["a", "b"]),
        np.array([True, False]),
        np.array([1 + 2j]),
    ],
    ids=[
        "str-column",
        "bool-column",
        "str-series",
        "bool-series",
        "str-array",
        "bool-array",
        "complex",
    ],
)
def test_rejects_non_numeric_values(data: object) -> None:
    with pytest.raises(TypeError, match=r"numeric|real numbers"):
        hash_data(data)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "index",
    [
        pd.Index([0.5, 1.5]),
        pd.Index(["a", 1], dtype=object),
        pd.MultiIndex.from_tuples([("a", 1), ("b", 2)]),
    ],
    ids=["float", "mixed", "multi"],
)
def test_rejects_unsupported_indexes(index: pd.Index) -> None:
    with pytest.raises(TypeError, match="index"):
        hash_data(pd.Series([1.0, 2.0], index=index))


def test_rejects_duplicated_column_labels() -> None:
    duplicated = pd.DataFrame([[1.0, 2.0]], columns=["a", "a"])
    with pytest.raises(InputValidationError, match="duplicated"):
        hash_data(duplicated)

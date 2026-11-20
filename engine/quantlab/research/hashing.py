"""Stable fingerprints of the data an experiment used (RULE 017).

To reproduce a result months later it is not enough to know the symbol and the dates: the
source may have revised past prices. The SHA-256 fingerprint of the exact table that fed
the computation (``data_hash``) shows whether the data is still the same.

The fingerprint depends only on the *content*: index labels, column names and numeric
values. It does not depend on how the table was built, on pandas' internal datetime
resolution, on the platform's byte order, or on cosmetic differences such as ``-0.0``
versus ``0.0`` and the many bit patterns of NaN, so equal data gives equal hashes across
machines and library versions.
"""

from __future__ import annotations

import hashlib
import json

import numpy as np
import numpy.typing as npt
import pandas as pd

from quantlab.exceptions import InputValidationError

_FLOAT64_LITTLE_ENDIAN = "<f8"
_INT64_LITTLE_ENDIAN = "<i8"


def _canonical_floats(values: npt.ArrayLike) -> bytes:
    """Return the values as little-endian float64 bytes with a single NaN and no ``-0.0``."""
    as_float = np.asarray(values, dtype=np.float64)
    cleaned = np.where(np.isnan(as_float), np.nan, as_float) + 0.0  # `+ 0.0` turns -0.0 into 0.0
    return np.ascontiguousarray(cleaned, dtype=_FLOAT64_LITTLE_ENDIAN).tobytes()


type Hashable = pd.DataFrame | pd.Series[int] | pd.Series[float] | npt.NDArray[np.generic]
"""What :func:`hash_data` accepts (integer and float series alike)."""


def _numeric_values(data: Hashable) -> bytes:
    """Return the canonical bytes of the numeric values of ``data``."""
    if isinstance(data, pd.DataFrame):
        for column, dtype in data.dtypes.items():
            if pd.api.types.is_bool_dtype(dtype) or not pd.api.types.is_numeric_dtype(dtype):
                raise TypeError(f"column {column!r} must be numeric, got {dtype}.")
        return _canonical_floats(data.to_numpy(dtype=np.float64, na_value=np.nan))
    if isinstance(data, pd.Series):
        if pd.api.types.is_bool_dtype(data.dtype) or not pd.api.types.is_numeric_dtype(data.dtype):
            raise TypeError(f"series must be numeric, got {data.dtype}.")
        return _canonical_floats(data.to_numpy(dtype=np.float64, na_value=np.nan))
    if data.dtype.kind not in "iuf":
        raise TypeError(f"array must hold real numbers, got dtype {data.dtype}.")
    return _canonical_floats(data.astype(np.float64))


def _index_bytes(index: pd.Index) -> tuple[str, bytes]:
    """Return a tag naming the kind of index and its canonical bytes."""
    if isinstance(index, pd.DatetimeIndex):
        utc = index if index.tz is None else index.tz_convert("UTC").tz_localize(None)
        # Datetime resolution differs between pandas versions; nanoseconds is canonical.
        nanoseconds = np.asarray(utc.as_unit("ns").asi8, dtype=_INT64_LITTLE_ENDIAN)
        return "datetime-ns-utc", nanoseconds.tobytes()
    if pd.api.types.is_integer_dtype(index.dtype) and not pd.api.types.is_bool_dtype(index.dtype):
        return "int64", np.asarray(index.to_numpy(), dtype=_INT64_LITTLE_ENDIAN).tobytes()
    if pd.api.types.is_string_dtype(index.dtype) and all(isinstance(label, str) for label in index):
        return "str", json.dumps(list(index), ensure_ascii=True).encode("ascii")
    raise TypeError(
        f"index must hold dates, integers or strings, got {index.dtype}. "
        "Reindex the data before hashing it."
    )


def hash_data(data: Hashable) -> str:
    """Return the SHA-256 fingerprint of a table, a series or an array of numbers.

    Parameters
    ----------
    data
        A numeric :class:`pandas.DataFrame` or :class:`pandas.Series`, whose index is
        included in the fingerprint, or a numeric :class:`numpy.ndarray`, whose shape is.
        Missing values are allowed and hash the same regardless of their bit pattern.

    Returns
    -------
    str
        64 lowercase hexadecimal characters.

    Raises
    ------
    TypeError
        If ``data`` is of another type, has non-numeric (or boolean) values, or has an index
        that is not made of dates, integers or strings.
    InputValidationError
        If the table has two columns with the same label, which would make the content
        ambiguous.

    Notes
    -----
    Values are compared as float64, so ``1`` and ``1.0`` are the same data but two floats
    that differ in the last bit are different data. A table that went through a different
    cleaning policy hashes differently, which is how the fingerprint reveals it.
    """
    if not isinstance(data, pd.DataFrame | pd.Series | np.ndarray):
        raise TypeError(
            f"data must be a pandas DataFrame, a pandas Series or a numpy array, "
            f"got {type(data).__name__}."
        )
    header: dict[str, object]
    if isinstance(data, np.ndarray):
        header = {"kind": "array", "shape": list(data.shape)}
        index_tag, index = "none", b""
    else:
        index_tag, index = _index_bytes(data.index)
        header = {
            "index": index_tag,
            "index_name": None if data.index.name is None else str(data.index.name),
        }
        if isinstance(data, pd.DataFrame):
            if not data.columns.is_unique:
                raise InputValidationError("data has duplicated column labels.")
            header["kind"] = "frame"
            header["columns"] = [str(column) for column in data.columns]
        else:
            header["kind"] = "series"
            header["name"] = None if data.name is None else str(data.name)
    values = _numeric_values(data)

    digest = hashlib.sha256()
    for part in (
        json.dumps(header, sort_keys=True, ensure_ascii=True).encode("ascii"),
        index,
        values,
    ):
        digest.update(len(part).to_bytes(8, "big"))  # length prefix: parts cannot blur together
        digest.update(part)
    return digest.hexdigest()
